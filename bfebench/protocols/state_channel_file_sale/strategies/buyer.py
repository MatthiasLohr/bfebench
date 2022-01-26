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
from ....utils.merkle import from_bytes, obj2mt
from ...fairswap.util import LeafDigestMismatchError, decode, keccak
from ...strategy import BuyerStrategy
from ..file_sale import FileSale
from ..file_sale_helper import FileSaleHelper
from ..perun import Adjudicator, Channel
from ..protocol import StateChannelDisagreement, StateChannelFileSale


class StateChannelFileSaleBuyer(BuyerStrategy[StateChannelFileSale]):
    def __init__(self, protocol: StateChannelFileSale) -> None:
        super().__init__(protocol)

        # caching expected file digest here to avoid hashing to be counted during execution
        with open(self.protocol.filename, "rb") as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        self._expected_plain_digest = data_merkle.digest

    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        # ======== OPEN STATE CHANNEL ========
        # See: https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#open-phase
        last_common_state = self.open_state_channel(environment, p2p_stream)

        # validate remote signature
        if not file_sale_helper.validate_signed_channel_state(
            channel_state=last_common_state.state,
            signature=last_common_state.sigs[0],
            signer=opposite_address,
        ):
            self.logger.error("Seller's signature invalid!")
            return

        # ======== FUND STATE CHANNEL ========
        self.fund_state_channel(
            environment,
            file_sale_helper.get_funding_id(last_common_state.state.channel_id, environment.wallet_address),
        )

        # ======== EXECUTE FILE EXCHANGE ========
        for file_sale_iteration in range(1, self.protocol.file_sale_iterations + 1):
            if self.protocol.file_sale_iterations > 1:
                self.logger.debug("starting file sale iteration %s" % file_sale_iteration)

            try:
                self.conduct_file_sale(
                    last_common_state=last_common_state,
                    environment=environment,
                    p2p_stream=p2p_stream,
                    opposite_address=opposite_address,
                    iteration=file_sale_iteration,
                )
            except StateChannelDisagreement as disagreement:
                self.logger.debug("channel disagreement: " + str(disagreement))
                self.dispute(environment, disagreement.last_common_state, disagreement.register)
                return

        # ======== CLOSE STATE CHANNEL ========
        # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
        self.close_state_channel(environment, p2p_stream, last_common_state)

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

    def conduct_file_sale(
        self,
        last_common_state: Adjudicator.SignedState,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
        iteration: int,
    ) -> None:
        file_sale_helper = FileSaleHelper(environment, self.protocol)

        self.logger.debug("Requesting file (iteration %d)" % iteration)
        p2p_stream.send_object({"action": "request", "file_root": self._expected_plain_digest.hex()})

        # === PHASE 1: wait for seller initialization ===
        msg_init, _ = p2p_stream.receive_object()
        assert msg_init["action"] == "initialize"
        data_merkle_encrypted = obj2mt(
            data=msg_init.get("tree"),
            digest_func=keccak,
            decode_func=lambda s: bytes.fromhex(str(s)),
        )
        key_commitment = bytes.fromhex(msg_init["key_commitment"])

        # === PHASE 2: accept (check before!) ===
        assert bytes.fromhex(msg_init["file_root"]) == self._expected_plain_digest
        assert bytes.fromhex(msg_init["ciphertext_root"]) == data_merkle_encrypted.digest
        proposed_app_state = FileSale.AppState(
            file_root=bytes.fromhex(msg_init["file_root"]),
            ciphertext_root=bytes.fromhex(msg_init["ciphertext_root"]),
            key_commitment=bytes.fromhex(msg_init["key_commitment"]),
            price=msg_init["price"],
        )
        proposed_channel_state = Channel.State(
            channel_id=last_common_state.state.channel_id,
            outcome=last_common_state.state.outcome,
            app_data=proposed_app_state.encode_abi(),
        )
        if not file_sale_helper.validate_signed_channel_state(
            channel_state=proposed_channel_state,
            signature=bytes.fromhex(msg_init["signature"]),
            signer=opposite_address,
        ):
            raise StateChannelDisagreement("init signature mismatch", last_common_state, False)

        self.logger.debug("init signature validated")
        last_common_state.state = proposed_channel_state
        last_common_state.sigs = [
            bytes.fromhex(msg_init["signature"]),
            file_sale_helper.sign_channel_state(proposed_channel_state),
        ]

        p2p_stream.send_object(
            {"action": "accept", "signature": file_sale_helper.sign_channel_state(proposed_channel_state).hex()}
        )

        # === PHASE 3: wait for key revelation ===
        self.logger.debug("waiting for key revelation")
        msg_key_revelation, _ = p2p_stream.receive_object()
        assert msg_key_revelation["action"] == "reveal_key"
        data_key = bytes.fromhex(msg_key_revelation["key"])

        proposed_app_state.key = data_key
        proposed_channel_state.app_data = proposed_app_state.encode_abi()
        proposed_channel_state.outcome.balances = [
            [
                last_common_state.state.outcome.balances[0][0] + self.protocol.price,
                last_common_state.state.outcome.balances[0][1] - self.protocol.price,
            ]
        ]
        if not file_sale_helper.validate_signed_channel_state(
            channel_state=proposed_channel_state,
            signature=bytes.fromhex(msg_key_revelation["signature"]),
            signer=opposite_address,
        ):
            raise StateChannelDisagreement("key revelation signature mismatch", last_common_state, False)

        # === PHASE 4: complain ===
        if keccak(data_key) != key_commitment:
            raise StateChannelDisagreement("key does not match commitment", last_common_state, False)

        data_merkle, errors = decode(data_merkle_encrypted, data_key)
        if len(errors) == 0:
            self.logger.debug("file successfully decrypted, quitting.")
            p2p_stream.send_object({"action": "confirm", "signature": None})  # TODO send signature
            return
        elif isinstance(errors[-1], LeafDigestMismatchError):
            # TODO implement complainAboutLeaf
            # error: NodeDigestMismatchError = errors[-1]
            # environment.send_contract_transaction(
            #     contract,
            #     "complainAboutLeaf",
            #     error.index_out,
            #     error.index_in,
            #     error.out.data,
            #     error.in1.data_as_list(),
            #     error.in2.data_as_list(),
            #     data_merkle_encrypted.get_proof(error.out),
            #     data_merkle_encrypted.get_proof(error.in1),
            # )
            return
        else:
            # TODO implement complainAboutNode
            # error = errors[-1]
            # environment.send_contract_transaction(
            #     contract,
            #     "complainAboutNode",
            #     error.index_out,
            #     error.index_in,
            #     error.out.data,
            #     error.in1.data,
            #     error.in2.data,
            #     data_merkle_encrypted.get_proof(error.out),
            #     data_merkle_encrypted.get_proof(error.in1),
            #  )
            return

    def close_state_channel(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        last_common_state: Adjudicator.SignedState,
    ) -> None:
        # ======== CLOSE STATE CHANNEL ========
        # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
        file_sale_helper = FileSaleHelper(environment, self.protocol)

        last_common_state.state.is_final = True
        p2p_stream.send_object(
            {
                "action": "close",
                "signature": file_sale_helper.sign_channel_state(last_common_state.state).hex(),
            }
        )

    def dispute(self, environment: Environment, last_common_state: Adjudicator.SignedState, register: bool) -> None:
        if register:
            self.logger.debug("registering dispute")
            environment.send_contract_transaction(
                self.protocol.adjudicator_contract, "register", tuple(last_common_state), []
            )

        # TODO implement
