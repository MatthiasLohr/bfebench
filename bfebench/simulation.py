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

from .data_providers import DataProvider
from .environments import Environment
from .party import PartySimulationProcess
from .protocols import Protocol
from .simulation_result import SimulationResult


class Simulation(object):
    def __init__(self, environment: Environment, protocol: Protocol, data_provider: DataProvider, iterations: int):
        self._environment = environment
        self._protocol = protocol
        self._data_provider = data_provider
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
        self.environment.set_up()
        self.protocol.set_up_simulation(self.environment)
        for iteration in range(self._iterations):
            self.protocol.set_up_iteration(self.environment)

            seller_process = PartySimulationProcess(self.environment)
            buyer_process = PartySimulationProcess(self.environment)

            seller_process.start()
            buyer_process.start()

            seller_process.join()
            buyer_process.join()

            self.protocol.tear_down_iteration(self.environment)
        self.protocol.tear_down_simulation(self.environment)
        self.environment.tear_down()
        return SimulationResult()  # TODO add result data
