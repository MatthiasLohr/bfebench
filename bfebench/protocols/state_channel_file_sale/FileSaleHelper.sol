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

import "./perun-eth-contracts/contracts/Channel.sol";

contract FileSaleHelper {
    // https://github.com/hyperledger-labs/perun-eth-contracts/blob/abd762dc7d3271f797e304d8bb641f71f8c5c206/contracts/AssetHolder.sol#L208-L216
    function getFundingID(bytes32 channelID, address participant) public pure returns (bytes32) {
        return keccak256(abi.encode(channelID, participant));
    }

    function encodeChannelParams(Channel.Params memory params) public pure returns (bytes memory) {
        return abi.encode(params);
    }

    function encodeChannelState(Channel.State memory state) public pure returns (bytes memory) {
        return abi.encode(state);
    }
}
