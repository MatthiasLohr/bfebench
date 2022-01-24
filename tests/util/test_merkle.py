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

from base64 import b64decode, b64encode
from math import log2
from unittest import TestCase

from bfebench.protocols.fairswap.util import B032, keccak
from bfebench.utils.bytes import generate_bytes
from bfebench.utils.merkle import (
    MerkleTreeLeaf,
    MerkleTreeNode,
    from_bytes,
    mt2obj,
    obj2mt,
)


class MerkleTest(TestCase):
    EXAMPLE_TREE1 = MerkleTreeNode(
        keccak,
        MerkleTreeNode(
            keccak,
            MerkleTreeLeaf(keccak, generate_bytes(32)),
            MerkleTreeLeaf(keccak, generate_bytes(32)),
        ),
        MerkleTreeNode(
            keccak,
            MerkleTreeLeaf(keccak, generate_bytes(32)),
            MerkleTreeLeaf(keccak, generate_bytes(32)),
        ),
    )

    def test_init(self) -> None:
        self.assertRaises(
            ValueError,
            MerkleTreeNode,
            keccak,
            MerkleTreeLeaf(keccak, B032),
            MerkleTreeLeaf(keccak, B032),
            MerkleTreeLeaf(keccak, B032),
        )

    def test_get_proof_and_validate(self) -> None:
        for slice_count in [2, 4, 8, 16]:
            tree = from_bytes(generate_bytes(32 * slice_count), keccak, slice_count)
            for index, leaf in enumerate(tree.leaves):
                proof = tree.get_proof(leaf)
                self.assertEqual(len(proof), int(log2(slice_count)))
                self.assertTrue(MerkleTreeNode.validate_proof(tree.digest, leaf, index, proof, keccak))

    def test_mt2obj2mt_plain(self) -> None:
        obj = mt2obj(self.EXAMPLE_TREE1)
        mt2 = obj2mt(obj, keccak)

        self.assertEqual(self.EXAMPLE_TREE1, mt2)
        self.assertEqual(self.EXAMPLE_TREE1.digest, mt2.digest)

    def test_mt2obj2mt_b64(self) -> None:
        obj = mt2obj(self.EXAMPLE_TREE1, b64encode)
        mt2 = obj2mt(obj, keccak, b64decode)

        self.assertEqual(self.EXAMPLE_TREE1, mt2)
        self.assertEqual(self.EXAMPLE_TREE1.digest, mt2.digest)

    def test_mt2obj2mt_hex(self) -> None:
        obj = mt2obj(self.EXAMPLE_TREE1, encode_func=lambda b: bytes(b).hex())
        mt2 = obj2mt(obj, digest_func=keccak, decode_func=lambda s: bytes.fromhex(str(s)))

        self.assertEqual(self.EXAMPLE_TREE1, mt2)
        self.assertEqual(self.EXAMPLE_TREE1.digest, mt2.digest)

    def test_obj2mt_error(self) -> None:
        self.assertRaises(ValueError, obj2mt, 3, keccak)

    def test_from_bytes_encode_decode(self) -> None:
        data = generate_bytes(32 * 2 * 16)
        tree_original = from_bytes(data, digest_func=keccak, slice_count=16)

        self.assertEqual(b"".join([leaf.data for leaf in tree_original.leaves]), data)

        tree_encoded = mt2obj(tree_original, encode_func=lambda b: bytes(b).hex())
        tree_decoded = obj2mt(
            tree_encoded,
            digest_func=keccak,
            decode_func=lambda s: bytes.fromhex(str(s)),
        )

        self.assertEqual(b"".join([leaf.data for leaf in tree_decoded.leaves]), data)
        self.assertEqual(tree_original.digest, tree_decoded.digest)
