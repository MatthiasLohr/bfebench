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

from enum import Enum
from time import sleep, time
from typing import Any, Callable

from eth_typing.evm import ChecksumAddress
from hexbytes.main import HexBytes
from web3 import Web3
from web3.contract import Contract as Web3Contract
from web3.middleware.geth_poa import geth_poa_middleware
from web3.middleware.signing import construct_sign_and_send_raw_middleware
from eth_account.account import Account
from web3.types import TxReceipt

from .contract import Contract


DEFAULT_WAIT_POLL_INTERVAL = 0.3  # 300 ms


class EnvironmentWaitResult(Enum):
    TIMEOUT = 1
    CONDITION = 2


class Environment(object):
    def __init__(self, web3: Web3, wallet_address: ChecksumAddress | None = None,
                 private_key: HexBytes | None = None, wait_poll_interval: float = DEFAULT_WAIT_POLL_INTERVAL) -> None:
        self._web3 = web3
        self._wait_poll_interval = wait_poll_interval

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

        self._total_tx_count = 0
        self._total_tx_fees = 0

        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if self.private_key is not None:
            self.web3.middleware_onion.add(construct_sign_and_send_raw_middleware(self.private_key))

    @property
    def web3(self) -> Web3:
        return self._web3

    @property
    def wallet_address(self) -> ChecksumAddress:
        return self._wallet_address

    @property
    def private_key(self) -> HexBytes | None:
        return self._private_key

    @property
    def total_tx_count(self) -> int:
        return self._total_tx_count

    @property
    def total_tx_fees(self) -> int:
        return self._total_tx_fees

    @property
    def wait_poll_interval(self) -> float:
        return self._wait_poll_interval

    def deploy_contract(self, contract: Contract, *constructor_args: Any, **constructor_kwargs: Any) -> ChecksumAddress:
        web3_contract = self.web3.eth.contract(abi=contract.abi, bytecode=contract.bytecode)
        tx_receipt = self._send_transaction(
            factory=web3_contract.constructor(*constructor_args, **constructor_kwargs)
        )
        contract.address = ChecksumAddress(tx_receipt['contractAddress'])
        return contract.address

    def get_web3_contract(self, contract: Contract) -> Web3Contract:
        return self._web3.eth.contract(address=contract.address, abi=contract.abi)

    def send_contract_transaction(self, contract: Contract, method: str, *args: Any, value: int = 0,
                                  **kwargs: Any) -> TxReceipt:
        web3_contract = self.get_web3_contract(contract)
        web3_contract_method = getattr(web3_contract.functions, method)
        tx_receipt = self._send_transaction(
            factory=web3_contract_method(*args, **kwargs),
            value=value
        )
        return tx_receipt

    def send_direct_transaction(self, to: ChecksumAddress | None, value: int = 0) -> None:
        self._send_transaction(to=to, value=value)

    def _send_transaction(self, to: ChecksumAddress | None = None, factory: Any | None = None,
                          value: int = 0) -> TxReceipt:
        tx_draft = {
            'from': self.wallet_address,
            'nonce': self.web3.eth.get_transaction_count(self.wallet_address, 'pending'),
            'chainId': self.web3.eth.chain_id,
            'value': value
        }

        if to is not None:
            tx_draft['to'] = to

        if factory is not None:
            tx_draft = factory.buildTransaction(tx_draft)

        tx_hash = self.web3.eth.send_transaction(tx_draft)
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        self._total_tx_count += 1
        self._total_tx_fees += tx_receipt['gasUsed']  # type: ignore

        return tx_receipt

    def wait(self, timeout: float | None = None, condition: Callable[[], Any] | None = None,
             wait_poll_interval: float | None = None) -> EnvironmentWaitResult:
        if wait_poll_interval is None:
            wait_poll_interval = self._wait_poll_interval

        if condition is None:
            if timeout is None:
                raise ValueError('timeout and condition cannot be None simultaneously')

            sleep(timeout - time())
            while self.web3.eth.get_block('latest').get('timestamp') < timeout:
                sleep(wait_poll_interval)
            return EnvironmentWaitResult.TIMEOUT

        while True:
            if condition():
                return EnvironmentWaitResult.CONDITION

            if timeout is not None:
                if time() > timeout and self.web3.eth.get_block('latest').get('timestamp') >= timeout:
                    return EnvironmentWaitResult.TIMEOUT

            sleep(wait_poll_interval)

    def get_balance(self) -> int:
        return self.web3.eth.get_balance(self.wallet_address)
