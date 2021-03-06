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

from argparse import ArgumentParser, Namespace

from bfebench.protocols import PROTOCOL_SPECIFICATIONS

from .command import SubCommand


class ListStrategiesCommand(SubCommand):
    def __init__(self, argument_parser: ArgumentParser) -> None:
        super().__init__(argument_parser)

        argument_parser.add_argument("protocol", choices=PROTOCOL_SPECIFICATIONS.keys())

    def __call__(self, args: Namespace) -> int:
        protocol_specification = PROTOCOL_SPECIFICATIONS.get(args.protocol)
        if protocol_specification is None:
            raise RuntimeError("cannot load protocol specification")

        roles = (
            ("Seller", protocol_specification.seller_strategies.keys()),
            ("Buyer", protocol_specification.buyer_strategies.keys()),
        )

        for role, strategies in roles:
            print("Strategies for %s:" % role)
            for strategy in strategies:
                print("  * %s" % strategy)

        return 0
