# This file is part of the Blockchain-based Fair Exchange Benchmark Tool
#    https://gitlab.com/MatthiasLohr/bfebench
#
# Copyright 2021-2022 Matthias Lohr <mail@mlohr.com>
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

from copy import deepcopy
from time import sleep, time
from typing import Callable

from eth_typing.evm import ChecksumAddress

from ....environment import Environment
from ....utils.json_stream import JsonObjectSocketStream
from ....utils.merkle import from_bytes, obj2mt
from ...fairswap.util import (
    LeafDigestMismatchError,
    NodeDigestMismatchError,
    crypt,
    decode,
    keccak,
)
from ...strategy import BuyerStrategy
from ..file_sale import FileSale, FileSalePhase
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
                self.dispute(
                    environment=environment,
                    last_common_state=disagreement.last_common_state,
                    complain_method=disagreement.complain_method,
                )
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
            phase=FileSalePhase.ACCEPTED,
        )
        proposed_channel_state = Channel.State(
            channel_id=last_common_state.state.channel_id,
            version=last_common_state.state.version + 1,
            outcome=deepcopy(last_common_state.state.outcome),
            app_data=proposed_app_state.encode_abi(),
        )
        if not file_sale_helper.validate_signed_channel_state(
            channel_state=proposed_channel_state,
            signature=bytes.fromhex(msg_init["signature"]),
            signer=opposite_address,
        ):
            raise StateChannelDisagreement("init signature mismatch", last_common_state)

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

        proposed_app_state = FileSale.AppState(
            file_root=bytes.fromhex(msg_init["file_root"]),
            ciphertext_root=bytes.fromhex(msg_init["ciphertext_root"]),
            key_commitment=bytes.fromhex(msg_init["key_commitment"]),
            price=msg_init["price"],
            key=bytes.fromhex(msg_key_revelation["key"]),
            phase=FileSalePhase.COMPLETED,
        )
        proposed_channel_state = Channel.State(
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
            app_data=proposed_app_state.encode_abi(),
        )

        if not file_sale_helper.validate_signed_channel_state(
            channel_state=proposed_channel_state,
            signature=bytes.fromhex(msg_key_revelation["signature"]),
            signer=opposite_address,
        ):
            raise StateChannelDisagreement("key revelation signature mismatch", last_common_state)

        if keccak(proposed_app_state.key) != key_commitment:
            # released key does not match key commitment
            raise StateChannelDisagreement("key does not match commitment", last_common_state)

        if (
            crypt(data_merkle_encrypted.leaves[-2].data, 2 * self.protocol.slice_count - 2, proposed_app_state.key)
            != self._expected_plain_digest
        ):
            # released key matches key commitment,
            # but decoding root element using this key reveals wrong plain root hash
            raise StateChannelDisagreement(
                reason="decrypted plain file hash does not match",
                last_common_state=last_common_state,
                complain_method=lambda: environment.send_contract_transaction(
                    self.protocol.app_contract,
                    "complainAboutRoot",
                    tuple(last_common_state.params),
                    tuple(last_common_state.state),
                    last_common_state.sigs[0],
                    data_merkle_encrypted.leaves[-2].digest,
                    data_merkle_encrypted.get_proof(data_merkle_encrypted.leaves[-2]),
                ),
            )

        data_merkle, errors = decode(data_merkle_encrypted, proposed_app_state.key)
        if len(errors) == 0:
            self.logger.debug("file successfully decrypted")
            last_common_state.state = proposed_channel_state
            last_common_state.sigs = [
                bytes.fromhex(msg_key_revelation["signature"]),
                file_sale_helper.sign_channel_state(last_common_state.state),
            ]

            p2p_stream.send_object({"action": "confirm", "signature": last_common_state.sigs[1].hex()})
            return

        # === PHASE 4: complain ===
        elif isinstance(errors[-1], LeafDigestMismatchError):
            error: NodeDigestMismatchError = errors[-1]

            # print(MerkleTreeNode.validate_proof(
            #     data_merkle_encrypted.digest,
            #     data_merkle_encrypted.leaves[error.index_in],
            #     error.index_in,
            #     data_merkle_encrypted.get_proof(error.in1),
            #     keccak
            # ))
            #
            # print(environment.get_web3_contract(self.protocol.app_contract).functions.vrfy(
            #     error.index_in,
            #     data_merkle_encrypted.leaves[error.index_in].digest,
            #     data_merkle_encrypted.get_proof(error.in1),
            #     data_merkle_encrypted.digest
            # ).call())
            #
            # print(len(data_merkle_encrypted.leaves[error.index_in].data))
            # print(data_merkle_encrypted.leaves[error.index_in].data)
            # print(len(data_merkle_encrypted.leaves[error.index_in].digest))
            # print(data_merkle_encrypted.leaves[error.index_in].digest)

            raise StateChannelDisagreement(
                reason="leaf hash mismatch",
                last_common_state=last_common_state,
                complain_method=lambda: environment.send_contract_transaction(
                    self.protocol.app_contract,
                    "complainAboutLeaf",
                    tuple(last_common_state.params),
                    tuple(last_common_state.state),
                    last_common_state.sigs[0],
                    error.index_out,
                    error.index_in,
                    error.out.digest,
                    error.in1.data_as_list(),
                    error.in2.data_as_list(),
                    data_merkle_encrypted.get_proof(error.out),
                    data_merkle_encrypted.get_proof(error.in1),
                ),
            )
        else:
            error = errors[-1]
            raise StateChannelDisagreement(
                reason="node hash mismatch",
                last_common_state=last_common_state,
                complain_method=lambda: environment.send_contract_transaction(
                    self.protocol.app_contract,
                    "complainAboutNode",
                    tuple(last_common_state.params),
                    tuple(last_common_state.state),
                    last_common_state.sigs[0],
                    error.index_out,
                    error.index_in,
                    error.out.digest,
                    error.in1.digest,
                    error.in2.digest,
                    data_merkle_encrypted.get_proof(error.out),
                    data_merkle_encrypted.get_proof(error.in1),
                ),
            )

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

    def dispute(
        self,
        environment: Environment,
        last_common_state: Adjudicator.SignedState,
        complain_method: Callable[[], None] | None = None,
    ) -> None:
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        channel_event_filter = file_sale_helper.create_channel_event_filter()
        last_channel_state = last_common_state.state

        while True:
            dispute = file_sale_helper.get_dispute(last_common_state.state.channel_id)
            last_channel_state, last_channel_app_state = file_sale_helper.update_last_state(
                channel_event_filter, last_channel_state
            )

            if dispute.phase == Adjudicator.DisputePhase.DISPUTE:
                if (
                    last_common_state.state.outcome.balances[0][1] > 0
                    and last_common_state.state.version > dispute.version
                ):
                    # if we have a newer commonly signed state than already registered and an incentive to register:
                    file_sale_helper.dispute_register(last_common_state)
                    continue

                # if DISPUTE phase timed out and we have an incentive
                if (
                    last_channel_state.outcome.balances[0][1] > 0
                    and time() > dispute.timeout + dispute.challenge_duration + 1
                ):
                    environment.send_contract_transaction(
                        self.protocol.adjudicator_contract,
                        "conclude",
                        tuple(last_common_state.params),
                        tuple(last_channel_state),
                        [],
                    )
                    continue

            elif dispute.phase == Adjudicator.DisputePhase.FORCEEXEC:
                if last_channel_app_state.phase == FileSalePhase.COMPLETED and complain_method is not None:
                    # conduct actual complain
                    complain_method()

                    last_local_app_state = FileSale.AppState(
                        file_root=last_channel_app_state.file_root,
                        ciphertext_root=last_channel_app_state.ciphertext_root,
                        key_commitment=last_channel_app_state.key_commitment,
                        key=last_channel_app_state.key,
                        price=last_channel_app_state.price,
                        phase=FileSalePhase.COMPLAINT_SUCCESSFUL,
                    )
                    last_local_state = Channel.State(
                        channel_id=last_common_state.state.channel_id,
                        version=last_channel_state.version + 1,
                        outcome=Channel.Allocation(
                            assets=last_common_state.state.outcome.assets,
                            balances=[
                                [
                                    last_channel_state.outcome.balances[0][0] - self.protocol.price,
                                    last_channel_state.outcome.balances[0][1] + self.protocol.price,
                                ]
                            ],
                            locked=[],
                        ),
                        app_data=last_local_app_state.encode_abi(),
                    )
                    environment.send_contract_transaction(
                        self.protocol.adjudicator_contract,
                        "progress",
                        tuple(last_common_state.params),
                        tuple(last_channel_state),
                        tuple(last_local_state),
                        1,  # buyer is signing
                        file_sale_helper.sign_channel_state(last_local_state),
                    )
                    continue

                # if FORCEEXEC phase timed out and we have an incentive
                if last_channel_state.outcome.balances[0][1] > 0 and time() > dispute.timeout + 1:
                    environment.send_contract_transaction(
                        self.protocol.adjudicator_contract,
                        "conclude",
                        tuple(last_common_state.params),
                        tuple(last_channel_state),
                        [],
                    )
                    continue

            elif dispute.phase == Adjudicator.DisputePhase.CONCLUDED:
                break

            else:
                raise RuntimeError("should never reach here")
            sleep(1)

        # dispute is over, withdraw holdings
        file_sale_helper.withdraw_holdings(last_common_state.state.channel_id)
