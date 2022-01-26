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
    enum Phase {CONFIRMED_IDLE, ACCEPTED, KEY_REVEALED, COMPLAINT_SUCCESSFUL}

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
    mapping (bytes32 => bool) public complaintSuccessful;

    /**
     * @notice ValidTransition checks if there was a valid transition between two states.
     * @param params The parameters of the channel.
     * @param currentState The current state.
     * @param nextState The potential next state.
     * @param signerIdx Index of the participant who signed this transition.
     */
    function validTransition(
        Channel.Params calldata params,
        Channel.State calldata currentState,
        Channel.State calldata nextState,
        uint256 signerIdx)
    external pure override {
        (AppState memory currentFileSaleState) = abi.decode(currentState.appData, (AppState));
        (AppState memory nextFileSaleState) = abi.decode(nextState.appData, (AppState));
        if (currentFileSaleState.phase == Phase.ACCEPTED && nextFileSaleState.phase == Phase.KEY_REVEALED) {
            require(currentFileSaleState.fileRoot == nextFileSaleState.fileRoot, "fileRoot mismatch");
            require(currentFileSaleState.ciphertextRoot == nextFileSaleState.ciphertextRoot, "ciphertextRoot mismatch");
            require(currentFileSaleState.keyCommit == nextFileSaleState.keyCommit, "keyCommit mismatch");
            require(keccak256(abi.encode(nextFileSaleState.key)) == nextFileSaleState.keyCommit, "key hash mismatch");
            require(currentFileSaleState.price == nextFileSaleState.price, "price mismatch");
            require(currentState.outcome.balances[0][1] >= currentFileSaleState.price, "not enough funds for buyer");
            // transfer money from seller to buyer
            require(currentState.outcome.balances[0][0] == nextState.outcome.balances[0][0] + nextFileSaleState.price, "seller balance diff mismatch");
            require(currentState.outcome.balances[0][1] == nextState.outcome.balances[0][1] - nextFileSaleState.price, "buyer balance diff mismatch");
        }
        else if (currentFileSaleState.phase == Phase.KEY_REVEALED && nextFileSaleState.phase == Phase.COMPLAINT_SUCCESSFUL) {
            // TODO ensure complaint was successful
            // transfer back money from buyer to seller
            require(currentState.outcome.balances[0][0] == nextState.outcome.balances[0][0] - nextFileSaleState.price, "seller balance diff mismatch");
            require(currentState.outcome.balances[0][1] == nextState.outcome.balances[0][1] + nextFileSaleState.price, "buyer balance diff mismatch");
        }
        else {
            revert("not a valid transition");
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
        complaintSuccessful[channelID(params)] = true;
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
        complaintSuccessful[channelID(params)] = true;
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
        complaintSuccessful[channelID(params)] = true;
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
