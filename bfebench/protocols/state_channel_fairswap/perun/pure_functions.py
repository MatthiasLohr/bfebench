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

from eth_abi import encode_abi
from eth_typing.evm import ChecksumAddress
from web3 import Web3

from .channel import ChannelState


def get_funding_id(channel_id: bytes, participant: ChecksumAddress) -> bytes:
    encoded = "0x" + encode_abi(["bytes32", "address"], [channel_id, participant]).hex()
    return bytes(Web3.solidityKeccak(["bytes"], [encoded]))


def hash_state(channel_state: ChannelState) -> bytes:
    pass  # TODO implement
