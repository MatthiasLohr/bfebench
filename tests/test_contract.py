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

import os
from unittest import TestCase

from bfebench.contract import SolidityContractSourceCodeManager
from bfebench.protocols.fairswap.util import B032


class ContractCollectionTest(TestCase):
    def test_compile_fairswap(self) -> None:
        contracts_path = os.path.join(
            os.path.dirname(__file__), "../bfebench/protocols/fairswap"
        )

        scscm = SolidityContractSourceCodeManager()
        scscm.add_contract_template_file(
            contract_template_file=os.path.join(contracts_path, "fairswap.tpl.sol"),
            context={
                "merkle_tree_depth": 3,
                "slice_length": 32,
                "slice_count": 4,
                "receiver": "0x0000000000000000000000000000000000000000",
                "price": 1000000000,
                "key_commitment": "0x" + B032.hex(),
                "ciphertext_root_hash": "0x" + B032.hex(),
                "file_root_hash": "0x" + B032.hex(),
                "timeout": 10,
            },
        )

        contracts = scscm.compile("0.6.1")

        self.assertIn("FileSale", contracts)

    def test_compile_fairswap_reusable(self) -> None:
        pass  # TODO implement

    def test_compile_state_channel_fairswap(self) -> None:
        contracts_path = os.path.join(
            os.path.dirname(__file__),
            "../bfebench/protocols/state_channel_fairswap/perun-eth-contracts",
        )

        scscm = SolidityContractSourceCodeManager(allowed_paths=[contracts_path])
        scscm.add_contract_file(
            os.path.join(contracts_path, "contracts/Adjudicator.sol")
        )
        scscm.add_contract_file(
            os.path.join(contracts_path, "contracts/AssetHolderETH.sol")
        )

        contracts = scscm.compile("0.7.0")

        self.assertIn("Adjudicator", contracts)
        self.assertIn("AssetHolderETH", contracts)
