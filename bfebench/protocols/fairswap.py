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

from Crypto.Hash import keccak

from bfebench.strategy import BuyerStrategy, SellerStrategy
from .common import Protocol
from .fairswap_strategies import FaithfulBuyer, FaithfulSeller


B032 = b'\x00' * 32


class Fairswap(Protocol):
    name = 'Fairswap'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # TODO implement

    @staticmethod
    def get_seller_strategies() -> Dict[str, Type[SellerStrategy]]:
        return {
            'Faithful': FaithfulSeller
        }

    @staticmethod
    def get_buyer_strategies() -> Dict[str, Type[BuyerStrategy]]:
        return {
            'Faithful': FaithfulBuyer
        }

    @staticmethod
    def keccak(data: bytes) -> bytes:
        return keccak.new(data=data, digest_bytes=32).digest()
