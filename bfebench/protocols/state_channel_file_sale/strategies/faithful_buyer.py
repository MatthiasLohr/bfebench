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
from .buyer import StateChannelFileSaleBuyer
from .file_sale_helper import FileSaleHelper


class FaithfulBuyer(StateChannelFileSaleBuyer):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        # ======== PREPARE STATE CHANNEL ========
        file_sale_helper = FileSaleHelper(environment, self.protocol)
        channel_id = file_sale_helper.get_channel_id(self.protocol.channel_params)
        funding_id = file_sale_helper.get_funding_id(
            channel_id, environment.wallet_address
        )

        for file_sale_iteration in range(1, self.protocol.file_sale_iterations + 1):
            if self.protocol.file_sale_iterations > 1:
                self.logger.debug(
                    "starting file sale iteration %s" % file_sale_iteration
                )

            # ensure funding
            funding_current = file_sale_helper.get_funding_holdings(funding_id)
            funding_required = self.protocol.price * self.protocol.file_sale_iterations
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

            # ======== REQUEST EXCHANGE ========
            pass  # TODO implement

            # ======== WAIT FOR ENCRYPTED FILE / INITIALIZATION ========
            pass  # TODO implement

            # ======== CHECK HASHES / ACCEPT ========
            pass  # TODO implement

            # ======== WAIT FOR KEY REVELATION ========
            pass  # TODO implement

            # ======== VALIDATE KEY / CONFIRM / SIGN FINAL STATE / COMPLAIN ========
            pass  # TODO implement
