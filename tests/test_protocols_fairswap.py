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
from typing import Tuple
from unittest import TestCase

from eth_tester import EthereumTester, PyEVMBackend  # type: ignore
from web3 import Web3
from web3.contract import Contract
from web3.providers.eth_tester.main import EthereumTesterProvider

from bfebench.const import DEFAULT_PRICE, DEFAULT_TIMEOUT
from bfebench.contract import SolidityContractSourceCodeManager
from bfebench.protocols.fairswap import Fairswap
from bfebench.protocols.fairswap.util import (
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
from bfebench.utils.bytes import generate_bytes
from bfebench.utils.merkle import from_bytes, mt2obj, obj2mt


class EncodingTest(TestCase):
    def test_encode_decode(self) -> None:
        key = generate_bytes(32)
        for size, slice_count in [(128, 4), (1024, 16)]:
            data = generate_bytes(size)
            tree = from_bytes(data, keccak, slice_count)
            tree_enc = encode(tree, key)

            tree_enc_obj = mt2obj(tree_enc, encode_func=lambda b: bytes(b).hex())
            tree_enc_obj2mt = obj2mt(
                tree_enc_obj,
                digest_func=keccak,
                decode_func=lambda s: bytes.fromhex(str(s)),
            )

            self.assertEqual(tree_enc.leaves, tree_enc_obj2mt.leaves)
            self.assertEqual(tree_enc.digest, tree_enc_obj2mt.digest)

            tree_dec, errors = decode(tree_enc, key)
            self.assertEqual([], errors)
            self.assertEqual(tree, tree_dec)
            self.assertEqual(tree.digest, tree_dec.digest)

    def test_encode_forge_first_leaf(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), keccak, 4)
        tree_enc = encode_forge_first_leaf(tree, B032)
        tree_dec, errors = decode(tree_enc, B032)
        self.assertEqual(1, len(errors))
        self.assertEqual(LeafDigestMismatchError, type(errors[0]))

    def test_encode_forge_first_leaf_first_hash(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), keccak, 4)
        tree_enc = encode_forge_first_leaf_first_hash(tree, B032)
        tree_dec, errors = decode(tree_enc, B032)
        self.assertEqual(1, len(errors))
        self.assertEqual(NodeDigestMismatchError, type(errors[0]))


class ContractTest(TestCase):
    @staticmethod
    def prepare_contract(
        file_root_hash: bytes,
        ciphertext_root_hash: bytes,
        key_hash: bytes,
        slice_count: int = 4,
    ) -> Tuple[Web3, Contract]:
        web3 = Web3(EthereumTesterProvider(EthereumTester(PyEVMBackend())))

        scscm = SolidityContractSourceCodeManager()
        scscm.add_contract_template_file(
            os.path.join(
                os.path.dirname(__file__),
                "../bfebench/protocols/fairswap",
                Fairswap.CONTRACT_TEMPLATE_FILE,
            ),
            {
                "merkle_tree_depth": log2(slice_count) + 1,
                "slice_length": 32,
                "slice_count": slice_count,
                "receiver": Web3.toChecksumAddress(
                    "0xc1912fee45d61c87cc5ea59dae31190fffff232d"
                ),
                "price": DEFAULT_PRICE,
                "key_commitment": "0x" + key_hash.hex(),
                "ciphertext_root_hash": "0x" + ciphertext_root_hash.hex(),
                "file_root_hash": "0x" + file_root_hash.hex(),
                "timeout": DEFAULT_TIMEOUT,
            },
        )
        contracts = scscm.compile(Fairswap.CONTRACT_SOLC_VERSION)
        contract = contracts[Fairswap.CONTRACT_NAME]
        contract_preparation = web3.eth.contract(
            abi=contract.abi, bytecode=contract.bytecode
        )
        tx_hash = contract_preparation.constructor().transact()
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt is None:
            raise RuntimeError("should not be None at this point")
        return web3, web3.eth.contract(
            address=tx_receipt["contractAddress"], abi=contract.abi
        )

    def test_vrfy(self) -> None:
        tree = from_bytes(generate_bytes(128, seed=42), keccak, 4)
        key = generate_bytes(32, seed=43)
        tree_enc = encode(tree, key)
        web3, contract = self.prepare_contract(tree.digest, tree_enc.digest, B032)

        for index, leaf in enumerate(tree_enc.leaves):
            proof = tree_enc.get_proof(leaf)
            self.assertEqual(len(proof), 3)
            call_result = contract.functions.vrfy(index, leaf.digest, proof).call()
            self.assertTrue(call_result)

    def test_crypt_small(self) -> None:
        for n in [4, 8, 16]:
            web3, contract = self.prepare_contract(
                generate_bytes(32), generate_bytes(32), B032, n
            )
            for i in range(8):
                data = generate_bytes(32)
                call_result = contract.functions.cryptSmall(i, data).call()
                self.assertEqual(call_result, crypt(data, i, B032))
