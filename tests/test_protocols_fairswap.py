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

from bfebench.protocols.fairswap.protocol import Fairswap, B032, NodeDigestMismatchError, LeafDigestMismatchError
from bfebench.utils.bytes import generate_bytes
from bfebench.utils.merkle import from_bytes


class EncodingTest(TestCase):
    def test_encode_decode(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), Fairswap.keccak, 4)
        tree_enc = Fairswap.encode(tree, B032)
        tree_dec, errors = Fairswap.decode(tree_enc, B032)
        self.assertEqual([], errors)
        self.assertEqual(tree, tree_dec)

    def test_encode_forge_first_leaf(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), Fairswap.keccak, 4)
        tree_enc = Fairswap.encode_forge_first_leaf(tree, B032)
        tree_dec, errors = Fairswap.decode(tree_enc, B032)
        self.assertEqual(1, len(errors))
        self.assertEqual(LeafDigestMismatchError, type(errors[0]))

    def test_encode_forge_first_leaf_first_hash(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), Fairswap.keccak, 4)
        tree_enc = Fairswap.encode_forge_first_leaf_first_hash(tree, B032)
        tree_dec, errors = Fairswap.decode(tree_enc, B032)
        self.assertEqual(1, len(errors))
        self.assertEqual(NodeDigestMismatchError, type(errors[0]))
