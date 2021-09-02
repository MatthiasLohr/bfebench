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

from bfebench.protocols.fairswap.util import (
    B032,
    keccak,
    encode,
    encode_forge_first_leaf,
    encode_forge_first_leaf_first_hash,
    decode,
    LeafDigestMismatchError,
    NodeDigestMismatchError
)
from bfebench.utils.bytes import generate_bytes
from bfebench.utils.merkle import from_bytes, mt2obj, obj2mt


class EncodingTest(TestCase):
    def test_encode_decode(self) -> None:
        key = generate_bytes(32)
        for size, slice_count in [(128, 4), (1024, 16)]:
            data = generate_bytes(size)
            tree = from_bytes(data, keccak, slice_count)
            tree_enc = encode(tree, key)

            tree_enc_obj = mt2obj(tree_enc, encode_func=lambda b: bytes(b).hex())
            tree_enc_obj2mt = obj2mt(tree_enc_obj, digest_func=keccak, decode_func=lambda s: bytes.fromhex(str(s)))

            self.assertEqual(tree_enc.leaves, tree_enc_obj2mt.leaves)
            self.assertEqual(tree_enc.digest, tree_enc_obj2mt.digest)

            tree_dec, errors = decode(tree_enc, key)
            self.assertEqual([], errors)
            self.assertEqual(tree, tree_dec)
            self.assertEqual(tree.digest, tree_dec.digest)

    def test_encode_forge_first_leaf(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), keccak, 4)
        tree_enc = encode_forge_first_leaf(tree, B032)
        tree_dec, errors = decode(tree_enc, B032)
        self.assertEqual(1, len(errors))
        self.assertEqual(LeafDigestMismatchError, type(errors[0]))

    def test_encode_forge_first_leaf_first_hash(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), keccak, 4)
        tree_enc = encode_forge_first_leaf_first_hash(tree, B032)
        tree_dec, errors = decode(tree_enc, B032)
        self.assertEqual(1, len(errors))
        self.assertEqual(NodeDigestMismatchError, type(errors[0]))
