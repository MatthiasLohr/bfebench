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

from __future__ import annotations

import logging
from argparse import ArgumentParser, Namespace
from typing import Dict, Type

import bfebench


class SubCommand(object):
    help: str | None = None

    def __init__(self, argument_parser: ArgumentParser) -> None:
        pass

    def __call__(self, args: Namespace) -> int:
        raise NotImplementedError()


class SubCommandManager(object):
    def __init__(self) -> None:
        self._argument_parser = ArgumentParser()
        self._argument_parser.add_argument(
            "-l",
            "--log-level",
            default="WARNING",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        )
        self._sub_command_sub_parser = self._argument_parser.add_subparsers(
            title="command", dest="command", required=True
        )
        self._sub_commands: Dict[str, SubCommand] = {}

    def add_sub_command(self, command_name: str, command_cls: Type[SubCommand]) -> None:
        self._sub_commands[command_name] = command_cls(self._sub_command_sub_parser.add_parser(command_name))

    def run(self) -> int:
        args = self._argument_parser.parse_args()

        root_logger = logging.getLogger(bfebench.__name__)
        root_logger.setLevel(logging.getLevelName(args.log_level))

        sub_command = self._sub_commands.get(args.command)
        if sub_command is None:
            raise RuntimeError("sub_command should not be None here")
        return sub_command(args)
