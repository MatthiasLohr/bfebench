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

from .fairswap import PROTOCOL_SPEC as PROTOCOL_SPEC_FAIRSWAP
from .fairswap_reusable import PROTOCOL_SPEC as PROTOCOL_SPEC_FAIRSWAP_REUSABLE
from .protocol import Protocol
from .protocol_spec import ProtocolSpec
from .state_channel_fairswap import (
    PROTOCOL_SPEC as PROTOCOL_SPEC_STATE_CHANNEL_FAIRSWAP,
)
from .strategy import BuyerStrategy, SellerStrategy, Strategy

PROTOCOL_SPECIFICATIONS = {
    "Fairswap": PROTOCOL_SPEC_FAIRSWAP,
    "FairswapReusable": PROTOCOL_SPEC_FAIRSWAP_REUSABLE,
    "StateChannelFairswap": PROTOCOL_SPEC_STATE_CHANNEL_FAIRSWAP,
}

__all__ = [
    "BuyerStrategy",
    "Protocol",
    "ProtocolSpec",
    "PROTOCOL_SPECIFICATIONS",
    "SellerStrategy",
    "Strategy",
]
