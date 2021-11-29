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

from __future__ import annotations

from typing import Any, Generator, List, NamedTuple

from eth_abi.abi import encode_abi
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing.evm import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3


class ChannelParams(NamedTuple):
    challenge_duration: int
    nonce: int
    participants: List[ChecksumAddress]
    app: ChecksumAddress
    ledger_channel: bool
    virtual_channel: bool

    def abi_encode(self) -> bytes:
        return encode_abi(
            ["(uint256,uint256,address[],address,bool,bool)"], [tuple(self)]
        )

    def get_keccak(self) -> bytes:
        return bytes(Web3.solidityKeccak(["bytes"], [self.abi_encode()]))

    def get_channel_id(self) -> bytes:
        return self.get_keccak()


class SubAllocation(NamedTuple):
    id: bytes
    balances: List[int] = []
    index_map: List[int] = []


class Allocation(NamedTuple):
    assets: List[ChecksumAddress] = []
    balances: List[List[int]] = [[]]
    locked: List[SubAllocation] = []

    def __iter__(self) -> Generator[Any, None, None]:
        yield self.assets
        yield self.balances
        yield [tuple(sub_alloc) for sub_alloc in self.locked]


class ChannelState(NamedTuple):
    channel_id: bytes
    version: int
    outcome: Allocation
    app_data: bytes
    is_final: bool

    def abi_encode(self) -> bytes:
        return encode_abi(
            [
                "(bytes32,uint64,(address[],uint256[][],(bytes32,uint256[],uint16[])[]),bytes,bool)"
            ],
            [tuple(self)],
        )

    def get_keccak(self) -> bytes:
        return bytes(Web3.solidityKeccak(["bytes"], [self.abi_encode()]))

    def sign(self, private_key: HexBytes | bytes) -> bytes:
        signed_message = Account.sign_message(
            encode_defunct(self.get_keccak()), bytes(private_key)
        )
        return bytes(signed_message.signature)

    def __iter__(self) -> Generator[Any, None, None]:
        yield self.channel_id
        yield self.version
        yield tuple(self.outcome)
        yield self.app_data
        yield self.is_final
