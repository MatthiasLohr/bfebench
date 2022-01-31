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

from ....utils.merkle import MerkleTreeNode
from ...fairswap.util import encode_forge_first_leaf
from .seller import StateChannelFileSaleSeller


class LeafForgingSeller(StateChannelFileSaleSeller):
    def encode_file(self, root: MerkleTreeNode, key: bytes, iteration: int) -> MerkleTreeNode:
        if self.protocol.is_last_iteration(iteration):
            return encode_forge_first_leaf(root, key)
        else:
            return super().encode_file(root, key, iteration)
