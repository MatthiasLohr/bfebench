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

from eth_typing.evm import ChecksumAddress

from ...contract import Contract, SolidityContractSourceCodeManager
from ...environment import Environment, EnvironmentWaitResult
from ...utils.bytes import generate_bytes
from ...utils.json_stream import JsonObjectSocketStream
from ...utils.merkle import MerkleTreeNode, from_bytes, mt2obj, obj2mt
from ..strategy import BuyerStrategy, SellerStrategy
from .protocol import Fairswap
from .util import (
    B032,
    LeafDigestMismatchError,
    NodeDigestMismatchError,
    crypt,
    decode,
    encode,
    encode_forge_first_leaf,
    encode_forge_first_leaf_first_hash,
    keccak,
)


class FaithfulSeller(SellerStrategy[Fairswap]):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        # === PHASE 1: transfer file / initialize (deploy contract) ===
        # transmit encrypted data
        with open(self.protocol.filename, "rb") as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        data_key = generate_bytes(32)
        data_merkle_encrypted = self.encode_file(data_merkle, data_key)

        # deploy contract
        scscm = SolidityContractSourceCodeManager()
        scscm.add_contract_template_file(
            os.path.join(os.path.dirname(__file__), Fairswap.CONTRACT_TEMPLATE_FILE),
            {
                "merkle_tree_depth": log2(self.protocol.slice_count) + 1,
                "slice_length": self.protocol.slice_length,
                "slice_count": self.protocol.slice_count,
                "receiver": str(opposite_address),
                "price": self.protocol.price,
                "key_commitment": "0x" + keccak(data_key).hex(),
                "ciphertext_root_hash": "0x" + data_merkle_encrypted.digest.hex(),
                "file_root_hash": "0x" + data_merkle.digest.hex(),
                "timeout": self.protocol.timeout,
            },
        )
        contracts = scscm.compile(Fairswap.CONTRACT_SOLC_VERSION)
        contract = contracts[Fairswap.CONTRACT_NAME]
        tx_receipt = environment.deploy_contract(contract)
        self.logger.debug("deployed contract at %s (%s gas used)" % (contract.address, tx_receipt["gasUsed"]))
        web3_contract = environment.get_web3_contract(contract)

        p2p_stream.send_object(
            {
                "contract_address": contract.address,
                "contract_abi": contract.abi,
                "tree": mt2obj(data_merkle_encrypted, encode_func=lambda b: bytes(b).hex()),
            }
        )

        # === PHASE 2: wait for buyer accept ===
        self.logger.debug("waiting for accept")
        result = environment.wait(
            timeout=web3_contract.functions.timeout().call() + 1,
            condition=lambda: web3_contract.functions.phase().call() == 2,
        )
        if result == EnvironmentWaitResult.TIMEOUT:
            self.logger.debug("timeout reached, requesting refund")
            environment.send_contract_transaction(contract, "refund")
            return
        self.logger.debug("accepted")

        # === PHASE 3: reveal key ===
        environment.send_contract_transaction(contract, "revealKey", data_key, gas_limit=65000)

        # === PHASE 5: finalize
        self.logger.debug("waiting for confirmation or timeout...")
        result = environment.wait(
            timeout=web3_contract.functions.timeout().call() + 1,
            condition=lambda: not environment.web3.eth.get_code(contract.address),
        )
        if result == EnvironmentWaitResult.TIMEOUT:
            self.logger.debug("timeout reached, requesting refund")
            environment.send_contract_transaction(contract, "refund")
            return

    def encode_file(self, data_merkle: MerkleTreeNode, data_key: bytes) -> MerkleTreeNode:
        return encode(data_merkle, data_key)


class RootForgingSeller(FaithfulSeller):
    def encode_file(self, data_merkle: MerkleTreeNode, data_key: bytes) -> MerkleTreeNode:
        return encode(data_merkle, generate_bytes(32, avoid=data_key))


class LeafForgingSeller(FaithfulSeller):
    def encode_file(self, data_merkle: MerkleTreeNode, data_key: bytes) -> MerkleTreeNode:
        return encode_forge_first_leaf(data_merkle, data_key)


class NodeForgingSeller(FaithfulSeller):
    def encode_file(self, data_merkle: MerkleTreeNode, data_key: bytes) -> MerkleTreeNode:
        return encode_forge_first_leaf_first_hash(data_merkle, data_key)


