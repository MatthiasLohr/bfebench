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

from .affiliate import AffiliateProcess
from .data_providers import DataProvider
from .environments import Environment
from .protocols import Protocol
from .simulation_result import SimulationResult
from .strategy import BuyerStrategy, SellerStrategy


logger = logging.getLogger(__name__)


class Simulation(object):
    def __init__(self, environment: Environment, protocol: Protocol, data_provider: DataProvider,
                 seller_strategy: Type[SellerStrategy], buyer_strategy: Type[BuyerStrategy], iterations: int) -> None:
        self._environment = environment
        self._protocol = protocol
        self._data_provider = data_provider
        self._seller_strategy = seller_strategy
        self._buyer_strategy = buyer_strategy
        self._iterations = iterations

    @property
    def environment(self) -> Environment:
        return self._environment

    @property
    def protocol(self) -> Protocol:
        return self._protocol

    @property
    def data_provider(self) -> DataProvider:
        return self._data_provider

    def run(self) -> SimulationResult:
        logger.debug('starting simulation')
        logger.debug('setting up environment...')
        self.environment.set_up()
        logger.debug('setting up protocol simulation...')
        self.protocol.set_up_simulation(self.environment)
        for iteration in range(self._iterations):
            logger.debug('setting up protocol iteration...')
            self.protocol.set_up_iteration(self.environment)

            logger.debug('setting up affiliates...')

            seller_strategy_instance = self._seller_strategy()
            buyer_strategy_instance = self._buyer_strategy()

            seller_process = AffiliateProcess(self.environment, seller_strategy_instance, None)
            buyer_process = AffiliateProcess(self.environment, buyer_strategy_instance, None)

            logger.debug('starting exchange...')

            seller_process.start()
            buyer_process.start()

            seller_process.join()
            buyer_process.join()

            logger.debug('tearing down protocol iteration')
            self.protocol.tear_down_iteration(self.environment)

        logger.debug('tearing down protocol simulation')
        self.protocol.tear_down_simulation(self.environment)
        logger.debug('tearing down environment...')
        self.environment.tear_down()
        logger.debug('simulation has finished')
        return SimulationResult()  # TODO add result data
