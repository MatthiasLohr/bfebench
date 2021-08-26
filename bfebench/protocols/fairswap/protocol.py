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
from typing import Any, Dict, List, Tuple, Type

from Crypto.Hash import keccak
from web3 import Web3

from bfebench.strategy import SellerStrategy, BuyerStrategy
from bfebench.utils.merkle import MerkleTreeNode, MerkleTreeLeaf, MerkleTreeHashLeaf, from_leaves
from bfebench.utils.xor import xor_crypt
from .strategies import FaithfulSeller, FaithfulBuyer
from .. import Protocol


B032 = b'\x00' * 32


class Fairswap(Protocol):
    name = 'Fairswap'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # TODO implement

    @staticmethod
    def get_seller_strategies() -> Dict[str, Type[SellerStrategy]]:
        return {
            'Faithful': FaithfulSeller
        }

    @staticmethod
    def get_buyer_strategies() -> Dict[str, Type[BuyerStrategy]]:
        return {
            'Faithful': FaithfulBuyer
        }

    @staticmethod
    def keccak(data: bytes) -> bytes:
        return keccak.new(data=data, digest_bytes=32).digest()

    @staticmethod
    def crypt(value: bytes, index: int, key: bytes) -> bytes:
        return xor_crypt(value, Web3.solidityKeccak(['uint256', 'bytes32'], [index, key]))

    @staticmethod
    def encode(root: MerkleTreeNode, key: bytes) -> MerkleTreeNode:
        leaves_enc = [Fairswap.crypt(leaf.data, index, key) for index, leaf in enumerate(root.leaves)]
        digests_enc = [Fairswap.crypt(digest, 2 * len(leaves_enc) + index, key) for index, digest in
                       enumerate(root.digests_pack)]
        return from_leaves([MerkleTreeLeaf(Fairswap.keccak, x) for x in leaves_enc]
                           + [MerkleTreeHashLeaf(Fairswap.keccak, x) for x in digests_enc]
                           + [MerkleTreeHashLeaf(Fairswap.keccak, B032)])

    @staticmethod
    def encode_forge_first_leaf(root: MerkleTreeNode, key: bytes) -> MerkleTreeNode:
        leaf_data = [leaf.data for leaf in root.leaves]
        leaf_data[0] = b'\0' * len(leaf_data[0])
        leaf_data_enc = [Fairswap.crypt(data, index, key) for index, data in enumerate(leaf_data)]
        digests_enc = [Fairswap.crypt(digest, 2 * len(leaf_data_enc) + index, key) for index, digest in
                       enumerate(root.digests_pack)]
        return from_leaves([MerkleTreeLeaf(Fairswap.keccak, x) for x in leaf_data_enc]
                           + [MerkleTreeHashLeaf(Fairswap.keccak, x) for x in digests_enc]
                           + [MerkleTreeHashLeaf(Fairswap.keccak, B032)])

    @staticmethod
    def encode_forge_first_leaf_first_hash(root: MerkleTreeNode, key: bytes) -> MerkleTreeNode:
        leaf_data = [leaf.data for leaf in root.leaves]
        leaf_data[0] = b'\0' * len(leaf_data[0])
        leaf_data_enc = [Fairswap.crypt(data, index, key) for index, data in enumerate(leaf_data)]
        digests = root.digests_pack
        digests[0] = MerkleTreeNode(
            Fairswap.keccak,
            MerkleTreeLeaf(Fairswap.keccak, leaf_data[0]),
            MerkleTreeLeaf(Fairswap.keccak, leaf_data[1])
        ).digest
        digests_enc = [
            Fairswap.crypt(digest, 2 * len(leaf_data_enc) + index, key) for index, digest in enumerate(digests)
        ]
        return from_leaves(
            [
                MerkleTreeLeaf(Fairswap.keccak, x) for x in leaf_data_enc
            ] + [
                MerkleTreeHashLeaf(Fairswap.keccak, x) for x in digests_enc
            ] + [
                MerkleTreeHashLeaf(Fairswap.keccak, B032)
            ]
        )

    @staticmethod
    def decode(root: MerkleTreeNode, key: bytes) -> Tuple[MerkleTreeNode, List['NodeDigestMismatchError']]:
        leaf_bytes_enc = root.leaves
        if not log2(len(leaf_bytes_enc)).is_integer():
            raise ValueError('Merkle Tree must have 2^x leaves')
        if leaf_bytes_enc[-1] != B032:
            raise ValueError('The provided Merkle Tree does not appear to be encoded')

        errors: List[NodeDigestMismatchError] = []
        digest_start_index = int(len(leaf_bytes_enc) / 2)
        node_index = 0
        digest_index = digest_start_index
        nodes: List[MerkleTreeNode] = [MerkleTreeLeaf(Fairswap.keccak, Fairswap.crypt(leaf_bytes_enc[i].data, i, key))
                                       for i in range(0, digest_start_index)]
        while len(nodes) > 1:
            nodes_new = []
            for i in range(0, len(nodes), 2):
                node = MerkleTreeNode(Fairswap.keccak, nodes[i], nodes[i + 1])
                expected_digest = Fairswap.crypt(
                    leaf_bytes_enc[digest_index].data,
                    digest_start_index + digest_index, key
                )

                if node_index < digest_start_index:
                    error_type: Type[NodeDigestMismatchError] = LeafDigestMismatchError
                    actual_digest = node.digest
                else:
                    error_type = NodeDigestMismatchError
                    actual_digest = Web3.solidityKeccak(['bytes32', 'bytes32'], [
                        Fairswap.crypt(leaf_bytes_enc[node_index].data, digest_start_index + node_index, key),
                        Fairswap.crypt(leaf_bytes_enc[node_index + 1].data, digest_start_index + node_index + 1, key)
                    ])

                if expected_digest != actual_digest:
                    errors.append(error_type(
                        in1=leaf_bytes_enc[node_index],
                        in2=leaf_bytes_enc[node_index + 1],
                        out=leaf_bytes_enc[digest_index],
                        index_in=node_index,
                        index_out=digest_index,
                        expected_digest=expected_digest,
                        actual_digest=actual_digest
                    ))

                node_index += 2
                digest_index += 1
                nodes_new.append(node)

            nodes = nodes_new

        return nodes[0], errors


class DecodingError(Exception):
    pass


class NodeDigestMismatchError(DecodingError):
    def __init__(self, in1: MerkleTreeLeaf, in2: MerkleTreeLeaf, out: MerkleTreeLeaf, index_in: int,
                 index_out: int, expected_digest: bytes, actual_digest: bytes) -> None:
        self.in1 = in1
        self.in2 = in2
        self.out = out
        self.index_in = index_in
        self.index_out = index_out
        self.expected_digest = expected_digest
        self.actual_digest = actual_digest


class LeafDigestMismatchError(NodeDigestMismatchError):
    pass
