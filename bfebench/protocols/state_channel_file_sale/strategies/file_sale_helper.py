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

from typing import cast

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing.evm import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3

from ....environment import Environment
from ..file_sale import FileSale
from ..perun import Channel
from ..protocol import StateChannelFileSale


class FileSaleHelper(object):
    def __init__(
        self, environment: Environment, protocol: StateChannelFileSale
    ) -> None:
        self._adjudicator_web3_contract = environment.get_web3_contract(
            protocol.adjudicator_contract
        )
        self._app_web3_contract = environment.get_web3_contract(protocol.app_contract)
        self._asset_holder_web3_contract = environment.get_web3_contract(
            protocol.asset_holder_contract
        )
        self._helper_web3_contract = environment.get_web3_contract(
            protocol.helper_contract
        )

    def get_channel_id(self, channel_params: Channel.Params) -> bytes:
        # TODO replace with Python-only version
        # currently blocked by https://github.com/ethereum/web3.py/issues/1065
        return cast(
            bytes,
            self._adjudicator_web3_contract.functions.channelID(
                tuple(channel_params)
            ).call(),
        )

    def get_funding_id(self, channel_id: bytes, participant: ChecksumAddress) -> bytes:
        # TODO replace with Python-only version
        return cast(
            bytes,
            self._helper_web3_contract.functions.getFundingID(
                channel_id, participant
            ).call(),
        )

    def get_funding_holdings(self, funding_id: bytes) -> int:
        return cast(
            int, self._asset_holder_web3_contract.functions.holdings(funding_id).call()
        )

    def is_valid_transition(
        self,
        channel_params: Channel.Params,
        state_from: Channel.State,
        state_to: Channel.State,
    ) -> bool:
        self._app_web3_contract.functions.validTransition(
            channel_params, state_from, state_to
        ).call()
        pass  # TODO check outcome for error
        return False

    def encode_channel_params(self, params: Channel.Params) -> bytes:
        return cast(
            bytes,
            self._helper_web3_contract.functions.encodeChannelParams(
                tuple(params)
            ).call(),
        )

    def encode_channel_state(self, state: Channel.State) -> bytes:
        return cast(
            bytes,
            self._helper_web3_contract.functions.encodeChannelState(
                tuple(state)
            ).call(),
        )

    def hash_channel_state(self, state: Channel.State) -> bytes:
        return bytes(Web3.solidityKeccak(["bytes"], [self.encode_channel_state(state)]))

    def sign_channel_state(
        self, state: Channel.State, private_key: HexBytes | bytes
    ) -> bytes:
        signed_message = Account.sign_message(
            encode_defunct(self.hash_channel_state(state)), private_key
        )
        return bytes(signed_message.signature)

    def encode_app_data(self, app_state: FileSale.AppState) -> bytes:
        return cast(
            bytes,
            self._helper_web3_contract.functions.encodeAppState(
                tuple(app_state)
            ).call(),
        )
