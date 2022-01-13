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
from math import log2
from random import randint
from typing import Any

from eth_typing.evm import ChecksumAddress

from ...contract import Contract, SolidityContractSourceCodeManager
from ...environment import Environment
from ...errors import ProtocolInitializationError
from ...protocols import Protocol
from ..fairswap.protocol import DEFAULT_SLICE_LENGTH, DEFAULT_TIMEOUT
from .perun import Channel

logger = logging.getLogger(__name__)


class StateChannelFileSale(Protocol):
    SOLC_VERSION = "0.7.0"

    PERUN_ADJUDICATOR_CONTRACT_NAME = "Adjudicator"
    PERUN_ADJUDICATOR_CONTRACT_FILE = "perun-eth-contracts/contracts/Adjudicator.sol"

    PERUN_ASSET_HOLDER_CONTRACT_NAME = "AssetHolderETH"
    PERUN_ASSET_HOLDER_CONTRACT_FILE = (
        "perun-eth-contracts/contracts/AssetHolderETH.sol"
    )

    FILE_SALE_APP_CONTRACT_NAME = "FileSaleApp"
    FILE_SALE_APP_CONTRACT_FILE = "./FileSaleApp.sol"

    FILE_SALE_HELPER_CONTRACT_NAME = "FileSaleHelper"
    FILE_SALE_HELPER_CONTRACT_FILE = "./FileSaleHelper.sol"

    def __init__(
        self,
        slice_length: int | None = None,
        slice_count: int | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        file_sale_iterations: int = 1,
        seller_deposit: int = 0,
        buyer_deposit: int | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        file_size = os.path.getsize(self.filename)

        if slice_count is None:
            if slice_length is None:
                self._slice_length = DEFAULT_SLICE_LENGTH

            if (file_size / self._slice_length).is_integer():
                self._slice_count = int(file_size / self._slice_length)
            else:
                raise ProtocolInitializationError(
                    "file_size / slice_length must be int"
                )
        else:
            if slice_length is None:
                if (file_size / slice_count).is_integer():
                    self._slice_length = int(file_size / slice_count)
                else:
                    raise ProtocolInitializationError(
                        "file_size / slice_count must be int"
                    )
            else:
                raise ProtocolInitializationError(
                    "you cannot set both slice_length and slice_count"
                )

        if not log2(self._slice_count).is_integer():
            raise ProtocolInitializationError("slice_count must be a power of 2")

        if self._slice_length % 32 > 0:
            raise ProtocolInitializationError("slice_length must be a multiple of 32")

        self._timeout = int(timeout)

        self._file_sale_iterations = int(file_sale_iterations)

        if not self._file_sale_iterations >= 1:
            raise ValueError("_file_sale_iterations must be an int >= 1")

        self._seller_deposit = int(seller_deposit)
        self._buyer_deposit: int | None = None
        if buyer_deposit is not None:
            self._buyer_deposit = int(buyer_deposit)

        self._adjudicator_contract: Contract | None = None
        self._asset_holder_contract: Contract | None = None
        self._app_contract: Contract | None = None
        self._helper_contract: Contract | None = None
        self._channel_params: Channel.Params | None = None

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
            os.path.join(contracts_root_path, self.FILE_SALE_APP_CONTRACT_FILE)
        )
        scscm.add_contract_file(
            os.path.join(contracts_root_path, self.FILE_SALE_HELPER_CONTRACT_FILE)
        )
        contracts = scscm.compile(self.SOLC_VERSION)
        self._adjudicator_contract = contracts[self.PERUN_ADJUDICATOR_CONTRACT_NAME]
        self._asset_holder_contract = contracts[self.PERUN_ASSET_HOLDER_CONTRACT_NAME]
        self._app_contract = contracts[self.FILE_SALE_APP_CONTRACT_NAME]
        self._helper_contract = contracts[self.FILE_SALE_HELPER_CONTRACT_NAME]

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

        tx_receipt = environment.deploy_contract(self._helper_contract)
        logger.debug(
            "deployed helper contract at %s (%s gas used)"
            % (self._helper_contract.address, tx_receipt["gasUsed"])
        )

    def set_up_iteration(
        self,
        environment: Environment,
        seller_address: ChecksumAddress,
        buyer_address: ChecksumAddress,
    ) -> None:
        app_contract_address = self.app_contract.address
        if app_contract_address is None:
            raise RuntimeError("accessing uninitialized contract")

        self._channel_params = Channel.Params(
            challenge_duration=self.timeout,
            nonce=randint(0, 2 ** 256),
            participants=[seller_address, buyer_address],
            app=app_contract_address,
            ledger_channel=True,
            virtual_channel=False,
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
    def helper_contract(self) -> Contract:
        if self._helper_contract is None:
            raise RuntimeError("accessing uninitialized contract")
        return self._helper_contract

    @property
    def slice_count(self) -> int:
        return self._slice_count

    @property
    def slice_length(self) -> int:
        return self._slice_length

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def file_sale_iterations(self) -> int:
        return self._file_sale_iterations

    @property
    def seller_deposit(self) -> int:
        return self._seller_deposit

    @property
    def buyer_deposit(self) -> int:
        if self._buyer_deposit is not None:
            return self._buyer_deposit
        else:
            return self._file_sale_iterations * self._price

    @property
    def channel_params(self) -> Channel.Params:
        if self._channel_params is None:
            raise RuntimeError("accessing uninitialized channel params")
        return self._channel_params
