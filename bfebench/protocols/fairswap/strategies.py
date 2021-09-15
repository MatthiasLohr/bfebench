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

import os
from math import log2
from time import time, sleep

from eth_typing.evm import ChecksumAddress

from .protocol import Fairswap
from .util import keccak, encode, B032, decode, LeafDigestMismatchError, NodeDigestMismatchError
from ..strategy import SellerStrategy, BuyerStrategy
from ...contract import SolidityContractCollection, Contract
from ...environment import Environment
from ...utils.bytes import generate_bytes
from ...utils.json_stream import JsonObjectSocketStream
from ...utils.merkle import from_bytes, mt2obj, obj2mt


class FaithfulSeller(SellerStrategy[Fairswap]):
    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream,
            opposite_address: ChecksumAddress) -> None:
        # === PHASE 1: transfer file / initialize (deploy contract) ===
        # transmit encrypted data
        with open(self.protocol.filename, 'rb') as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        data_key = generate_bytes(32)
        data_merkle_encrypted = encode(data_merkle, data_key)

        # deploy contract
        contract_collection = SolidityContractCollection()
        contract_collection.add_contract_template_file(
            Fairswap.CONTRACT_NAME,
            os.path.join(os.path.dirname(__file__), Fairswap.CONTRACT_TEMPLATE_FILE),
            {
                'merkle_tree_depth': log2(self.protocol.slice_count) + 1,
                'slice_length': self.protocol.slice_length,
                'slice_count': self.protocol.slice_count,
                'receiver': str(opposite_address),
                'price': self.protocol.price,
                'key_commitment': '0x' + keccak(data_key).hex(),
                'ciphertext_root_hash': '0x' + data_merkle_encrypted.digest.hex(),
                'file_root_hash': '0x' + data_merkle.digest.hex(),
                'timeout': self.protocol.timeout
            }
        )
        contract = contract_collection.get(Fairswap.CONTRACT_NAME)
        environment.deploy_contract(contract)
        web3_contract = environment.get_web3_contract(contract)

        p2p_stream.send_object({
            'contract_address': contract.address,
            'contract_abi': contract.abi,
            'tree': mt2obj(data_merkle_encrypted, encode_func=lambda b: bytes(b).hex())
        })

        # === PHASE 2: wait for buyer accept ===
        self.logger.debug('waiting for accept')
        while web3_contract.functions.phase().call() != 2:
            sleep(self.protocol.wait_poll_interval)
        self.logger.debug('accepted')

        # === PHASE 3: reveal key ===
        environment.send_contract_transaction(contract, 'revealKey', data_key)

        # === PHASE 5: finalize
        self.logger.debug('waiting for confirmation or timeout...')
        timeout = web3_contract.functions.timeout().call() + 1
        while True:
            if not environment.web3.eth.get_code(contract.address):
                self.logger.debug('contract has been destroyed. quitting.')
                return
            if time() > timeout and environment.web3.eth.get_block('latest').timestamp >= timeout:
                self.logger.debug('timeout reached, requesting payout')
                environment.send_contract_transaction(
                    contract,
                    'refund'
                )
                return
            sleep(self.protocol.wait_poll_interval)


class FaithfulBuyer(BuyerStrategy[Fairswap]):
    def __init__(self, protocol: Fairswap) -> None:
        super().__init__(protocol)

        # caching expected file digest here to avoid hashing to be counted during execution
        with open(self.protocol.filename, 'rb') as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        self._expected_plain_digest = data_merkle.digest

    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream,
            opposite_address: ChecksumAddress) -> None:
        # === PHASE 1: wait for seller initialization ===
        init_info, byte_count = p2p_stream.receive_object()
        data_merkle_encrypted = obj2mt(
            data=init_info.get('tree'),
            digest_func=keccak,
            decode_func=lambda s: bytes.fromhex(str(s))
        )
        contract = Contract(
            abi=init_info.get('contract_abi'),
            address=init_info.get('contract_address')
        )
        web3_contract = environment.get_web3_contract(contract)

        # === PHASE 2: accept ===
        if web3_contract.functions.fileRoot().call() == self._expected_plain_digest:
            self.logger.debug('confirming plain file hash')
        else:
            self.logger.debug('wrong plain file hash')
            return

        if web3_contract.functions.ciphertextRoot().call() == data_merkle_encrypted.digest:
            self.logger.debug('confirming ciphertext hash')
        else:
            self.logger.debug('wrong ciphertext hash')
            return

        environment.send_contract_transaction(contract, 'accept', value=self.protocol.price)

        # === PHASE 3: wait for key revelation ===
        self.logger.debug('waiting for key revelation')
        while web3_contract.functions.key().call() == B032:
            sleep(self.protocol.wait_poll_interval)
        data_key = web3_contract.functions.key().call()
        self.logger.debug('key revealed')

        # === PHASE 4: complain ===
        data_merkle, errors = decode(data_merkle_encrypted, data_key)
        if len(errors) == 0:
            self.logger.debug('file successfully decrypted, quitting.')
            # not calling `noComplain` here, no benefit for buyer (rational party)
            return
        elif isinstance(errors[-1], LeafDigestMismatchError):
            error: NodeDigestMismatchError = errors[-1]
            environment.send_contract_transaction(
                contract,
                'complainAboutLeaf',
                error.index_out,
                error.index_in,
                error.out.data,
                error.in1.data_as_list(),
                error.in2.data_as_list(),
                data_merkle_encrypted.get_proof(error.out),
                data_merkle_encrypted.get_proof(error.in1)
            )
            return
        else:
            error = errors[-1]
            environment.send_contract_transaction(
                contract,
                'complainAboutNode',
                error.index_out,
                error.index_in,
                error.out.data,
                error.in1.data,
                error.in2.data,
                data_merkle_encrypted.get_proof(error.out),
                data_merkle_encrypted.get_proof(error.in1)
            )
            return
