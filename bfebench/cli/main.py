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
import sys

from bfebench.errors import BaseError

from .bulk_execute import BulkExecuteCommand
from .command import SubCommandManager
from .list_protocols import ListProtocolsCommand
from .list_strategies import ListStrategiesCommand
from .run import RunCommand

logger = logging.getLogger(__name__)


def main() -> None:
    scm = SubCommandManager()

    scm.add_sub_command("bulk-execute", BulkExecuteCommand)
    scm.add_sub_command("run", RunCommand)
    scm.add_sub_command("list-protocols", ListProtocolsCommand)
    scm.add_sub_command("list-strategies", ListStrategiesCommand)

    try:
        exit_code = scm.run()
    except BaseError as e:
        logger.error("A general error occurred.", exc_info=e)
        exit_code = 1

    sys.exit(exit_code)
