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

from unittest import TestCase

from bfebench.protocols.state_channel_fairswap.protocol import (
    FileSalePhase,
    FileSaleState,
)
from bfebench.utils.bytes import generate_bytes


class TestStateChannelFairswap(TestCase):
    def test_file_sale_state(self) -> None:
        file_root_hash = generate_bytes(32)
        ciphertext_root_hash = generate_bytes(32)
        key_hash = generate_bytes(32)
        key = generate_bytes(32)
        phase = FileSalePhase.ACCEPTED

        state1 = FileSaleState(
            file_root_hash=file_root_hash,
            ciphertext_root_hash=ciphertext_root_hash,
            key_hash=key_hash,
            key=key,
            phase=phase,
        )

        state_bytes = bytes(state1)
        state2 = FileSaleState.from_bytes(state_bytes)

        self.assertEqual(state1, state2)
