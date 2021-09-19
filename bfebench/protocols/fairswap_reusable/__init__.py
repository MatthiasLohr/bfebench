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

from .protocol import FairswapReusable
from .strategies import FaithfulSeller, FaithfulBuyer, GrievingBuyer
from ..protocol_spec import ProtocolSpec


PROTOCOL_SPEC = ProtocolSpec(
    protocol=FairswapReusable,
    seller_strategies={
        'Faithful': FaithfulSeller
    },
    buyer_strategies={
        'Faithful': FaithfulBuyer,
        'Grieving': GrievingBuyer
    }
)