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

from math import log2
from unittest import TestCase

from bfebench.protocols.fairswap.protocol import Fairswap, B032
from bfebench.utils.bytes import generate_bytes
from bfebench.utils.merkle import MerkleTreeNode, MerkleTreeLeaf, from_bytes


class MerkleTest(TestCase):
    def test_init(self) -> None:
        self.assertRaises(
            ValueError,
            MerkleTreeNode,
            Fairswap.keccak,
            MerkleTreeLeaf(Fairswap.keccak, B032),
            MerkleTreeLeaf(Fairswap.keccak, B032),
            MerkleTreeLeaf(Fairswap.keccak, B032)
        )

    def test_get_proof_and_validate(self) -> None:
        for slice_count in [2, 4, 8, 16]:
            tree = from_bytes(generate_bytes(32 * slice_count), Fairswap.keccak, slice_count)
            for index, leaf in enumerate(tree.leaves):
                proof = tree.get_proof(leaf)
                self.assertEqual(len(proof), int(log2(slice_count)))
                self.assertTrue(MerkleTreeNode.validate_proof(tree.digest, leaf, index, proof, Fairswap.keccak))