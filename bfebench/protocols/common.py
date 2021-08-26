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

from typing import Any, Dict, Type

from bfebench.environment import Environment
from bfebench.errors import BaseError
from bfebench.strategy import SellerStrategy, BuyerStrategy


class Protocol(object):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if len(args) > 0:
            raise BaseError('too many positional arguments for initializing %s' % self.__class__.__name__)
        if len(kwargs) > 0:
            raise BaseError('unrecognized keyword arguments for initializing %s: %s' % (
                self.__class__.__name__,
                ', '.join(kwargs.keys())
            ))

    @staticmethod
    def get_seller_strategies() -> Dict[str, Type[SellerStrategy]]:
        raise NotImplementedError()

    def get_seller_strategy_kwargs(self) -> Dict[str, Any]:
        return {}

    def get_buyer_strategy_kwargs(self) -> Dict[str, Any]:
        return {}

    @staticmethod
    def get_buyer_strategies() -> Dict[str, Type[BuyerStrategy]]:
        raise NotImplementedError()

    def set_up_simulation(self, operator_environment: Environment, seller_environment: Environment,
                          buyer_environment: Environment) -> None:
        pass

    def set_up_iteration(self, operator_environment: Environment, seller_environment: Environment,
                         buyer_environment: Environment) -> None:
        pass

    def tear_down_iteration(self, operator_environment: Environment, seller_environment: Environment,
                            buyer_environment: Environment) -> None:
        pass

    def tear_down_simulation(self, operator_environment: Environment, seller_environment: Environment,
                             buyer_environment: Environment) -> None:
        pass
