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

// SPDX-License-Identifier: Apache-2.0

pragma solidity ^0.7.0;
pragma experimental ABIEncoderV2;

import "../../bfebench/protocols/state_channel_fairswap/perun-eth-contracts/contracts/Channel.sol";

contract PerunTest {
    // custom test function for testing the test case
    function getRandomNumber() public returns (int) {
        return 4;
    }

    // functions taken from perun-eth-contracts/contracts/Adjudicator.sol for testing
    /**
     * @notice Calculates the channel's ID from the given parameters.
     * @param params The parameters of the channel.
     * @return The ID of the channel.
     */
    function channelID(Channel.Params memory params) public pure returns (bytes32) {
        return keccak256(Channel.encodeParams(params));
    }

    /**
     * @notice Calculates the hash of a state.
     * @param state The state to hash.
     * @return The hash of the state.
     */
    function hashState(Channel.State memory state) public pure returns (bytes32) {
        return keccak256(Channel.encodeState(state));
    }

    // functions taken from perun-eth-contracts/contracts/AssetHolder.sol for testing
    /**
     * @notice Internal helper function that calculates the fundingID.
     * @param channelID ID of the channel.
     * @param participant Address of a participant in the channel.
     * @return The funding ID, an identifier used for indexing.
     */
    function calcFundingID(bytes32 channelID, address participant) public pure returns (bytes32) {
        return keccak256(abi.encode(channelID, participant));
    }

    // functions taken from perun-eth-contracts/contracts/Channel.sol for testing
    function encodeParams(Channel.Params memory params) public pure returns (bytes memory)  {
        return abi.encode(params);
    }

    function encodeState(Channel.State memory state) public pure returns (bytes memory)  {
        return abi.encode(state);
    }

    function verifySignature(bytes memory data, bytes memory signature, address signer) public pure returns (bool) {
        return Sig.verify(data, signature, signer);
    }
}
