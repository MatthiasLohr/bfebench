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

import csv
from datetime import datetime

from bfebench.simulation_result import IterationResult, SimulationResult


class SimulationResultCollector(object):
    def __init__(self, csv_file: str | None = None) -> None:
        self._simulation_result = SimulationResult()
        self._csv_file = None
        self._csv_writer = None

        self._simulation_start_date = datetime.now().isoformat()

        if csv_file is not None:
            self._csv_file = open(csv_file, "a")
            self._csv_writer = csv.writer(self._csv_file)
            if self._csv_file.tell() == 0:
                self._csv_writer.writerow(["Start"] + SimulationResult.get_headers())

    def add_iteration_result(self, iteration_result: IterationResult) -> None:
        self._simulation_result.add_iteration_result(iteration_result)

        if self._csv_file is not None and self._csv_writer is not None:
            self._csv_writer.writerow(
                [self._simulation_start_date]
                + SimulationResult.get_columns(iteration_result)
            )

    def get_result(self) -> SimulationResult:
        return self._simulation_result

    def __del__(self) -> None:
        if self._csv_file is not None:
            self._csv_file.close()
            self._csv_writer = None
            self._csv_file = None
