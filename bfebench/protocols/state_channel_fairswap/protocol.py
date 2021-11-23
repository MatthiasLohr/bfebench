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

import logging
import os
from typing import Any

from eth_typing.evm import ChecksumAddress

from ...contract import Contract, SolidityContractSourceCodeManager
from ...environment import Environment
from ..fairswap.protocol import DEFAULT_TIMEOUT
from ..protocol import Protocol

logger = logging.getLogger(__name__)


class StateChannelFairswap(Protocol):
    SOLC_VERSION = "0.7.0"

    PERUN_ADJUDICATOR_CONTRACT_NAME = "Adjudicator"
    PERUN_ADJUDICATOR_CONTRACT_FILE = "perun-eth-contracts/contracts/Adjudicator.sol"

    PERUN_ASSET_HOLDER_CONTRACT_NAME = "AssetHolderETH"
    PERUN_ASSET_HOLDER_CONTRACT_FILE = (
        "perun-eth-contracts/contracts/AssetHolderETH.sol"
    )

    PERUN_APP_CONTRACT_NAME = "FileSale"
    PERUN_APP_CONTRACT_FILE = "./FileSaleApp.sol"

    def __init__(
        self,
        slice_length: int | None = None,
        slice_count: int | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        swap_iterations: int = 1,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        # TODO check slice_length, slice_count, timeout

        self._swap_iterations = int(swap_iterations)

        if not self._swap_iterations >= 1:
            raise ValueError("swap_iterations must be an int >= 1")

        self._adjudicator_contract: Contract | None = None
        self._asset_holder_contract: Contract | None = None
        self._app_contract: Contract | None = None

    def set_up_simulation(
        self,
        environment: Environment,
        seller_address: ChecksumAddress,
        buyer_address: ChecksumAddress,
    ) -> None:
        logger.debug("deploying contracts...")
        contracts_root_path = os.path.dirname(__file__)
        scscm = SolidityContractSourceCodeManager(allowed_paths=[contracts_root_path])
        scscm.add_contract_file(
            os.path.join(contracts_root_path, self.PERUN_ADJUDICATOR_CONTRACT_FILE)
        )
        scscm.add_contract_file(
            os.path.join(contracts_root_path, self.PERUN_ASSET_HOLDER_CONTRACT_FILE)
        )
        scscm.add_contract_file(
            os.path.join(contracts_root_path, self.PERUN_APP_CONTRACT_FILE)
        )
        contracts = scscm.compile(self.SOLC_VERSION)
        self._adjudicator_contract = contracts[self.PERUN_ADJUDICATOR_CONTRACT_NAME]
        self._asset_holder_contract = contracts[self.PERUN_ASSET_HOLDER_CONTRACT_NAME]
        self._app_contract = contracts[self.PERUN_APP_CONTRACT_NAME]

        tx_receipt = environment.deploy_contract(self._adjudicator_contract)
        logger.debug(
            "deployed adjudicator contract at %s (%s gas used)"
            % (self._adjudicator_contract.address, tx_receipt["gasUsed"])
        )

        tx_receipt = environment.deploy_contract(
            self._asset_holder_contract, self._adjudicator_contract.address
        )
        logger.debug(
            "deployed asset holder contract at %s (%s gas used)"
            % (self._asset_holder_contract.address, tx_receipt["gasUsed"])
        )

        tx_receipt = environment.deploy_contract(self._app_contract)
        logger.debug(
            "deployed app contract at %s (%s gas used)"
            % (self._app_contract.address, tx_receipt["gasUsed"])
        )

    @property
    def adjudicator_contract(self) -> Contract:
        if self._adjudicator_contract is None:
            raise RuntimeError("accessing uninitialized contract")
        return self._adjudicator_contract

    @property
    def asset_holder_contract(self) -> Contract:
        if self._asset_holder_contract is None:
            raise RuntimeError("accessing uninitialized contract")
        return self._asset_holder_contract

    @property
    def app_contract(self) -> Contract:
        if self._app_contract is None:
            raise RuntimeError("accessing uninitialized contract")
        return self._app_contract

    @property
    def swap_iterations(self) -> int:
        return self._swap_iterations
