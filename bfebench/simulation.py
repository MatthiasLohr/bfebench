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

from .environments_configuration import EnvironmentsConfiguration
from .protocols import Protocol, SellerStrategy, BuyerStrategy
from .simulation_result import IterationResult, SimulationResult
from .strategy_process import StrategyProcess
from .utils.json_stream import (
    JsonObjectUnixDomainSocketClientStream,
    JsonObjectUnixDomainSocketServerStream,
    JsonObjectSocketStreamForwarder
)


logger = logging.getLogger(__name__)


class Simulation(object):
    def __init__(self, environments_configuration: EnvironmentsConfiguration, protocol: Protocol,
                 seller_strategy: SellerStrategy[Protocol], buyer_strategy: BuyerStrategy[Protocol],
                 iterations: int = 1) -> None:
        self._environments = environments_configuration
        self._protocol = protocol
        self._seller_strategy = seller_strategy
        self._buyer_strategy = buyer_strategy
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
        simulation_result = SimulationResult()
        self.protocol.set_up_simulation(
            seller_address=self.environments.seller_environment.wallet_address,
            buyer_address=self.environments.buyer_environment.wallet_address
        )
        for iteration in range(self._iterations):
            logger.debug('setting up protocol iteration...')
            self.protocol.set_up_iteration(
                seller_address=self.environments.seller_environment.wallet_address,
                buyer_address=self.environments.buyer_environment.wallet_address
            )

            logger.debug('setting up strategies...')
            seller_socket = 'seller-%d.ipc' % iteration
            buyer_socket = 'buyer-%d.ipc' % iteration
            seller_p2p_server = JsonObjectUnixDomainSocketServerStream(os.path.join(self._tmp_dir, seller_socket))
            buyer_p2p_server = JsonObjectUnixDomainSocketServerStream(os.path.join(self._tmp_dir, buyer_socket))

            p2p_forwarder = JsonObjectSocketStreamForwarder(seller_p2p_server, buyer_p2p_server)
            p2p_forwarder.start()

            seller_p2p_client = JsonObjectUnixDomainSocketClientStream(os.path.join(self._tmp_dir, seller_socket))
            buyer_p2p_client = JsonObjectUnixDomainSocketClientStream(os.path.join(self._tmp_dir, buyer_socket))

            seller_process = StrategyProcess(
                strategy=self._seller_strategy,
                environment=self.environments.seller_environment,
                p2p_stream=seller_p2p_client
            )
            buyer_process = StrategyProcess(
                strategy=self._buyer_strategy,
                environment=self.environments.buyer_environment,
                p2p_stream=buyer_p2p_client
            )

            logger.debug('launching exchange protocol')
            seller_process.start()
            buyer_process.start()

            seller_process.join()
            buyer_process.join()

            logger.debug('tearing down protocol iteration')
            self.protocol.tear_down_iteration(
                seller_address=self.environments.seller_environment.wallet_address,
                buyer_address=self.environments.buyer_environment.wallet_address
            )

            simulation_result.add_iteration_result(IterationResult(
                seller_resource_usage=seller_process.get_resource_usage(),
                buyer_resource_usage=buyer_process.get_resource_usage(),
                seller2buyer_direct_bytes=p2p_forwarder.bytes_1to2,
                buyer2seller_direct_bytes=p2p_forwarder.bytes_2to1,
                seller2buyer_direct_objects=p2p_forwarder.objects_1to2,
                buyer2seller_direct_objects=p2p_forwarder.objects_2to1
            ))

            seller_p2p_client.close()
            buyer_p2p_client.close()
            del seller_p2p_client
            del buyer_p2p_client

            del seller_process
            del buyer_process

            seller_p2p_server.close()
            buyer_p2p_server.close()

            del seller_p2p_server
            del buyer_p2p_server

        logger.debug('tearing down protocol simulation')
        self.protocol.tear_down_simulation(
            seller_address=self.environments.seller_environment.wallet_address,
            buyer_address=self.environments.buyer_environment.wallet_address
        )
        rmtree(self._tmp_dir)
        logger.debug('simulation has finished')
        return simulation_result

    def __del__(self) -> None:
        rmtree(self._tmp_dir, ignore_errors=True)
