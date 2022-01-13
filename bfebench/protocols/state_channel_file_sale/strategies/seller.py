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

from eth_typing.evm import ChecksumAddress

from bfebench.utils.json_stream import JsonObjectSocketStream

from ....environment import Environment
from ...strategy import SellerStrategy
from ..perun import Adjudicator, AssetHolder
from ..protocol import StateChannelFileSale
from .file_sale_helper import FileSaleHelper


class StateChannelFileSaleSeller(SellerStrategy[StateChannelFileSale]):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        # ======== OPEN STATE CHANNEL ========
        # See: https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#open-phase
        channel_info = self.open_state_channel(environment, p2p_stream)

        # validate remote signature
        if not file_sale_helper.validate_signed_channel_state(
            channel_state=channel_info.state,
            signature=channel_info.sigs[1],
            signer=opposite_address,
        ):
            self.logger.error("Buyer's signature invalid!")
            return

        # ======== FUND STATE CHANNEL ========
        self.fund_state_channel(
            environment,
            file_sale_helper.get_funding_id(
                channel_info.state.channel_id, environment.wallet_address
            ),
        )

        # ======== EXECUTE FILE EXCHANGE ========
        while True:
            msg, _ = p2p_stream.receive_object()
            self.logger.debug("Received '%s' message from buyer" % msg["action"])
            if msg["action"] == "request":
                # ======== EXECUTE FILE EXCHANGE ========
                self.conduct_file_sale()

            elif msg["action"] == "close":
                # ======== CLOSE STATE CHANNEL ========
                # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
                channel_info.sigs[1] = bytes.fromhex(msg["signature"])
                self.close_state_channel(environment, channel_info)
                return

    def open_state_channel(
        self, environment: Environment, p2p_stream: JsonObjectSocketStream
    ) -> Adjudicator.SignedState:
        # ======== OPEN STATE CHANNEL ========
        # See: https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#open-phase
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        channel_state = file_sale_helper.get_initial_channel_state(
            self.protocol.channel_params
        )

        msg, _ = p2p_stream.receive_object()
        assert msg["action"] == "open"
        remote_signature = bytes.fromhex(msg["signature"])

        p2p_stream.send_object(
            {
                "action": "open",
                "signature": file_sale_helper.sign_channel_state(channel_state).hex(),
            }
        )

        return Adjudicator.SignedState(
            params=self.protocol.channel_params,
            state=channel_state,
            sigs=[file_sale_helper.sign_channel_state(channel_state), remote_signature],
        )

    def fund_state_channel(self, environment: Environment, funding_id: bytes) -> None:
        if self.protocol.seller_deposit > 0:
            environment.send_contract_transaction(
                self.protocol.asset_holder_contract,
                "deposit",
                funding_id,
                self.protocol.seller_deposit,
                value=self.protocol.seller_deposit,
            )

    def conduct_file_sale(self) -> None:
        pass  # TODO implement

    def close_state_channel(
        self, environment: Environment, channel_info: Adjudicator.SignedState
    ) -> None:
        # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
        file_sale_helper = FileSaleHelper(environment, self.protocol)

        channel_info.state.is_final = True
        channel_info.sigs[0] = file_sale_helper.sign_channel_state(channel_info.state)

        environment.send_contract_transaction(
            self.protocol.adjudicator_contract,
            "concludeFinal",
            tuple(self.protocol.channel_params),
            tuple(channel_info.state),
            channel_info.sigs,
        )

        funding_id = file_sale_helper.get_funding_id(
            channel_info.state.channel_id, environment.wallet_address
        )
        authorization = AssetHolder.WithdrawalAuth(
            channel_id=channel_info.state.channel_id,
            participant=environment.wallet_address,
            receiver=environment.wallet_address,
            amount=file_sale_helper.get_funding_holdings(
                funding_id
            ),  # TODO change amount
        )
        environment.send_contract_transaction(
            self.protocol.asset_holder_contract,
            "withdraw",
            tuple(authorization),
            file_sale_helper.sign_withdrawal_auth(authorization),
        )
