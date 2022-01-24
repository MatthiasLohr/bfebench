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
from ...strategy import BuyerStrategy
from ..perun import Adjudicator
from ..protocol import StateChannelFileSale
from .file_sale_helper import FileSaleHelper


class StateChannelFileSaleBuyer(BuyerStrategy[StateChannelFileSale]):
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
            signature=channel_info.sigs[0],
            signer=opposite_address,
        ):
            self.logger.error("Seller's signature invalid!")
            return

        # ======== FUND STATE CHANNEL ========
        self.fund_state_channel(
            environment,
            file_sale_helper.get_funding_id(channel_info.state.channel_id, environment.wallet_address),
        )

        # ======== EXECUTE FILE EXCHANGE ========
        for file_sale_iteration in range(1, self.protocol.file_sale_iterations + 1):
            if self.protocol.file_sale_iterations > 1:
                self.logger.debug("starting file sale iteration %s" % file_sale_iteration)

            self.conduct_file_sale(p2p_stream, file_sale_iteration)

        # ======== CLOSE STATE CHANNEL ========
        # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
        self.close_state_channel(environment, p2p_stream, channel_info)

    def open_state_channel(
        self, environment: Environment, p2p_stream: JsonObjectSocketStream
    ) -> Adjudicator.SignedState:
        # ======== OPEN STATE CHANNEL ========
        # See: https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#open-phase
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        channel_state = file_sale_helper.get_initial_channel_state(self.protocol.channel_params)

        p2p_stream.send_object(
            {
                "action": "open",
                "signature": file_sale_helper.sign_channel_state(channel_state).hex(),
            }
        )

        msg, _ = p2p_stream.receive_object()
        assert msg["action"] == "open"
        remote_signature = bytes.fromhex(msg["signature"])

        return Adjudicator.SignedState(
            params=self.protocol.channel_params,
            state=channel_state,
            sigs=[remote_signature, file_sale_helper.sign_channel_state(channel_state)],
        )

    def fund_state_channel(self, environment: Environment, funding_id: bytes) -> None:
        if self.protocol.buyer_deposit > 0:
            environment.send_contract_transaction(
                self.protocol.asset_holder_contract,
                "deposit",
                funding_id,
                self.protocol.buyer_deposit,
                value=self.protocol.buyer_deposit,
            )

    def conduct_file_sale(self, iteration: int) -> None:
        pass  # TODO implement

    def close_state_channel(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        channel_info: Adjudicator.SignedState,
    ) -> None:
        # ======== CLOSE STATE CHANNEL ========
        # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
        file_sale_helper = FileSaleHelper(environment, self.protocol)

        channel_info.state.is_final = True
        p2p_stream.send_object(
            {
                "action": "close",
                "signature": file_sale_helper.sign_channel_state(channel_info.state).hex(),
            }
        )
