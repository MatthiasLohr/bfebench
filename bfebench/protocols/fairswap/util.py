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
from typing import List, Tuple, Type

from Crypto.Hash import keccak as base_keccak

from bfebench.utils.merkle import MerkleTreeLeaf, MerkleTreeNode, from_leaves
from bfebench.utils.xor import xor_crypt

B032 = b"\x00" * 32


def keccak(data: bytes) -> bytes:
    return base_keccak.new(data=data, digest_bytes=32).digest()


def crypt(value: bytes, index: int, key: bytes) -> bytes:
    return xor_crypt(value, keccak(index.to_bytes(length=32, byteorder="big") + key))


def encode(root: MerkleTreeNode, key: bytes) -> MerkleTreeNode:
    leaves_enc = [crypt(leaf.data, index, key) for index, leaf in enumerate(root.leaves)]
    digests_enc = [crypt(digest, len(leaves_enc) + index, key) for index, digest in enumerate(root.digests_pack)]
    return from_leaves(
        [MerkleTreeLeaf(keccak, x) for x in leaves_enc]
        + [MerkleTreeLeaf(keccak, x) for x in digests_enc]
        + [MerkleTreeLeaf(keccak, B032)]
    )


def encode_forge_first_leaf(root: MerkleTreeNode, key: bytes) -> MerkleTreeNode:
    leaf_data = [leaf.data for leaf in root.leaves]
    leaf_data[0] = b"\0" * len(leaf_data[0])
    leaf_data_enc = [crypt(data, index, key) for index, data in enumerate(leaf_data)]
    digests_enc = [crypt(digest, len(leaf_data_enc) + index, key) for index, digest in enumerate(root.digests_pack)]
    return from_leaves(
        [MerkleTreeLeaf(keccak, x) for x in leaf_data_enc]
        + [MerkleTreeLeaf(keccak, x) for x in digests_enc]
        + [MerkleTreeLeaf(keccak, B032)]
    )


def encode_forge_first_leaf_first_hash(root: MerkleTreeNode, key: bytes) -> MerkleTreeNode:
    leaf_data = [leaf.data for leaf in root.leaves]
    leaf_data[0] = b"\0" * len(leaf_data[0])
    leaf_data_enc = [crypt(data, index, key) for index, data in enumerate(leaf_data)]
    digests = root.digests_pack
    digests[0] = MerkleTreeNode(
        keccak,
        MerkleTreeLeaf(keccak, leaf_data[0]),
        MerkleTreeLeaf(keccak, leaf_data[1]),
    ).digest
    digests_enc = [crypt(digest, len(leaf_data_enc) + index, key) for index, digest in enumerate(digests)]
    return from_leaves(
        [MerkleTreeLeaf(keccak, x) for x in leaf_data_enc]
        + [MerkleTreeLeaf(keccak, x) for x in digests_enc]
        + [MerkleTreeLeaf(keccak, B032)]
    )


def decode(root: MerkleTreeNode, key: bytes) -> Tuple[MerkleTreeNode, List["NodeDigestMismatchError"]]:
    leaf_bytes_enc = root.leaves
    if not log2(len(leaf_bytes_enc)).is_integer():
        raise ValueError("Merkle Tree must have 2^x leaves")
    if leaf_bytes_enc[-1] != B032:
        raise ValueError("The provided Merkle Tree does not appear to be encoded")

    errors: List[NodeDigestMismatchError] = []
    digest_start_index = int(len(leaf_bytes_enc) / 2)
    node_index = 0
    digest_index = digest_start_index
    nodes: List[MerkleTreeNode] = [
        MerkleTreeLeaf(keccak, crypt(leaf_bytes_enc[i].data, i, key)) for i in range(0, digest_start_index)
    ]
    while len(nodes) > 1:
        nodes_new = []
        for i in range(0, len(nodes), 2):
            node = MerkleTreeNode(keccak, nodes[i], nodes[i + 1])
            expected_digest = crypt(
                leaf_bytes_enc[digest_index].data,
                digest_index,
                key,
            )

            if node_index < digest_start_index:
                error_type: Type[NodeDigestMismatchError] = LeafDigestMismatchError
                actual_digest = node.digest
            else:
                error_type = NodeDigestMismatchError
                actual_digest = keccak(
                    crypt(
                        leaf_bytes_enc[node_index].data,
                        node_index,
                        key,
                    )
                    + crypt(
                        leaf_bytes_enc[node_index + 1].data,
                        node_index + 1,
                        key,
                    )
                )

            if expected_digest != actual_digest:
                errors.append(
                    error_type(
                        in1=leaf_bytes_enc[node_index],
                        in2=leaf_bytes_enc[node_index + 1],
                        out=leaf_bytes_enc[digest_index],
                        index_in=node_index,
                        index_out=digest_index,
                        expected_digest=expected_digest,
                        actual_digest=actual_digest,
                    )
                )

            node_index += 2
            digest_index += 1
            nodes_new.append(node)

        nodes = nodes_new

    return nodes[0], errors


class DecodingError(Exception):
    pass


class NodeDigestMismatchError(DecodingError):
    def __init__(
        self,
        in1: MerkleTreeLeaf,
        in2: MerkleTreeLeaf,
        out: MerkleTreeLeaf,
        index_in: int,
        index_out: int,
        expected_digest: bytes,
        actual_digest: bytes,
    ) -> None:
        self.in1 = in1
        self.in2 = in2
        self.out = out
        self.index_in = index_in
        self.index_out = index_out
        self.expected_digest = expected_digest
        self.actual_digest = actual_digest


class LeafDigestMismatchError(NodeDigestMismatchError):
    pass
