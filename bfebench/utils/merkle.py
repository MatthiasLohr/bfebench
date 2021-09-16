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

from __future__ import annotations

import itertools
import math
from typing import Any, Callable, List, Tuple, Union


class MerkleTreeNode(object):
    def __init__(self, digest_func: Callable[[bytes], bytes], *children: 'MerkleTreeNode') -> None:
        if len(children) > 2:
            raise ValueError('Cannot have more than two children')

        self._digest_func = digest_func
        self._children = list(children)

    @property
    def digest_func(self) -> Callable[[bytes], bytes]:
        return self._digest_func

    @property
    def children(self) -> List['MerkleTreeNode']:
        return self._children

    @property
    def leaves(self) -> List['MerkleTreeLeaf']:
        return list(itertools.chain.from_iterable([c.leaves for c in self.children]))

    @property
    def digest(self) -> bytes:
        digest_input = b''
        for child in self.children:
            digest_input += child.digest
        return self._digest_func(digest_input)

    @property
    def digests_dfs(self) -> List[bytes]:
        return list(itertools.chain.from_iterable([c.digests_dfs for c in self.children])) + [self.digest]

    @property
    def digests_pack(self) -> List[bytes]:
        return [digest for digest, level in sorted(self._digests_pack(0), key=lambda d: d[1], reverse=True)]

    def _digests_pack(self, level: int) -> List[Tuple[bytes, int]]:
        return list(itertools.chain.from_iterable([
            c._digests_pack(level + 1) for c in self.children
        ])) + [(self.digest, level)]

    def has_indirect_child(self, node: 'MerkleTreeNode') -> bool:
        if node in self.children:
            return True

        for child in self.children:
            if child.has_indirect_child(node):
                return True

        return False

    def get_proof(self, node: 'MerkleTreeLeaf') -> List[bytes]:
        if self.children[0] == node:
            return [self.children[1].digest]
        elif self.children[1] == node:
            return [self.children[0].digest]

        if self.children[0].has_indirect_child(node):
            return [self.children[1].digest] + self.children[0].get_proof(node)
        elif self.children[1].has_indirect_child(node):
            return [self.children[0].digest] + self.children[1].get_proof(node)
        else:
            raise ValueError('Node is not part of this tree')

    @staticmethod
    def validate_proof(root_digest: bytes, node: 'MerkleTreeNode', index: int, proof: List[bytes],
                       digest_func: Callable[[bytes], bytes]) -> bool:
        tmp_digest = node.digest
        for i in range(len(proof)):
            if (index & 1 << i) >> i == 1:
                tmp_digest = digest_func(proof[len(proof) - i - 1] + tmp_digest)
            else:
                tmp_digest = digest_func(tmp_digest + proof[len(proof) - i - 1])
        return tmp_digest == root_digest

    def __repr__(self) -> str:
        return '<%s.%s %s>' % (
            __name__,
            MerkleTreeNode.__name__,
            self.digest.hex()
        )

    def __str__(self) -> str:
        return '\n  '.join(['#:' + self.digest.hex()] + '\n'.join([str(child) for child in self.children]).split('\n'))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MerkleTreeNode):
            return self.digest == other.digest
        else:
            return NotImplemented

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


class MerkleTreeLeaf(MerkleTreeNode):
    def __init__(self, digest_func: Callable[[bytes], bytes], data: bytes) -> None:
        super(MerkleTreeLeaf, self).__init__(digest_func=digest_func)
        if (len(data) % 32) != 0:
            raise ValueError('data length has to be a multiple of 32')
        self._data = data

    @property
    def digest(self) -> bytes:
        return self.digest_func(b''.join(self.data_as_list()))

    @property
    def data(self) -> bytes:
        return self._data

    @data.setter
    def data(self, data: bytes) -> None:
        self._data = data

    def data_as_list(self, slice_size: int = 32) -> List[bytes]:
        return [self.data[i * slice_size:(i + 1) * slice_size] for i in range(int(len(self.data) / slice_size))]

    @property
    def leaves(self) -> List['MerkleTreeLeaf']:
        return [self]

    @property
    def digests_dfs(self) -> List[bytes]:
        return []

    @property
    def digests_pack(self) -> List[bytes]:
        return []

    def _digests_pack(self, level: int) -> List[Tuple[bytes, int]]:
        return []

    def __repr__(self) -> str:
        return '<%s.%s %s>' % (
            __name__,
            MerkleTreeLeaf.__name__,
            str(self.data)
        )

    def __str__(self) -> str:
        return 'D:' + self.data.hex()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MerkleTreeLeaf):
            return self.data == other.data
        else:
            return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, MerkleTreeLeaf):
            return not self.data == other.data
        else:
            return False


def from_leaves(leaves: List[MerkleTreeLeaf]) -> MerkleTreeNode:
    if len(leaves) == 0:
        raise ValueError('Cannot create tree from empty list')
    digest_func = leaves[0].digest_func
    for i in range(1, len(leaves)):
        if digest_func != leaves[i].digest_func:
            raise ValueError('All leaves have to use the same digest function!')
    nodes: List[MerkleTreeNode] = list(leaves)
    while len(nodes) > 1:
        nodes = [MerkleTreeNode(digest_func, *nodes[i:i + 2]) for i in range(0, len(nodes), 2)]
    return nodes[0]


def from_bytes(data: bytes, digest_func: Callable[[bytes], bytes], slice_count: int = 8) -> MerkleTreeNode:
    if slice_count < 2 or not math.log2(slice_count).is_integer():
        raise ValueError('slices_count must be >= 2 integer and power of 2')
    slice_len = math.ceil(len(data) / slice_count)
    return from_leaves(
        [
            MerkleTreeLeaf(
                digest_func=digest_func,
                data=data[slice_len * s:slice_len * (s + 1)]
            ) for s in range(slice_count)
        ]
    )


def from_list(items: List[bytes], digest_func: Callable[[bytes], bytes]) -> MerkleTreeNode:
    return from_leaves(
        [
            MerkleTreeLeaf(
                digest_func=digest_func,
                data=item
            ) for item in items
        ]
    )


def mt2obj(node: MerkleTreeNode,
           encode_func: Callable[[bytes], Union[bytes, str]] | None = None) -> Union[bytes, str, List[Any]]:
    if isinstance(node, MerkleTreeLeaf):
        if encode_func is None:
            return node.data
        else:
            return encode_func(node.data)
    else:
        return [mt2obj(child, encode_func) for child in node.children]


def obj2mt(data: Union[bytes, str, List[Any]], digest_func: Callable[[bytes], bytes],
           decode_func: Callable[[Union[bytes, str]], bytes] | None = None) -> MerkleTreeNode:
    if isinstance(data, List):
        return MerkleTreeNode(
            digest_func,
            *[obj2mt(child, digest_func, decode_func) for child in data]
        )
    elif isinstance(data, bytes) and decode_func is None:
        return MerkleTreeLeaf(digest_func, data)
    elif (isinstance(data, bytes) or isinstance(data, str)) and decode_func is not None:
        return MerkleTreeLeaf(digest_func, decode_func(data))
    else:
        raise ValueError('cannot convert input of type %s to merkle tree' % type(data))
