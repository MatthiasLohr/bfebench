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
    enum Phase {IDLE, INITIALIZED, ACCEPTED, REVEALED}

    struct AppState {
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
        require(from.version == 1 && to.version == 1, "only version==1 is supported");
        // TODO implement
    }
}
