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

    class SubAlloc(NamedTuple):
        id: bytes
        balances: List[int] = []
        index_map: List[int] = []

        def __iter__(self) -> Any:
            yield self.id
            yield self.balances
            yield self.index_map

    class Allocation(NamedTuple):
        assets: List[ChecksumAddress] = []
        balances: List[List[int]] = [[]]
        locked: List["Channel.SubAlloc"] = []

        def __iter__(self) -> Any:
            yield self.assets
            yield self.balances
            yield [tuple(entry) for entry in self.locked]

    class State(object):
        def __init__(self, channel_id: bytes, outcome: "Channel.Allocation", app_data: bytes) -> None:
            self.channel_id = channel_id
            self.version = 1
            self.outcome = outcome
            self.app_data = app_data
            self.is_final = False

        def __iter__(self) -> Any:
            yield self.channel_id
            yield self.version
            yield tuple(self.outcome)
            yield self.app_data
            yield self.is_final
