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

from math import log2

from eth_typing.evm import ChecksumAddress

from .protocol import FairswapReusable, FileSaleSession
from ..fairswap.util import keccak, encode, decode, B032, LeafDigestMismatchError, NodeDigestMismatchError
from ..strategy import SellerStrategy, BuyerStrategy
from ...environment import Environment, EnvironmentWaitResult
from ...utils.bytes import generate_bytes
from ...utils.json_stream import JsonObjectSocketStream
from ...utils.merkle import from_bytes, mt2obj, obj2mt


class FaithfulSeller(SellerStrategy[FairswapReusable]):
    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream,
            opposite_address: ChecksumAddress) -> None:
        # === PHASE 1: transfer file / initialize ===
        # transmit encrypted data
        with open(self.protocol.filename, 'rb') as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        data_merkle_digest = data_merkle.digest
        data_key = generate_bytes(32)
        data_merkle_encrypted = encode(data_merkle, data_key)

        p2p_stream.send_object({
            'tree': mt2obj(data_merkle_encrypted, encode_func=lambda b: bytes(b).hex())
        })

        session_id = self.protocol.get_session_id(
            seller=environment.wallet_address,
            buyer=opposite_address,
            file_root_hash=data_merkle_digest
        )

        self.logger.debug('initializing smart contract')
        environment.send_contract_transaction(
            self.protocol.contract,
            'init',
            opposite_address,
            int(log2(self.protocol.slice_count) + 1),
            self.protocol.slice_length,
            self.protocol.slice_count,
            self.protocol.timeout,
            self.protocol.price,
            keccak(data_key),
            data_merkle_encrypted.digest,
            data_merkle_digest
        )

        # === PHASE 2: wait for buyer accept ===
        self.logger.debug('waiting for accept')
        web3_contract = environment.get_web3_contract(self.protocol.contract)

        result = environment.wait(
            timeout=FileSaleSession(*web3_contract.functions.sessions(session_id).call()).timeout + 1,
            condition=lambda: FileSaleSession(*web3_contract.functions.sessions(session_id).call()).phase == 2
        )

        if result == EnvironmentWaitResult.TIMEOUT:
            self.logger.debug('timeout reached, requesting refund')
            environment.send_contract_transaction(self.protocol.contract, 'refund', session_id)
            return
        self.logger.debug('accepted')

        # === PHASE 3: reveal key ===
        environment.send_contract_transaction(self.protocol.contract, 'revealKey', session_id, data_key)

        # === PHASE 5: finalize
        self.logger.debug('waiting for confirmation or timeout...')
        result = environment.wait(
            timeout=FileSaleSession(*web3_contract.functions.sessions(session_id).call()).timeout + 1,
            condition=lambda: not FileSaleSession(*web3_contract.functions.sessions(session_id).call()).length
        )
        if result == EnvironmentWaitResult.TIMEOUT:
            self.logger.debug('timeout reached, requesting refund')
            environment.send_contract_transaction(self.protocol.contract, 'refund', session_id)
            return


class FairswapReusableBuyer(BuyerStrategy[FairswapReusable]):
    def __init__(self, protocol: FairswapReusable) -> None:
        super().__init__(protocol)

        # caching expected file digest here to avoid hashing to be counted during execution
        with open(self.protocol.filename, 'rb') as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        self._expected_plain_digest = data_merkle.digest

    @property
    def expected_plain_digest(self) -> bytes:
        return self._expected_plain_digest

    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream,
            opposite_address: ChecksumAddress) -> None:
        raise NotImplementedError()


class FaithfulBuyer(FairswapReusableBuyer):
    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream,
            opposite_address: ChecksumAddress) -> None:
        # === PHASE 1: wait for seller initialization ===
        init_info, byte_count = p2p_stream.receive_object()
        data_merkle_encrypted = obj2mt(
            data=init_info.get('tree'),
            digest_func=keccak,
            decode_func=lambda s: bytes.fromhex(str(s))
        )

        session_id = self.protocol.get_session_id(
            seller=environment.wallet_address,
            buyer=opposite_address,
            file_root_hash=self.expected_plain_digest
        )

        web3_contract = environment.get_web3_contract(self.protocol.contract)

        # === PHASE 2: accept ===
        session_info = FileSaleSession(*web3_contract.functions.sessions(session_id).call())
        if session_info.file_root == self.expected_plain_digest:
            self.logger.debug('confirming plain file hash')
        else:
            self.logger.debug('wrong plain file hash')
            return

        if session_info.ciphertext_root == data_merkle_encrypted.digest:
            self.logger.debug('confirming ciphertext hash')
        else:
            self.logger.debug('wrong ciphertext hash')
            return

        environment.send_contract_transaction(self.protocol.contract, 'accept', session_id, value=self.protocol.price)

        # === PHASE 3: wait for key revelation ===
        self.logger.debug('waiting for key revelation')
        result = environment.wait(
            timeout=FileSaleSession(*web3_contract.functions.sessions(session_id).call()).timeout + 1,
            condition=lambda: FileSaleSession(*web3_contract.functions.sessions(session_id).call()).key != B032
        )
        if result == EnvironmentWaitResult.TIMEOUT:
            self.logger.debug('timeout reached, requesting refund')
            environment.send_contract_transaction(self.protocol.contract, 'refund', session_id)
            return

        data_key = FileSaleSession(*web3_contract.functions.sessions(session_id).call()).key
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
                self.protocol.contract,
                'complainAboutLeaf',
                session_id,
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
                self.protocol.contract,
                'complainAboutNode',
                session_id,
                error.index_out,
                error.index_in,
                error.out.data,
                error.in1.data,
                error.in2.data,
                data_merkle_encrypted.get_proof(error.out),
                data_merkle_encrypted.get_proof(error.in1)
            )
            return


class GrievingBuyer(BuyerStrategy[FairswapReusable]):
    def run(self, environment: Environment, p2p_stream: JsonObjectSocketStream,
            opposite_address: ChecksumAddress) -> None:
        self.logger.debug('do(ing) nothing, successfully.')  # see `man true`
        return
