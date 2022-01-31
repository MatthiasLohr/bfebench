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

from eth_typing.encoding import HexStr
from eth_typing.evm import ChecksumAddress, HexAddress
from hexbytes.main import HexBytes
from web3 import Web3
from web3.providers.rpc import HTTPProvider

from bfebench.environment import Environment


class EnvironmentTest(TestCase):
    TEST_WALLET_ADDRESS = ChecksumAddress(HexAddress(HexStr("0x1D89080880C060691558eC16EF104aF5d8db000b")))
    TEST_WALLET_KEY = HexBytes("0x1ac620dde6d7d3aeb4c462bfdd2a53555e1b90b44e977a468f413fc69ce5c4b4")
    WEB3 = Web3(HTTPProvider("http://localhost:8545/"))

    def test_matching(self) -> None:
        env = Environment(web3=self.WEB3, wallet_address=self.TEST_WALLET_ADDRESS, private_key=self.TEST_WALLET_KEY)
        self.assertEqual(env.wallet_address, self.TEST_WALLET_ADDRESS)
        self.assertEqual(env.private_key, self.TEST_WALLET_KEY)

    def test_address_only(self) -> None:
        env = Environment(self.WEB3, self.TEST_WALLET_ADDRESS)
        self.assertEqual(env.wallet_address, self.TEST_WALLET_ADDRESS)
        self.assertIsNone(env.private_key)

    def test_key_only(self) -> None:
        env = Environment(self.WEB3, private_key=self.TEST_WALLET_KEY)
        self.assertEqual(env.wallet_address, self.TEST_WALLET_ADDRESS)
        self.assertEqual(env.private_key, self.TEST_WALLET_KEY)

    def test_init_no_address_no_private_key(self) -> None:
        self.assertRaises(ValueError, Environment, self.WEB3)

    def test_init_key_address_mismatch(self) -> None:
        self.assertRaises(ValueError, Environment, self.WEB3, self.TEST_WALLET_ADDRESS, "0x00")
