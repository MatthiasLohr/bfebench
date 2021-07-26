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

from typing import Dict, Type

from bfebench.component import Component
from bfebench.environments import Environment
from bfebench.strategy import BuyerStrategy, SellerStrategy


class Protocol(Component):
    @staticmethod
    def get_seller_strategies() -> Dict[str, Type[SellerStrategy]]:
        raise NotImplementedError()

    @staticmethod
    def get_buyer_strategies() -> Dict[str, Type[BuyerStrategy]]:
        raise NotImplementedError()

    def set_up_simulation(self, environment: Environment) -> None:
        pass

    def set_up_iteration(self, environment: Environment) -> None:
        pass

    def tear_down_iteration(self, environment: Environment) -> None:
        pass

    def tear_down_simulation(self, environment: Environment) -> None:
        pass
