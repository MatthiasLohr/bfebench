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

from typing import Any

from .environment import Environment
from .utils.json_stream import JsonObjectSocketStream


class Strategy(object):
    def __init__(self) -> None:
        pass

    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream, filename: str, price: int,
            **kwargs: Any) -> None:
        raise NotImplementedError()


class SellerStrategy(Strategy):
    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream, filename: str, price: int,
            **kwargs: Any) -> None:
        raise NotImplementedError()


class BuyerStrategy(Strategy):
    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream, filename: str, price: int,
            **kwargs: Any) -> None:
        raise NotImplementedError()
