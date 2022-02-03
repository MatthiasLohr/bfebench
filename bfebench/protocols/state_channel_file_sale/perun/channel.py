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

from typing import Any, List, NamedTuple

from eth_typing.evm import ChecksumAddress
from web3 import Web3


class Channel(object):
    class Params(NamedTuple):
        challenge_duration: int
        nonce: int
        participants: List[ChecksumAddress]
        app: ChecksumAddress
        ledger_channel: bool
        virtual_channel: bool

        def __iter__(self) -> Any:
            yield self.challenge_duration
            yield self.nonce
            yield self.participants
            yield self.app
            yield self.ledger_channel
            yield self.virtual_channel

        @staticmethod
        def from_tuple(*args: Any) -> "Channel.Params":
            return Channel.Params(
                args[0],
                args[1],
                [Web3.toChecksumAddress(address) for address in args[2]],
                Web3.toChecksumAddress(args[3]),
                args[4],
                args[5],
            )

    class SubAlloc(NamedTuple):
        id: bytes
        balances: List[int] = []
        index_map: List[int] = []

        def __iter__(self) -> Any:
            yield self.id
            yield self.balances
            yield self.index_map

        @staticmethod
        def from_tuple(*args: Any) -> "Channel.SubAlloc":
            return Channel.SubAlloc(*args)

    class Allocation(object):
        def __init__(
            self, assets: List[ChecksumAddress], balances: List[List[int]], locked: List["Channel.SubAlloc"]
        ) -> None:
            self.assets = assets
            self.balances = balances
            self.locked = locked

        def __iter__(self) -> Any:
            yield self.assets
            yield self.balances
            yield [tuple(entry) for entry in self.locked]

        @staticmethod
        def from_tuple(*args: Any) -> "Channel.Allocation":
            return Channel.Allocation(
                [Web3.toChecksumAddress(address) for address in args[0]],
                args[1],
                [Channel.SubAlloc.from_tuple(sub_alloc) for sub_alloc in args[2]],
            )

    class State(object):
        def __init__(
            self,
            channel_id: bytes,
            version: int,
            outcome: "Channel.Allocation",
            app_data: bytes,
            is_final: bool = False,
        ) -> None:
            self.channel_id = channel_id
            self.version = version
            self.outcome = outcome
            self.app_data = app_data
            self.is_final = is_final

        def __iter__(self) -> Any:
            yield self.channel_id
            yield self.version
            yield tuple(self.outcome)
            yield self.app_data
            yield self.is_final

        @staticmethod
        def from_tuple(*args: Any) -> "Channel.State":
            return Channel.State(args[0], args[1], Channel.Allocation.from_tuple(*args[2]), args[3], args[4])
