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

from ....utils.bytes import generate_bytes
from .seller import StateChannelFileSaleSeller


class KeyForgingSeller(StateChannelFileSaleSeller):
    def get_key_to_be_sent(self, original_key: bytes, iteration: int) -> bytes:
        if self.protocol.is_last_iteration(iteration):
            return generate_bytes(32, avoid=original_key)
        else:
            return super().get_key_to_be_sent(original_key, iteration)
