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
    enum Phase {IDLE, INITIALIZED, ACCEPTED, KEY_REVEALED}

    struct AppState {
        bytes32 fileRoot;
        bytes32 ciphertextRoot;
        bytes32 keyCommit;
        bytes32 key;
        uint price;
        Phase phase;
    }

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
    }
}
