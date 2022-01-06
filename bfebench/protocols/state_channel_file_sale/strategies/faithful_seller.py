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
from ..file_sale import FileSale
from ..perun import Channel
from .file_sale_helper import FileSaleHelper
from .seller import StateChannelFileSaleSeller


class FaithfulSeller(StateChannelFileSaleSeller):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        # ======== PREPARE STATE CHANNEL ========
        asset_holder_contract_address = self.protocol.asset_holder_contract.address
        assert asset_holder_contract_address is not None
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        channel_id = file_sale_helper.get_channel_id(self.protocol.channel_params)
        channel_state = Channel.State(
            channel_id=channel_id,
            allocation=Channel.Allocation(
                assets=[asset_holder_contract_address],
                balances=[[0, 0]],
                locked=[],
            ),
        )
        app_state = FileSale.AppState()

        while True:
            message, _ = p2p_stream.receive_object()
            if message["action"] == "request":
                self.logger.debug("Received 'request' message from buyer")
                # ======== WAIT FOR INCOMING EXCHANGE REQUEST ========
                pass  # TODO

                # ======== CHECK FOR SUFFICIENT FUNDING ========
                pass  # TODO

                # ======== SEND ENCRYPTED FILE / INITIALIZE ========
                pass  # TODO

                # ======== WAIT FOR ACCEPT ========
                pass  # TODO

                # ======== REVEAL KEY ========
                pass  # TODO

            elif message["action"] == "conclude":
                self.logger.debug("Received 'conclude' message from buyer")
                channel_state.app_data = file_sale_helper.encode_app_data(app_state)
                channel_state.is_final = True

                # conclude channel
                private_key = environment.private_key
                assert private_key is not None

                environment.send_contract_transaction(
                    self.protocol.adjudicator_contract,
                    "concludeFinal",
                    tuple(self.protocol.channel_params),
                    tuple(channel_state),
                    [
                        file_sale_helper.sign_channel_state(channel_state, private_key),
                        bytes.fromhex(message["signature"]),
                    ],
                )

                # request payout
                # TODO payout the money
                return
