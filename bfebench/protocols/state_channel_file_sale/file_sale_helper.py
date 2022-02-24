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
from typing import Any, Generator, Tuple, cast

from eth_abi.abi import encode_abi
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing.evm import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.filters import LogFilter
from web3.contract import ContractFunction
from web3.datastructures import AttributeDict

from ...environment import Environment
from ..fairswap.util import B032
from .file_sale import FileSale
from .perun import Adjudicator, AssetHolder, Channel
from .protocol import StateChannelFileSale

logger = logging.getLogger(__name__)


class FileSaleHelper(object):
    def __init__(self, environment: Environment, protocol: StateChannelFileSale) -> None:
        self._environment = environment
        self._protocol = protocol

        self._adjudicator_web3_contract = self._environment.get_web3_contract(self._protocol.adjudicator_contract)
        self._app_web3_contract = self._environment.get_web3_contract(protocol.app_contract)
        self._asset_holder_web3_contract = self._environment.get_web3_contract(self._protocol.asset_holder_contract)
        self._helper_web3_contract = self._environment.get_web3_contract(self._protocol.helper_contract)

    def get_channel_id(self, channel_params: Channel.Params) -> bytes:
        # TODO replace with Python-only version
        # currently blocked by https://github.com/ethereum/web3.py/issues/1065
        return cast(
            bytes,
            self._adjudicator_web3_contract.functions.channelID(tuple(channel_params)).call(),
        )

    def get_funding_id(self, channel_id: bytes, participant: ChecksumAddress) -> bytes:
        # TODO replace with Python-only version
        return cast(
            bytes,
            self._helper_web3_contract.functions.getFundingID(channel_id, participant).call(),
        )

    def get_funding_holdings(self, funding_id: bytes) -> int:
        return int(self._asset_holder_web3_contract.functions.holdings(funding_id).call())

    def is_valid_transition(
        self,
        channel_params: Channel.Params,
        state_from: Channel.State,
        state_to: Channel.State,
    ) -> bool:
        self._app_web3_contract.functions.validTransition(channel_params, state_from, state_to).call()
        pass  # TODO check outcome for error
        return False

    def encode_channel_params(self, params: Channel.Params) -> bytes:
        return cast(
            bytes,
            self._helper_web3_contract.functions.encodeChannelParams(tuple(params)).call(),
        )

    def encode_channel_state(self, state: Channel.State) -> bytes:
        try:
            return cast(
                bytes,
                self._helper_web3_contract.functions.encodeChannelState(tuple(state)).call(),
            )
        except OverflowError as e:
            logger.error("overflow error on channel state: %s" % str(tuple(state)))
            raise e

    def hash_channel_state(self, state: Channel.State) -> bytes:
        return bytes(Web3.solidityKeccak(["bytes"], [self.encode_channel_state(state)]))

    def sign_channel_state(self, channel_state: Channel.State, private_key: HexBytes | bytes | None = None) -> bytes:
        if private_key is None:
            private_key = self._environment.private_key

        signed_message = Account.sign_message(encode_defunct(self.hash_channel_state(channel_state)), private_key)
        return bytes(signed_message.signature)

    def validate_signed_channel_state(
        self,
        channel_state: Channel.State,
        signature: HexBytes | bytes,
        signer: ChecksumAddress,
    ) -> bool:
        recovered_signer = Account.recover_message(
            encode_defunct(self.hash_channel_state(channel_state)),
            signature=signature,
        )

        return bool(recovered_signer == signer)

    @staticmethod
    def encode_withdrawal_auth(authorization: AssetHolder.WithdrawalAuth) -> bytes:
        return encode_abi(["(bytes32,address,address,uint256)"], [tuple(authorization)])

    def hash_withdrawal_auth(self, authorization: AssetHolder.WithdrawalAuth) -> bytes:
        return bytes(Web3.solidityKeccak(["bytes"], [self.encode_withdrawal_auth(authorization)]))

    def sign_withdrawal_auth(
        self,
        authorization: AssetHolder.WithdrawalAuth,
        private_key: HexBytes | bytes | None = None,
    ) -> bytes:
        if private_key is None:
            private_key = self._environment.private_key

        signed_message = Account.sign_message(encode_defunct(self.hash_withdrawal_auth(authorization)), private_key)
        return bytes(signed_message.signature)

    def get_initial_channel_state(self, channel_params: Channel.Params) -> Channel.State:
        return Channel.State(
            channel_id=self.get_channel_id(channel_params),
            version=1,
            outcome=Channel.Allocation(
                assets=[self._asset_holder_web3_contract.address],
                balances=[[self._protocol.seller_deposit, self._protocol.buyer_deposit]],
                locked=[],
            ),
            app_data=FileSale.AppState().encode_abi(),
        )

    def withdraw_holdings(self, channel_id: bytes) -> None:
        funding_id = self.get_funding_id(channel_id, self._environment.wallet_address)
        holdings = self.get_funding_holdings(funding_id)
        if holdings > 0:
            authorization = AssetHolder.WithdrawalAuth(
                channel_id=channel_id,
                participant=self._environment.wallet_address,
                receiver=self._environment.wallet_address,
                amount=holdings,
            )
            self._environment.send_contract_transaction(
                self._protocol.asset_holder_contract,
                "withdraw",
                tuple(authorization),
                self.sign_withdrawal_auth(authorization),
            )
            logger.debug("withdrawn %d" % holdings)

    def dispute_registered(self, channel_id: bytes) -> bool:
        return self.get_dispute(channel_id).state_hash != B032

    def get_dispute(self, channel_id: bytes) -> Adjudicator.Dispute:
        dispute_raw = self._adjudicator_web3_contract.functions.disputes(channel_id).call()
        return Adjudicator.Dispute(
            timeout=dispute_raw[0],
            challenge_duration=dispute_raw[1],
            version=dispute_raw[2],
            has_app=dispute_raw[3],
            phase=Adjudicator.DisputePhase(dispute_raw[4]),
            state_hash=dispute_raw[5],
        )

    def dispute_register(self, last_common_state: Adjudicator.SignedState) -> None:
        self._environment.send_contract_transaction(
            self._protocol.adjudicator_contract, "register", tuple(last_common_state), [], gas_limit=150000
        )

    def dispute_get_updates(
        self, channel_id: bytes
    ) -> Generator[Tuple[AttributeDict[str, Any], ContractFunction, Tuple[Any, ...]], None, None]:
        for event in self._environment.filter_events_by_name(
            self._protocol.adjudicator_contract, "ChannelUpdate", self._protocol.timeout * 2
        ):
            # skip if not current channel
            if event["args"]["channelID"] != channel_id:
                continue

            # skip we self triggered the event
            tx_receipt = self._environment.web3.eth.get_transaction_receipt(event["transactionHash"])
            assert tx_receipt is not None
            if tx_receipt["from"] == self._environment.wallet_address:
                continue

            # get cause (contract function call) and its parameters
            tx = self._environment.web3.eth.get_transaction(event["transactionHash"])
            cause, cause_params = self._adjudicator_web3_contract.decode_function_input(tx["input"])

            yield event, cause, cause_params

    def create_channel_event_filter(self) -> LogFilter:
        return cast(LogFilter, self._adjudicator_web3_contract.events.ChannelUpdate.createFilter(fromBlock="latest"))

    def update_last_state(
        self, event_filter: LogFilter, last_channel_state: Channel.State
    ) -> Tuple[Channel.State, FileSale.AppState]:
        for event in event_filter.get_new_entries():
            if event["args"]["channelID"] != last_channel_state.channel_id:
                continue

            tx = self._environment.web3.eth.get_transaction(event["transactionHash"])
            assert tx is not None
            cause, cause_parameters = self._adjudicator_web3_contract.decode_function_input(tx["input"])

            if cause.function_identifier == "register":
                signed_state = Adjudicator.SignedState.from_tuple(*cause_parameters["channel"])
                last_channel_state = signed_state.state
            elif cause.function_identifier in ("progress", "conclude"):
                last_channel_state = Channel.State.from_tuple(*cause_parameters["state"])
            else:
                raise RuntimeError("unrecognized cause: %s" % cause.function_identifier)

        return last_channel_state, FileSale.AppState.decode_abi(last_channel_state.app_data)
