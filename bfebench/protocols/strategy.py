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

from typing import Generic, TypeVar

from eth_typing.evm import ChecksumAddress

from .protocol import Protocol
from ..utils.json_stream import JsonObjectSocketStream


T = TypeVar('T', bound=Protocol)


class Strategy(Generic[T]):
    def __init__(self, protocol: T) -> None:
        self._protocol = protocol

    @property
    def protocol(self) -> T:
        return self._protocol

    def run(self, p2p_stream: JsonObjectSocketStream, opposite_address: ChecksumAddress) -> None:
        raise NotImplementedError()


class SellerStrategy(Strategy[T]):
    def run(self, p2p_stream: JsonObjectSocketStream, opposite_address: ChecksumAddress) -> None:
        raise NotImplementedError()


class BuyerStrategy(Strategy[T]):
    def run(self, p2p_stream: JsonObjectSocketStream, opposite_address: ChecksumAddress) -> None:
        raise NotImplementedError()
