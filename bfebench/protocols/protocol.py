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

from eth_typing.evm import ChecksumAddress

from ..environment import Environment
from ..errors import BaseError


class Protocol(object):
    def __init__(self, filename: str, price: int, **kwargs: Any) -> None:
        if len(kwargs) > 0:
            raise BaseError(
                "unhandled protocol keyword parameters: %s" % ", ".join(kwargs.keys())
            )

        self._filename = filename
        self._price = price

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def price(self) -> int:
        return self._price

    def set_up_simulation(
        self,
        environment: Environment,
        seller_address: ChecksumAddress,
        buyer_address: ChecksumAddress,
    ) -> None:
        pass

    def set_up_iteration(
        self,
        environment: Environment,
        seller_address: ChecksumAddress,
        buyer_address: ChecksumAddress,
    ) -> None:
        pass

    def tear_down_iteration(
        self,
        environment: Environment,
        seller_address: ChecksumAddress,
        buyer_address: ChecksumAddress,
    ) -> None:
        pass

    def tear_down_simulation(
        self,
        environment: Environment,
        seller_address: ChecksumAddress,
        buyer_address: ChecksumAddress,
    ) -> None:
        pass
