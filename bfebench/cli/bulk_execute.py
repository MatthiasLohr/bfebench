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

import itertools
import logging
from argparse import ArgumentParser, Namespace

import yaml

from ..environments_configuration import EnvironmentsConfiguration
from ..protocols import PROTOCOL_SPECIFICATIONS
from ..simulation import Simulation
from ..simulation_result_collector import SimulationResultCollector
from .command import SubCommand

logger = logging.getLogger(__name__)


class BulkExecuteCommand(SubCommand):
    def __init__(self, argument_parser: ArgumentParser) -> None:
        super().__init__(argument_parser)

        argument_parser.add_argument(
            "-c",
            "--bulk-config",
            help="YAML file containing bulk execution configuration",
            default="default-bulk-config.yaml",
        )
        argument_parser.add_argument(
            "--target-iterations",
            help="number of desired iterations in total",
            type=int,
            default=1000,
        )
        argument_parser.add_argument(
            "--data-filename-template", default="testdata/bfebench-test-%s.bin"
        )
        argument_parser.add_argument(
            "--price",
            type=int,
            default=1000000000,
            help="price to be paid for the file",
        )
        argument_parser.add_argument(
            "-e", "--environments-configuration", default=".environments.yaml"
        )

    def __call__(self, args: Namespace) -> int:
        with open(args.bulk_config, "r") as fp:
            bulk_config = yaml.safe_load(fp)

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

        for protocol_config, size in itertools.product(
            bulk_config.get("protocols"), bulk_config.get("sizes")
        ):
            protocol_name = protocol_config.get("name")

            data_filename = args.data_filename_template % size

            protocol_specification = PROTOCOL_SPECIFICATIONS.get(protocol_name)

            if protocol_specification is None:
                raise RuntimeError("cannot load protocol specification")

            for seller_strategy_name, buyer_strategy_name in itertools.product(
                protocol_specification.seller_strategies.keys(),
                protocol_specification.buyer_strategies.keys(),
            ):
                logger.info(
                    f"simulating {protocol_name} (seller: {seller_strategy_name}, buyer: {buyer_strategy_name})"
                    f" size {size}..."
                )

                csv_filename = "bfebench-{protocol}-{seller_strategy}-{buyer_strategy}-{size}.csv".format(
                    protocol=protocol_name,
                    seller_strategy=seller_strategy_name,
                    buyer_strategy=buyer_strategy_name,
                    size=size,
                )

                try:
                    with open(csv_filename, "r") as f:
                        lines = f.readlines()
                        existing_results = (
                            len([line for line in lines if line.strip(" \n") != ""]) - 1
                        )
                except FileNotFoundError:
                    existing_results = 0

                if existing_results >= args.target_iterations:
                    continue

                protocol = protocol_specification.protocol(
                    filename=data_filename,
                    price=args.price,
                    **{
                        str(key).replace("-", "_"): value
                        for key, value in protocol_config.get("parameters", {}).items()
                    },
                )

                seller_strategy_cls = protocol_specification.seller_strategies.get(
                    seller_strategy_name
                )
                if seller_strategy_cls is None:
                    raise RuntimeError()

                buyer_strategy_cls = protocol_specification.buyer_strategies.get(
                    buyer_strategy_name
                )
                if buyer_strategy_cls is None:
                    raise RuntimeError()

                seller_strategy = seller_strategy_cls(protocol=protocol)

                buyer_strategy = buyer_strategy_cls(protocol=protocol)

                result_collector = SimulationResultCollector(csv_file=csv_filename)

                simulation = Simulation(
                    environments_configuration=environments_configuration,
                    protocol=protocol,
                    seller_strategy=seller_strategy,
                    buyer_strategy=buyer_strategy,
                    iterations=args.target_iterations - existing_results,
                    result_collector=result_collector,
                )
                simulation.run()

        return 0
