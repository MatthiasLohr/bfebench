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

from multiprocessing import Process
from time import sleep
from typing import Any, Dict, Generator

from .environments import Environment
from .strategy import Strategy


class AffiliateProcess(Process):
    def __init__(self, environment: Environment, strategy: Strategy,
                 direct_messages: Generator[Dict[str, Any], None, None]):
        super().__init__()
        self._environment = environment

    @property
    def environment(self) -> Environment:
        return self._environment

    def run(self) -> None:
        while True:
            print(self._environment.web3.eth.get_balance('0x77A2E07b4A3d54dB31f5E88475C3864A19163668'))
            sleep(1)
