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

from typing import List, NamedTuple

from tabulate import tabulate

from .strategy_process import ResourceUsage


class IterationResult(NamedTuple):
    seller_resource_usage: ResourceUsage
    buyer_resource_usage: ResourceUsage
    seller2buyer_direct_bytes: int
    buyer2seller_direct_bytes: int
    seller2buyer_direct_objects: int
    buyer2seller_direct_objects: int


class SimulationResult(object):
    def __init__(self) -> None:
        self._iteration_results: List[IterationResult] = []

    def add_iteration_result(self, iteration_result: IterationResult) -> None:
        self._iteration_results.append(iteration_result)

    def __str__(self) -> str:
        iterations = len(self._iteration_results)

        return tabulate(
            tabular_data=[[
                str(i + 1),
                r.seller_resource_usage.utime,
                r.buyer_resource_usage.utime,
                r.seller_resource_usage.stime,
                r.buyer_resource_usage.stime,
                r.seller2buyer_direct_bytes,
                r.buyer2seller_direct_bytes,
                r.seller2buyer_direct_objects,
                r.buyer2seller_direct_objects,
                0,  # TODO add seller blockchain transaction count
                0,  # TODO add buyer blockchain transaction count
                0,  # TODO add seller blockchain transaction fees
                0  # TODO add buyer blockchain transaction fees
            ] for i, r in enumerate(self._iteration_results)] + [[
                'Avg',
                sum([r.seller_resource_usage.utime for r in self._iteration_results]) / iterations,
                sum([r.buyer_resource_usage.utime for r in self._iteration_results]) / iterations,
                sum([r.seller_resource_usage.stime for r in self._iteration_results]) / iterations,
                sum([r.buyer_resource_usage.stime for r in self._iteration_results]) / iterations,
                sum([r.seller2buyer_direct_bytes for r in self._iteration_results]) / iterations,
                sum([r.buyer2seller_direct_bytes for r in self._iteration_results]) / iterations,
                sum([r.seller2buyer_direct_objects for r in self._iteration_results]) / iterations,
                sum([r.buyer2seller_direct_objects for r in self._iteration_results]) / iterations,
                0,  # TODO add seller blockchain transaction count
                0,  # TODO add buyer blockchain transaction count
                0,  # TODO add seller blockchain transaction fees
                0  # TODO add buyer blockchain transaction fees
            ]],
            headers=[
                '#',  # iteration / 'Avg'
                'S user',  # seller user CPU time
                'B user',  # buyer user CPU time
                'S sys',  # seller system CPU time
                'B sys',  # buyer system CPU time
                'S>B bytes',  # bytes directly sent from seller to buyer
                'B>S bytes',  # bytes directly sent from buyer to sender
                'S>B obj',  # objects directly sent from seller to buyer
                'B>S obj',  # objects directly sent from seller to buyer
                'S Tx Ct',  # seller blockchain transaction count
                'B Tx Ct',  # buyer blockchain transaction count
                'S Tx Fees',  # seller blockchain transaction fees
                'B Tx Fees'  # buyer blockchain transaction fees
            ]
        )
