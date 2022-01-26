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

from enum import IntEnum
from typing import Any

from eth_abi.abi import decode_single, encode_abi

from ..fairswap.util import B032


class FileSalePhase(IntEnum):
    CONFIRMED_IDLE = 0
    ACCEPTED = 1
    KEY_REVEALED = 2
    COMPLAINT_SUCCESSFUL = 3


class FileSale(object):
    class AppState(object):
        TYPES = "(bytes32,bytes32,bytes32,bytes32,uint,uint)"

        def __init__(
            self,
            file_root: bytes = B032,
            ciphertext_root: bytes = B032,
            key_commit: bytes = B032,
            key: bytes = B032,
            price: int = 0,
            phase: FileSalePhase = FileSalePhase.CONFIRMED_IDLE,
        ) -> None:
            self.file_root = file_root
            self.ciphertext_root = ciphertext_root
            self.key_commit = key_commit
            self.key = key
            self.price = price
            self.phase = FileSalePhase(phase)

        def __iter__(self) -> Any:
            yield self.file_root
            yield self.ciphertext_root
            yield self.key_commit
            yield self.key
            yield self.price
            yield self.phase.value

        def encode_abi(self) -> bytes:
            return encode_abi([self.TYPES], [tuple(self)])

        @classmethod
        def decode_abi(cls, data: bytes) -> "FileSale.AppState":
            return FileSale.AppState(*decode_single(cls.TYPES, data))

        def __eq__(self, other: Any) -> bool:
            if not isinstance(other, self.__class__):
                return False
            return tuple(self) == tuple(other)
