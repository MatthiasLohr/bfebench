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

from unittest import TestCase

from bfebench.protocols.state_channel_file_sale.file_sale import FileSale


class FileSaleAppStateTest(TestCase):
    def test_abi_encode_decode(self) -> None:
        app_state = FileSale.AppState()
        app_state_encoded = app_state.encode_abi()
        app_state_decoded = FileSale.AppState.decode_abi(app_state_encoded)
        self.assertEqual(app_state, app_state_decoded)
