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
from random import randint

from eth_typing.evm import ChecksumAddress

from ...environment import Environment
from ...utils.json_stream import JsonObjectSocketStream
from ..strategy import BuyerStrategy, SellerStrategy
from .perun import ChannelParams, get_funding_id
from .protocol import StateChannelFairswap


class FaithfulSeller(SellerStrategy[StateChannelFairswap]):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        pass  # TODO implement


class FaithfulBuyer(BuyerStrategy[StateChannelFairswap]):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        # generate state channel information
        assert self.protocol.app_contract.address is not None

        channel_params = ChannelParams(
            challenge_duration=self.protocol.timeout,
            nonce=randint(0, 2 ** 256),
            participants=[opposite_address, environment.wallet_address],
            app=self.protocol.app_contract.address,
            ledger_channel=True,
            virtual_channel=False,
        )
        channel_id = channel_params.get_channel_id()
        funding_id = get_funding_id(channel_id, environment.wallet_address)

        asset_holder_web3_contract = environment.get_web3_contract(
            self.protocol.asset_holder_contract
        )

        for swap_iteration in range(1, self.protocol.swap_iterations + 1):
            if self.protocol.swap_iterations > 1:
                self.logger.debug("starting swap iteration %s" % swap_iteration)

            # ensure funding
            funding_current = asset_holder_web3_contract.functions.holdings(
                funding_id
            ).call()
            funding_required = self.protocol.price * self.protocol.swap_iterations
            if funding_current >= funding_required:
                # sufficient funding
                self.logger.debug(
                    "Funding: sufficient (%d available, %d required)"
                    % (funding_current, funding_required)
                )
            else:
                # require more funding
                funding_missing = funding_required - funding_current
                self.logger.debug(
                    "Funding: additional funding required (%d available, %d required, %d missing), depositing..."
                    % (funding_current, funding_required, funding_missing)
                )
                environment.send_contract_transaction(
                    self.protocol.asset_holder_contract,
                    "deposit",
                    funding_id,
                    funding_missing,
                    value=funding_missing,
                )

            # start request
