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

import os
from typing import Any
from unittest import TestCase

from eth_tester import PyEVMBackend
from hexbytes import HexBytes
from web3 import Web3

from bfebench.contract import Contract, SolidityContractSourceCodeManager
from bfebench.environment import Environment
from bfebench.protocols.state_channel_fairswap import StateChannelFairswap
from bfebench.protocols.state_channel_fairswap.perun import ChannelParams


class PerunChannelTest(TestCase):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._environment: Environment | None = None
        self._contract: Contract | None = None

    @property
    def environment(self) -> Environment:
        if self._environment is None:
            self._environment = Environment(
                web3=Web3(
                    Web3.EthereumTesterProvider(
                        PyEVMBackend(
                            genesis_state={
                                b"\x15\xcb]Ph5h\xa7@\xc0\xbb\x837\xf7B\xb29]}q": {
                                    "balance": 1000000000000000000000,
                                    "nonce": 0,
                                    "code": b"",
                                    "storage": {},
                                },
                                b"~_ER\t\x1ai\x12]]\xfc\xb7\xb8\xc2e\x90)9[\xdf": {
                                    "balance": 1000000000000000000000,
                                    "nonce": 0,
                                    "code": b"",
                                    "storage": {},
                                },
                            }
                        )
                    )
                ),
                wallet_address=Web3.toChecksumAddress(
                    "0x15CB5d50683568A740c0bb8337F742B2395D7D71"
                ),
                private_key=HexBytes(
                    "0x4fde7191483ae6eedbe01e6bbecff3a332048d596d58a73db1cd2cc4b64cf2e0"
                ),
            )

        return self._environment

    @property
    def contract(self) -> Contract:
        if self._contract is None:
            contracts_root_path = os.path.dirname(__file__)
            scscm = SolidityContractSourceCodeManager(
                allowed_paths=[contracts_root_path]
            )
            scscm.add_contract_file(
                os.path.join(contracts_root_path, "contracts/perun_test.sol")
            )
            contracts = scscm.compile(StateChannelFairswap.SOLC_VERSION)
            self._contract = contracts["PerunTest"]
            self.environment.deploy_contract(self._contract)

        return self._contract

    def test_channel_id(self) -> None:
        channel_params_list = [
            ChannelParams(
                challenge_duration=60,
                nonce=1,
                participants=[
                    Web3.toChecksumAddress(
                        "0x598eC01a78be6945e5cB4C0451c5CF185211e96d"
                    ),
                    Web3.toChecksumAddress(
                        "0x65a3A53e899601d0C49C668bB1a7Bc06a5B23F35"
                    ),
                ],
                app=self.contract.address,
                ledger_channel=True,
                virtual_channel=False,
            )
        ]

        web3_contract = self.environment.get_web3_contract(self.contract)

        # check if test deployment worked
        self.assertEqual(web3_contract.functions.getRandomNumber().call(), 4)

        # check actual smart contract methods
        for channel_params in channel_params_list:
            self.assertEqual(
                channel_params.get_channel_id(), 0  # TODO replace with contract calls
            )
