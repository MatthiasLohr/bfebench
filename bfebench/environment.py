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

from typing import Optional

from eth_typing.evm import ChecksumAddress
from hexbytes.main import HexBytes
from web3 import Web3
from eth_account.account import Account


class Environment(object):
    def __init__(self, web3: Web3, wallet_address: Optional[ChecksumAddress] = None,
                 private_key: Optional[HexBytes] = None) -> None:
        self._web3 = web3

        if private_key is None:
            if wallet_address is None:
                raise ValueError('you need to provide wallet_address or private_key or both')
            self._wallet_address = wallet_address
            self._private_key = None
        else:
            self._private_key = private_key
            self._wallet_address = Account.from_key(self._private_key).address
            if wallet_address is not None and self._wallet_address != wallet_address:
                raise ValueError('provided wallet address (%s) does not match private key\'s public address (%s)' % (
                    wallet_address,
                    self._wallet_address
                ))

    @property
    def web3(self) -> Web3:
        return self._web3

    @property
    def wallet_address(self) -> ChecksumAddress:
        return self._wallet_address

    @property
    def private_key(self) -> Optional[HexBytes]:
        return self._private_key
