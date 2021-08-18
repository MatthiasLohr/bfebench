# This file is part of the Blockchain-based Fair Exchange Benchmark Tool
#    https://gitlab.com/MatthiasLohr/bfebench
#
# Copyright 2021 Matthias Lohr <mail@mlohr.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from shutil import rmtree
from tempfile import mkdtemp
from typing import Type

from .environments_configuration import EnvironmentsConfiguration
from .protocols import Protocol
from .simulation_result import SimulationResult
from .strategy import BuyerStrategy, SellerStrategy
from .strategy_process import StrategyProcess
from .utils.json_stream import (
    JsonObjectUnixDomainSocketClientStream,
    JsonObjectUnixDomainSocketServerStream,
    JsonObjectSocketStreamForwarder
)


logger = logging.getLogger(__name__)


class Simulation(object):
    def __init__(self, environments_configuration: EnvironmentsConfiguration, protocol: Protocol,
                 seller_strategy: Type[SellerStrategy], buyer_strategy: Type[BuyerStrategy],
                 iterations: int = 1) -> None:
        self._environments = environments_configuration
        self._protocol = protocol
        self._seller_strategy_type = seller_strategy
        self._buyer_strategy_type = buyer_strategy
        self._iterations = iterations

        self._tmp_dir = mkdtemp(prefix='bfebench-')

    @property
    def environments(self) -> EnvironmentsConfiguration:
        return self._environments

    @property
    def protocol(self) -> Protocol:
        return self._protocol

    def run(self) -> SimulationResult:
        logger.debug('starting simulation')
        logger.debug('setting up protocol simulation...')
        self.protocol.set_up_simulation(
            self.environments.operator_environment,
            self.environments.seller_environment,
            self.environments.buyer_environment
        )
        for iteration in range(self._iterations):
            logger.debug('setting up protocol iteration...')
            self.protocol.set_up_iteration(
                self.environments.operator_environment,
                self.environments.seller_environment,
                self.environments.buyer_environment
            )

            logger.debug('setting up strategies...')
            seller_p2p_stream = JsonObjectUnixDomainSocketServerStream(os.path.join(self._tmp_dir, 'seller.ipc'))
            buyer_p2p_stream = JsonObjectUnixDomainSocketServerStream(os.path.join(self._tmp_dir, 'buyer.ipc'))

            p2p_forwarder = JsonObjectSocketStreamForwarder(seller_p2p_stream, buyer_p2p_stream)
            p2p_forwarder.start()

            seller_process = StrategyProcess(
                strategy=self._seller_strategy_type(),
                environment=self.environments.seller_environment,
                p2p_stream=JsonObjectUnixDomainSocketClientStream(os.path.join(self._tmp_dir, 'seller.ipc'))
            )
            buyer_process = StrategyProcess(
                strategy=self._buyer_strategy_type(),
                environment=self.environments.buyer_environment,
                p2p_stream=JsonObjectUnixDomainSocketClientStream(os.path.join(self._tmp_dir, 'buyer.ipc'))
            )

            logger.debug('launching exchange protocol')
            seller_process.start()
            buyer_process.start()

            seller_process.join()
            buyer_process.join()

            logger.debug('tearing down protocol iteration')
            self.protocol.tear_down_iteration(
                self.environments.operator_environment,
                self.environments.seller_environment,
                self.environments.buyer_environment
            )

        logger.debug('tearing down protocol simulation')
        self.protocol.tear_down_simulation(
            self.environments.operator_environment,
            self.environments.seller_environment,
            self.environments.buyer_environment
        )
        logger.debug('simulation has finished')
        rmtree(self._tmp_dir)
        return SimulationResult()  # TODO add result data

    def __del__(self) -> None:
        rmtree(self._tmp_dir, ignore_errors=True)