class FairswapBuyer(BuyerStrategy[Fairswap]):
    def __init__(self, protocol: Fairswap) -> None:
        super().__init__(protocol)

        # caching expected file digest here to avoid hashing to be counted during execution
        with open(self.protocol.filename, "rb") as fp:
            data = fp.read()
        data_merkle = from_bytes(data, keccak, slice_count=self.protocol.slice_count)
        self._expected_plain_digest = data_merkle.digest

    @property
    def expected_plain_digest(self) -> bytes:
        return self._expected_plain_digest

    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        raise NotImplementedError()


class FaithfulBuyer(FairswapBuyer):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        # === PHASE 1: wait for seller initialization ===
        init_info, byte_count = p2p_stream.receive_object()
        data_merkle_encrypted = obj2mt(
            data=init_info.get("tree"),
            digest_func=keccak,
            decode_func=lambda s: bytes.fromhex(str(s)),
        )
        contract = Contract(abi=init_info.get("contract_abi"), address=init_info.get("contract_address"))
        web3_contract = environment.get_web3_contract(contract)

        # === PHASE 2: accept ===
        if web3_contract.functions.fileRoot().call() == self.expected_plain_digest:
            self.logger.debug("confirming plain file hash")
        else:
            self.logger.debug("wrong plain file hash")
            return

        if web3_contract.functions.ciphertextRoot().call() == data_merkle_encrypted.digest:
            self.logger.debug("confirming ciphertext hash")
        else:
            self.logger.debug("wrong ciphertext hash")
            return

        tx_receipt = environment.send_contract_transaction(
            contract, "accept", value=self.protocol.price, gas_limit=50000
        )
        self.logger.debug("Sent 'accept' transaction (%s Gas used)" % tx_receipt["gasUsed"])

        # === PHASE 3: wait for key revelation ===
        self.logger.debug("waiting for key revelation")
        result = environment.wait(
            timeout=web3_contract.functions.timeout().call() + 1,
            condition=lambda: web3_contract.functions.key().call() != B032,
        )
        if result == EnvironmentWaitResult.TIMEOUT:
            self.logger.debug("timeout reached, requesting refund")
            environment.send_contract_transaction(contract, "refund")
            return

        data_key = web3_contract.functions.key().call()
        self.logger.debug("key revealed")

        # === PHASE 4: complain ===
        if (
            crypt(data_merkle_encrypted.leaves[-2].data, 2 * self.protocol.slice_count - 2, data_key)
            != self.expected_plain_digest
        ):
            environment.send_contract_transaction(
                contract,
                "complainAboutRoot",
                data_merkle_encrypted.leaves[-2].digest,
                data_merkle_encrypted.get_proof(data_merkle_encrypted.leaves[-2]),
            )
            return
        else:
            data_merkle, errors = decode(data_merkle_encrypted, data_key)
            if len(errors) == 0:
                if self.protocol.send_buyer_confirmation:
                    environment.send_contract_transaction(contract, "noComplain")
                else:
                    self.logger.debug("file successfully decrypted, quitting.")
                    # not calling `noComplain` here, no benefit for buyer (rational party)
                return
            elif isinstance(errors[-1], LeafDigestMismatchError):
                error: NodeDigestMismatchError = errors[-1]
                environment.send_contract_transaction(
                    contract,
                    "complainAboutLeaf",
                    error.index_out,
                    error.index_in,
                    error.out.digest,
                    error.in1.data_as_list(),
                    error.in2.data_as_list(),
                    data_merkle_encrypted.get_proof(error.out),
                    data_merkle_encrypted.get_proof(error.in1),
                )
                return
            else:
                error = errors[-1]
                environment.send_contract_transaction(
                    contract,
                    "complainAboutNode",
                    error.index_out,
                    error.index_in,
                    error.out.digest,
                    error.in1.digest,
                    error.in2.digest,
                    data_merkle_encrypted.get_proof(error.out),
                    data_merkle_encrypted.get_proof(error.in1),
                )
                return


class GrievingBuyer(FairswapBuyer):
    def run(
        self,
        environment: Environment,
        p2p_stream: JsonObjectSocketStream,
        opposite_address: ChecksumAddress,
    ) -> None:
        self.logger.debug("do(ing) nothing, successfully.")  # see `man true`
        return
