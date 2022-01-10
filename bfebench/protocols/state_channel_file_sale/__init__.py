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

from bfebench.protocols import ProtocolSpec

from .protocol import StateChannelFileSale
from .strategies import (
    FaithfulBuyer,
    FaithfulSeller,
    GrievingSeller,
    LeafForgingSeller,
    NodeForgingSeller,
    RootForgingSeller,
)

PROTOCOL_SPEC = ProtocolSpec(
    protocol=StateChannelFileSale,
    seller_strategies={
        "Faithful": FaithfulSeller,
        "Grieving": GrievingSeller,
        "LeafForging": LeafForgingSeller,
        "NodeForging": NodeForgingSeller,
        "RootForging": RootForgingSeller,
    },
    buyer_strategies={"Faithful": FaithfulBuyer},
)
