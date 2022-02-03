# This file is part of the Blockchain-based Fair Exchange Benchmark Tool
#    https://gitlab.com/MatthiasLohr/bfebench
#
# Copyright 2021-2022 Matthias Lohr <mail@mlohr.com>
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
from typing import Any, List, NamedTuple

from .channel import Channel


class Adjudicator(object):
    class DisputePhase(IntEnum):
        DISPUTE = 0
        FORCEEXEC = 1
        CONCLUDED = 2

    class Dispute(NamedTuple):
        timeout: int
        challenge_duration: int
        version: int
        has_app: bool
        phase: "Adjudicator.DisputePhase"
        state_hash: bytes

        def __iter__(self) -> Any:
            yield self.timeout
            yield self.challenge_duration
            yield self.version
            yield self.has_app
            yield self.phase
            yield self.state_hash

    class SignedState(object):
        def __init__(self, params: Channel.Params, state: Channel.State, sigs: List[bytes]) -> None:
            self.params = params
            self.state = state
            self.sigs = sigs

        def __iter__(self) -> Any:
            yield tuple(self.params)
            yield tuple(self.state)
            yield self.sigs

        @staticmethod
        def from_tuple(*args: Any) -> "Adjudicator.SignedState":
            return Adjudicator.SignedState(
                Channel.Params.from_tuple(*args[0]), Channel.State.from_tuple(*args[1]), args[2]
            )
