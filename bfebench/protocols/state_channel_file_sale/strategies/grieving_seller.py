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

from eth_typing.evm import ChecksumAddress

from ....environment import Environment
from ....utils.json_stream import JsonObjectSocketStream
from .seller import StateChannelFileSaleSeller


class GrievingSeller(StateChannelFileSaleSeller):
    def run(
        self, environment: Environment, p2p_stream: JsonObjectSocketStream, opposite_address: ChecksumAddress
    ) -> None:
        self.open_state_channel(environment, p2p_stream)
        self.logger.debug("state channel opened, expecting buyer to fund, so quitting")
        return
