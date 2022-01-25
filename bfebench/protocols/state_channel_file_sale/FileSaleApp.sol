// This file is part of the Blockchain-based Fair Exchange Benchmark Tool
//    https://gitlab.com/MatthiasLohr/bfebench
//
// Copyright 2021 Matthias Lohr <mail@mlohr.com>
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// This contract is based on the FairSwap contract at https://github.com/lEthDev/FairSwap
// Original authors: Stefan Dziembowski, Lisa Eckey, Sebastian Faust

// SPDX-License-Identifier: Apache-2.0

pragma solidity ^0.7.0;
pragma experimental ABIEncoderV2;

import "./perun-eth-contracts/contracts/App.sol";

contract FileSaleApp is App {
    enum Phase {IDLE, INITIALIZED, ACCEPTED, KEY_REVEALED, DISPUTE}

    struct AppState {
        bytes32 fileRoot;
        bytes32 ciphertextRoot;
        bytes32 keyCommit;
        bytes32 key;
        uint price;
        Phase phase;
    }

    /**
     * This mapping channelID => bool stores if a complaint for the channel identified by  its channelID was
     * successful.
     */
    mapping (bytes32 => bool) public complainSuccessful;

    /**
     * @notice ValidTransition checks if there was a valid transition between two states.
     * @param params The parameters of the channel.
     * @param from The current state.
     * @param to The potential next state.
     * @param signerIdx Index of the participant who signed this transition.
     */
    function validTransition(
        Channel.Params calldata params,
        Channel.State calldata from,
        Channel.State calldata to,
        uint256 signerIdx)
    external pure override
    {
        (AppState memory appFrom) = abi.decode(from.appData, (AppState));
        (AppState memory appTo) = abi.decode(to.appData, (AppState));
        if (appTo.phase == Phase.INITIALIZED) {
            // ======== seller initializes new transfer ========
            require(signerIdx == 0, "only seller can initialize");
            require(appFrom.phase == Phase.IDLE, "IDLE -> INITIALIZED violation");
            // TODO check outcome Allocation
        }
        else if (appTo.phase == Phase.ACCEPTED) {
            // ======== buyer accepts transfer ========
            require(signerIdx == 1, "only buyer can accept");
            require(appFrom.phase == Phase.INITIALIZED, "INITIALIZED -> ACCEPTED violation");
            require(appFrom.fileRoot == appTo.fileRoot, "fileRoot mismatch");
            require(appFrom.ciphertextRoot == appTo.ciphertextRoot, "ciphertextRoot mismatch");
            require(appFrom.keyCommit == appTo.keyCommit, "keyCommit mismatch");
            require(appFrom.price == appTo.price, "price mismatch");
            // TODO check outcome Allocation
        }
        else if (appTo.phase == Phase.KEY_REVEALED) {
            // ======== seller reveals key ========
            require(signerIdx == 0, "only seller can reveal key");
            require(appFrom.phase == Phase.ACCEPTED, "ACCEPTED -> KEY_REVEALED violation");
            require(appFrom.fileRoot == appTo.fileRoot, "fileRoot mismatch");
            require(appFrom.ciphertextRoot == appTo.ciphertextRoot, "ciphertextRoot mismatch");
            require(appFrom.keyCommit == appTo.keyCommit, "keyCommit mismatch");
            require(appTo.keyCommit == keccak256(abi.encode(appTo.key)), "key mismatch");
            require(appFrom.price == appTo.price, "price mismatch");
            // TODO check outcome Allocation
        }
        else if (appTo.phase == Phase.IDLE) {
            // ======== buyer confirms ========
            require(signerIdx == 1, "only buyer can confirm");
            require(appFrom.phase == Phase.KEY_REVEALED, "KEY_REVEALED -> IDLE violation");
            // TODO check outcome Allocation
        }
        else if (appTo.phase == Phase.DISPUTE) {
            require(signerIdx == 1, "only buyer can dispute");
            require(appFrom.phase == Phase.KEY_REVEALED, "KEY_REVEALED -> DISPUTE violation");
            require(appFrom.fileRoot == appTo.fileRoot, "fileRoot mismatch");
            require(appFrom.ciphertextRoot == appTo.ciphertextRoot, "ciphertextRoot mismatch");
            require(appFrom.keyCommit == appTo.keyCommit, "keyCommit mismatch");
            require(appTo.keyCommit == keccak256(abi.encode(appTo.key)), "key mismatch");
            require(appFrom.price == appTo.price, "price mismatch");
            // TODO verify complain
            // when dispute is successful, payment should be reverted
            // TODO check outcome Allocation
        }
    }

    /**
     * @notice Calculates the channel's ID from the given parameters.
     * @param params The parameters of the channel.
     * @return The ID of the channel.
     *
     * Source:
     * https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/Adjudicator.sol#L270-L277
     */
    function channelID(Channel.Params memory params) public pure returns (bytes32) {
        return keccak256(Channel.encodeParams(params));
    }

    /**
     * ======== Fairswap Filesale ===
     * by Stefan Dziembowski, Lisa Eckey, Sebastian Faust -- https://github.com/lEthDev/FairSwap
     *
     * Modified by Matthias Lohr
     */

    // function complain about wrong hash of file
    function complainAboutRoot(
        Channel.Params memory params,
        Channel.State memory state,
        bytes memory sellerSignature,
        bytes32 _Zm,
        bytes32[] memory _proofZm
    )
    public
    {
        (AppState memory appState) = abi.decode(state.appData, (AppState));
        // State Channel checks
        // TODO implement
        // Fairswap checks
        require (vrfy((2 << _proofZm.length) - 2, _Zm, _proofZm, appState.ciphertextRoot));
        require (cryptSmall((2 << _proofZm.length) - 2, _Zm, appState.key) != appState.fileRoot);
        // store successful complaint
        complainSuccessful[channelID(params)] = true;
    }

    // function complain about wrong hash of two inputs
    function complainAboutLeaf(
        Channel.Params memory params,
        Channel.State memory state,
        bytes memory sellerSignature,
        uint _indexOut,
        uint _indexIn,
        bytes32 _Zout,
        bytes32[] memory _Zin1,
        bytes32[] memory _Zin2,
        bytes32[] memory _proofZout,
        bytes32[] memory _proofZin
    )
    public
    {
        (AppState memory appState) = abi.decode(state.appData, (AppState));
        // State Channel checks
        // TODO implement
        // Fairswap checks
        require (vrfy(_indexOut, _Zout, _proofZout, appState.ciphertextRoot));
        bytes32 Xout = cryptSmall(_indexOut, _Zout, appState.key);
        require (vrfy(_indexIn, keccak256(abi.encode(_Zin1)), _proofZin, appState.ciphertextRoot));
        require (_proofZin[_proofZin.length - 1] == keccak256(abi.encode(_Zin2)));
        require (Xout != keccak256(abi.encode(cryptLarge(_indexIn, _Zin1, appState.key), cryptLarge(_indexIn + 1, _Zin2, appState.key))));
        // store successful complaint
        complainSuccessful[channelID(params)] = true;
    }

    // function complain about wrong hash of two inputs
    function complainAboutNode(
        Channel.Params memory params,
        Channel.State memory state,
        bytes memory sellerSignature,
        uint _indexOut,
        uint _indexIn,
        bytes32 _Zout,
        bytes32 _Zin1,
        bytes32 _Zin2,
        bytes32[] memory _proofZout,
        bytes32[] memory _proofZin
    )
    public
    {
        (AppState memory appState) = abi.decode(state.appData, (AppState));
        // State Channel checks
        // TODO implement
        // Fairswap checks
        require (vrfy(_indexOut, _Zout, _proofZout, appState.ciphertextRoot));
        bytes32 Xout = cryptSmall(_indexOut, _Zout, appState.key);
        require (vrfy(_indexIn, _Zin1, _proofZin, appState.ciphertextRoot));
        require (_proofZin[_proofZin.length - 1] == _Zin2);
        require (Xout != keccak256(abi.encode(cryptSmall(_indexIn, _Zin1, appState.key), cryptSmall(_indexIn+ 1, _Zin2, appState.key))));
        // store successful complaint
        complainSuccessful[channelID(params)] = true;
    }

    // function to both encrypt and decrypt text chunks with key k
    function cryptLarge(uint _index, bytes32[] memory _ciphertext, bytes32 key) public view returns (bytes32[] memory) {
        _index = _index * _ciphertext.length;
        for (uint i = 0; i < _ciphertext.length; i++){
            _ciphertext[i] = keccak256(abi.encode(_index, key)) ^ _ciphertext[i];
            _index++;
        }
        return _ciphertext;
    }

    // function to decrypt hashes of the merkle tree
    function cryptSmall(uint _index, bytes32 _ciphertext, bytes32 key) public view returns (bytes32) {
        return keccak256(abi.encode(_index, key)) ^ _ciphertext;
    }

    // function to verify Merkle Tree proofs
    function vrfy(uint _index, bytes32 _value, bytes32[] memory _proof, bytes32 ciphertextRoot) public view returns (bool) {
        for (uint i = 0; i < _proof.length; i++) {
            if ((_index & 1 << i) >>i == 1)
                _value = keccak256(abi.encodePacked(_proof[_proof.length - i - 1], _value));
            else
                _value = keccak256(abi.encodePacked(_value, _proof[_proof.length - i - 1]));
        }
        return (_value == ciphertextRoot);
    }
}
