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

from Crypto.Hash import keccak
from eth_utils.crypto import keccak as eth_keccak
from web3 import Web3

from bfebench.utils.bytes import generate_bytes


class KeccakEquivalenceTest(TestCase):
    def test_keccak_equivalence(self) -> None:
        for i in range(10):
            data = generate_bytes(32)
            self.assertEqual(eth_keccak(data), keccak.new(data=data, digest_bytes=32).digest())
            self.assertEqual(eth_keccak(data), Web3.solidityKeccak(['bytes32'], [data]))
            self.assertEqual(eth_keccak(data), Web3.solidityKeccak(['bytes32[1]'], [[data]]))
            self.assertEqual(eth_keccak(data), Web3.keccak(data))
