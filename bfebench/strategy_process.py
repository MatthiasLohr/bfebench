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
from multiprocessing import Process
from resource import getrusage, RUSAGE_SELF

from .environment import Environment
from .strategy import Strategy
from .utils.json_stream import JsonObjectSocketStream


logger = logging.getLogger(__name__)


class StrategyProcess(Process):
    def __init__(self, strategy: Strategy, environment: Environment, p2p_stream: JsonObjectSocketStream) -> None:
        super().__init__()
        self._environment = environment
        self._strategy = strategy
        self._p2p_stream = p2p_stream

    def run(self) -> None:
        resources_start = getrusage(RUSAGE_SELF)
        self._strategy.run(self._environment, self._p2p_stream)
        resources_end = getrusage(RUSAGE_SELF)

        # TODO proper resource counting
        print(resources_start)
        print(resources_end)
