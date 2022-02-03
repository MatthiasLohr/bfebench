# This file is part of the Blockchain-based Fair Exchange Benchmark Tool
#    https://gitlab.com/MatthiasLohr/bfebench
#
# Copyright 2021-2022 Matthias Lohr <mail@mlohr.com>
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

import argparse
import logging
from unittest import TestCase

from bfebench.cli.run import RunCommand

logger = logging.getLogger(__name__)


class CliRunTest(TestCase):
    TEST_PROTOCOLS = {
        "Fairswap": {
            "strategy_pairs": [
                ("Faithful", "Faithful"),
                ("Faithful", "Grieving"),
                ("RootForging", "Faithful"),
            ],
            "protocol_parameters": [("timeout", 10)],
        },
        "StateChannelFileSale": {
            "strategy_pairs": [
                ("Faithful", "Faithful"),
                ("Grieving", "Faithful"),
                ("KeyForging", "Faithful"),
                ("RootForging", "Faithful"),
                ("NodeForging", "Faithful"),
                ("LeafForging", "Faithful"),
            ],
            "protocol_parameters": [("timeout", 10)],
        },
    }

    TEST_FILE_NAME = "testdata/bfebench-test-8KiB.bin"

    def test_cli_run(self) -> None:
        argument_parser = argparse.ArgumentParser()
        run_command = RunCommand(argument_parser)

        for protocol_name, configuration in self.TEST_PROTOCOLS.items():
            strategy_pairs = configuration["strategy_pairs"]

            for seller_strategy_name, buyer_strategy_name in strategy_pairs:  # type: ignore

                logger.debug(
                    "Starting simulation of protocol %s with %s seller and %s buyer"
                    % (protocol_name, seller_strategy_name, buyer_strategy_name)
                )

                result_code = run_command(
                    argparse.Namespace(
                        protocol=protocol_name,
                        protocol_parameters=[("timeout", 5)],
                        seller_strategy=seller_strategy_name,
                        buyer_strategy=buyer_strategy_name,
                        filename=self.TEST_FILE_NAME,
                        price=1000000000,
                        iterations=2,
                        environments_configuration=".environments.yaml",
                        output_csv=None,
                    )
                )

                self.assertEqual(result_code, 0)
