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

import logging
from argparse import ArgumentParser, Namespace

from bfebench.environments_configuration import EnvironmentsConfiguration
from bfebench.protocols import PROTOCOL_SPECIFICATIONS
from bfebench.simulation import Simulation

from ..const import DEFAULT_PRICE
from ..simulation_result_collector import SimulationResultCollector
from .command import SubCommand

logger = logging.getLogger(__name__)


class RunCommand(SubCommand):
    def __init__(self, argument_parser: ArgumentParser) -> None:
        super().__init__(argument_parser)

        argument_parser.add_argument("protocol", choices=PROTOCOL_SPECIFICATIONS.keys())
        argument_parser.add_argument(
            "-p",
            "--protocol-parameter",
            nargs=2,
            action="append",
            dest="protocol_parameters",
            default=[],
            metavar=("KEY", "VALUE"),
            help="pass additional parameters to the protocol",
        )
        argument_parser.add_argument("seller_strategy")
        argument_parser.add_argument("buyer_strategy")
        argument_parser.add_argument("filename", help="file to be exchanged")
        argument_parser.add_argument(
            "--price",
            type=int,
            default=DEFAULT_PRICE,
            help="price to be paid for the file",
        )
        argument_parser.add_argument(
            "-n",
            "--iterations",
            help="Number of exchanges to be simulated",
            type=int,
            default=1,
        )
        argument_parser.add_argument(
            "-e", "--environments-configuration", default=".environments.yaml"
        )
        argument_parser.add_argument(
            "--output-csv", help="write CSV file with results", default=None
        )

    def __call__(self, args: Namespace) -> int:
        protocol_specification = PROTOCOL_SPECIFICATIONS.get(args.protocol)
        if protocol_specification is None:
            raise RuntimeError("cannot load protocol specification")

        try:
            environments_configuration = EnvironmentsConfiguration(
                args.environments_configuration
            )
        except FileNotFoundError as e:
            logger.error(
                "Could not load environments configuration: %s: %s"
                % (e.strerror, e.filename)
            )
            return 1

        protocol = protocol_specification.protocol(
            filename=args.filename,
            price=args.price,
            **{
                str(key).replace("-", "_"): value
                for key, value in args.protocol_parameters
            }
        )

        seller_strategy_cls = protocol_specification.seller_strategies.get(
            args.seller_strategy
        )
        if seller_strategy_cls is None:
            logger.error('could not find a seller strategy "%s"' % args.seller_strategy)
            logger.error(
                "use `bfebench list-strategies %s` to list available strategies"
                % args.protocol
            )
            return 1

        buyer_strategy_cls = protocol_specification.buyer_strategies.get(
            args.buyer_strategy
        )
        if buyer_strategy_cls is None:
            logger.error('could not find a buyer strategy "%s"' % args.buyer_strategy)
            logger.error(
                "use `bfebench list-strategies %s` to list available strategies"
                % args.protocol
            )
            return 1

        seller_strategy = seller_strategy_cls(protocol=protocol)

        buyer_strategy = buyer_strategy_cls(protocol=protocol)

        result_collector = SimulationResultCollector(csv_file=args.output_csv)

        simulation = Simulation(
            environments_configuration=environments_configuration,
            protocol=protocol,
            seller_strategy=seller_strategy,
            buyer_strategy=buyer_strategy,
            iterations=args.iterations,
            result_collector=result_collector,
        )
        simulation.run()

        print(result_collector.get_result())

        return 0
