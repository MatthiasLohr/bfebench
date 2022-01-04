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

from typing import cast

from eth_typing.evm import ChecksumAddress

from ....environment import Environment
from ..perun import Channel
from ..protocol import StateChannelFileSale


class FileSaleHelper(object):
    def __init__(
        self, environment: Environment, protocol: StateChannelFileSale
    ) -> None:
        self._adjudicator_web3_contract = environment.get_web3_contract(
            protocol.adjudicator_contract
        )
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
