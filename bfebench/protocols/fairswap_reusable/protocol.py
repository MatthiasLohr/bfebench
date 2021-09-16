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

import logging
import os
from enum import IntEnum
from typing import Any, NamedTuple

from eth_typing.evm import ChecksumAddress

from ..fairswap.protocol import Fairswap
from ..fairswap.util import keccak
from ...contract import SolidityContractCollection, Contract
from ...environment import Environment


logger = logging.getLogger(__name__)


class FileSaleStage(IntEnum):
    CREATED = 0
    INITIALIZED = 1
    ACCEPTED = 2
    KEY_REVEALED = 3
    FINISHED = 4


class FileSaleSession(NamedTuple):
    key_commit: bytes
    ciphertext_root: bytes
    file_root: bytes
    key: bytes
    sender: ChecksumAddress
    receiver: ChecksumAddress
    depth: int
    length: int
    n: int
    timeout: int
    timeout_interval: int
    price: int
    phase: FileSaleStage


class FairswapReusable(Fairswap):
    CONTRACT_FILE = 'fairswap_reusable.sol'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        contract_collection = SolidityContractCollection()
        contract_collection.add_contract_file(
            FairswapReusable.CONTRACT_NAME,
            os.path.join(os.path.dirname(__file__), FairswapReusable.CONTRACT_FILE)
        )
        self._contract = contract_collection.get(FairswapReusable.CONTRACT_NAME)

    def set_up_simulation(self, environment: Environment, seller_address: ChecksumAddress,
                          buyer_address: ChecksumAddress) -> None:
        environment.deploy_contract(self._contract)

    @property
    def contract(self) -> Contract:
        return self._contract

    @staticmethod
    def get_session_id(seller: ChecksumAddress, buyer: ChecksumAddress, file_root_hash: bytes) -> bytes:
        return keccak(bytes.fromhex(seller[2:]) + bytes.fromhex(buyer[2:]) + file_root_hash)
