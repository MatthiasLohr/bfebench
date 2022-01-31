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

from copy import deepcopy

from eth_typing.evm import ChecksumAddress

from ....environment import Environment
from ....utils.bytes import generate_bytes
from ....utils.json_stream import JsonObjectSocketStream
from ....utils.merkle import MerkleTreeNode, from_bytes, mt2obj
from ...fairswap.util import encode, keccak
from ...strategy import SellerStrategy
from ..file_sale import FileSale, FileSalePhase
from ..file_sale_helper import FileSaleHelper
from ..perun import Adjudicator, Channel
from ..protocol import StateChannelDisagreement, StateChannelFileSale


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
        last_common_state = self.open_state_channel(environment, p2p_stream)

        # validate remote signature
        if not file_sale_helper.validate_signed_channel_state(
            channel_state=last_common_state.state,
            signature=last_common_state.sigs[1],
            signer=opposite_address,
        ):
            self.logger.error("Buyer's signature invalid!")
            return

        # ======== FUND STATE CHANNEL ========
        self.fund_state_channel(
            environment,
            file_sale_helper.get_funding_id(last_common_state.state.channel_id, environment.wallet_address),
        )

        # ======== EXECUTE FILE EXCHANGE ========
        iteration = 1
        while True:
            msg, _ = p2p_stream.receive_object()
            self.logger.debug("Received '%s' message from buyer" % msg["action"])
            if msg["action"] == "request":
                # ======== EXECUTE FILE EXCHANGE ========
                try:
                    self.conduct_file_sale(
                        last_common_state=last_common_state,
                        environment=environment,
                        p2p_stream=p2p_stream,
                        opposite_address=opposite_address,
                        file_root=bytes.fromhex(msg["file_root"]),
                        iteration=iteration,
                    )
                except StateChannelDisagreement as disagreement:
                    self.logger.debug("channel disagreement: " + str(disagreement))
                    self.dispute(
                        environment=environment,
                        last_common_state=disagreement.last_common_state,
                        register=disagreement.register,
                    )
                    return

            elif msg["action"] == "close":
                # ======== CLOSE STATE CHANNEL ========
                # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
                last_common_state.sigs[1] = bytes.fromhex(msg["signature"])
                self.close_state_channel(environment, last_common_state)
                return

            iteration += 1

    def open_state_channel(
        self, environment: Environment, p2p_stream: JsonObjectSocketStream
    ) -> Adjudicator.SignedState:
        # ======== OPEN STATE CHANNEL ========
        # See: https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#open-phase
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        channel_state = file_sale_helper.get_initial_channel_state(self.protocol.channel_params)

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

    def conduct_file_sale(
        self,
        last_common_state: Adjudicator.SignedState,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
        file_root: bytes,
        iteration: int,
    ) -> None:
        file_sale_helper = FileSaleHelper(environment, self.protocol)

        # === PHASE 1: transfer file / initialize (deploy contract) ===
        # transmit encrypted data
        with open(self.protocol.filename, "rb") as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        data_key = generate_bytes(32)
        data_merkle_encrypted = self.encode_file(data_merkle, data_key, iteration)

        new_app_state = FileSale.AppState(
            file_root=file_root,
            ciphertext_root=data_merkle_encrypted.digest,
            key_commitment=keccak(data_key),
            price=self.protocol.price,
            phase=FileSalePhase.ACCEPTED,
        )
        new_channel_state = Channel.State(
            channel_id=last_common_state.state.channel_id,
            version=last_common_state.state.version + 1,
            outcome=deepcopy(last_common_state.state.outcome),
            app_data=new_app_state.encode_abi(),
        )

        p2p_stream.send_object(
            {
                "action": "initialize",
                "file_root": new_app_state.file_root.hex(),
                "ciphertext_root": new_app_state.ciphertext_root.hex(),
                "key_commitment": new_app_state.key_commitment.hex(),
                "price": new_app_state.price,
                "tree": mt2obj(data_merkle_encrypted, encode_func=lambda b: bytes(b).hex()),
                "signature": file_sale_helper.sign_channel_state(new_channel_state).hex(),
            }
        )

        # === PHASE 2: wait for buyer accept ===
        self.logger.debug("waiting for accept")
        msg_accept, _ = p2p_stream.receive_object()
        assert msg_accept["action"] == "accept"
        if not file_sale_helper.validate_signed_channel_state(
            channel_state=new_channel_state, signature=bytes.fromhex(msg_accept["signature"]), signer=opposite_address
        ):
            raise StateChannelDisagreement("accept signature mismatch", last_common_state, True)

        last_common_state.state = new_channel_state
        last_common_state.sigs = [
            file_sale_helper.sign_channel_state(new_channel_state),
            bytes.fromhex(msg_accept["signature"]),
        ]

        self.logger.debug("accepted")

        # === PHASE 3: reveal key ===
        key_to_be_sent = self.get_key_to_be_sent(data_key, iteration)

        new_app_state = FileSale.AppState(
            file_root=file_root,
            ciphertext_root=data_merkle_encrypted.digest,
            key_commitment=keccak(data_key),
            price=self.protocol.price,
            key=key_to_be_sent,
            phase=FileSalePhase.COMPLETED,
        )
        new_channel_state = Channel.State(
            channel_id=last_common_state.state.channel_id,
            version=last_common_state.state.version + 1,
            outcome=Channel.Allocation(
                assets=last_common_state.state.outcome.assets,
                balances=[
                    [
                        last_common_state.state.outcome.balances[0][0] + self.protocol.price,
                        last_common_state.state.outcome.balances[0][1] - self.protocol.price,
                    ]
                ],
                locked=[],
            ),
            app_data=new_app_state.encode_abi(),
        )

        p2p_stream.send_object(
            {
                "action": "reveal_key",
                "key": key_to_be_sent.hex(),
                "signature": file_sale_helper.sign_channel_state(new_channel_state).hex(),
            }
        )

        # === PHASE 4: wait for confirmation
        self.logger.debug("waiting for confirmation or timeout...")
        try:
            msg_confirmation, _ = p2p_stream.receive_object(self.protocol.timeout)
            if not file_sale_helper.validate_signed_channel_state(
                channel_state=new_channel_state,
                signature=bytes.fromhex(msg_confirmation["signature"]),
                signer=opposite_address,
            ):
                raise StateChannelDisagreement("confirmation signature mismatch", last_common_state, True)
            last_common_state.state = new_channel_state
            last_common_state.sigs = [
                file_sale_helper.sign_channel_state(new_channel_state),
                bytes.fromhex(msg_confirmation["signature"]),
            ]
        except TimeoutError:
            raise StateChannelDisagreement("timeout, starting dispute", last_common_state, True)

    def encode_file(self, root: MerkleTreeNode, key: bytes, iteration: int) -> MerkleTreeNode:
        return encode(root, key)

    def close_state_channel(self, environment: Environment, last_common_state: Adjudicator.SignedState) -> None:
        # see https://labs.hyperledger.org/perun-doc/concepts/protocols_phases.html#finalize-phase
        file_sale_helper = FileSaleHelper(environment, self.protocol)

        last_common_state.state.is_final = True
        last_common_state.sigs[0] = file_sale_helper.sign_channel_state(last_common_state.state)

        environment.send_contract_transaction(
            self.protocol.adjudicator_contract,
            "concludeFinal",
            tuple(self.protocol.channel_params),
            tuple(last_common_state.state),
            last_common_state.sigs,
        )

        file_sale_helper.withdraw_holdings(last_common_state.state.channel_id)

    def dispute(self, environment: Environment, last_common_state: Adjudicator.SignedState, register: bool) -> None:
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        last_common_app_state = FileSale.AppState.decode_abi(last_common_state.state.app_data)
        self.logger.debug(
            "starting dispute based on version %d and app state %s"
            % (last_common_state.state.version, last_common_app_state.phase.name)
        )
        file_sale_helper.dispute_prepare(last_common_state, register)

        environment.send_contract_transaction(
            self.protocol.adjudicator_contract,
            "conclude",
            tuple(last_common_state.params),
            tuple(last_common_state.state),
            [],
        )

        file_sale_helper.withdraw_holdings(last_common_state.state.channel_id)

    def get_key_to_be_sent(self, original_key: bytes, iteration: int) -> bytes:
        return original_key
