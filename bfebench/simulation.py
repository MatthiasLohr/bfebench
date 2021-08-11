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
from typing import Type

from .environments_configuration import EnvironmentsConfiguration
from .protocols import Protocol
from .simulation_result import SimulationResult
from .strategy import BuyerStrategy, SellerStrategy
from .strategy_process import StrategyProcess


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

    @property
    def environments(self) -> EnvironmentsConfiguration:
        return self._environments

    @property
    def protocol(self) -> Protocol:
        return self._protocol

    def run(self) -> SimulationResult:
        logger.debug('starting simulation')
        logger.debug('setting up protocol simulation...')
        self.protocol.set_up_simulation(self.environments.operator_environment)
        for iteration in range(self._iterations):
            logger.debug('setting up protocol iteration...')
            self.protocol.set_up_iteration(self.environments.operator_environment)

            logger.debug('setting up strategies...')
            seller_strategy = self._seller_strategy_type(self.environments.seller_environment)
            seller_process = StrategyProcess(seller_strategy)
            buyer_strategy = self._buyer_strategy_type(self.environments.buyer_environment)
            buyer_process = StrategyProcess(buyer_strategy)

            logger.debug('launching exchange protocol')
            seller_process.start()
            buyer_process.start()

            seller_process.join()
            buyer_process.join()

            logger.debug('tearing down protocol iteration')
            self.protocol.tear_down_iteration(self.environments.operator_environment)

        logger.debug('tearing down protocol simulation')
        self.protocol.tear_down_simulation(self.environments.operator_environment)
        logger.debug('simulation has finished')
        return SimulationResult()  # TODO add result data
