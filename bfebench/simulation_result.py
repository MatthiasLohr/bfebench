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

from statistics import stdev
from typing import Any, List, NamedTuple

from tabulate import tabulate

from .strategy_process import StrategyProcessResult
from .utils.json_stream import JsonObjectSocketStreamForwarderStats


class IterationResult(NamedTuple):
    seller_result: StrategyProcessResult
    buyer_result: StrategyProcessResult
    p2p_result: JsonObjectSocketStreamForwarderStats


class SimulationResult(object):
    def __init__(self) -> None:
        self._iteration_results: List[IterationResult] = []

    def add_iteration_result(self, iteration_result: IterationResult) -> None:
        self._iteration_results.append(iteration_result)

    @staticmethod
    def get_headers() -> List[str]:
        return [
            'S real',  # seller real time
            'B real',  # buyer real time
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
            'S Tx Fees (Gas)',  # seller blockchain transaction fees
            'B Tx Fees (Gas)',  # buyer blockchain transaction fees
            'S Funds Diff (Eth)',  # seller funds diff (Eth)
            'B Funds Diff (Eth)',  # buyer funds diff (Eth)
        ]

    @staticmethod
    def get_columns(iteration_result: IterationResult) -> List[Any]:
        return [
            iteration_result.seller_result.realtime,
            iteration_result.buyer_result.realtime,
            iteration_result.seller_result.system_resource_stats.utime,
            iteration_result.buyer_result.system_resource_stats.utime,
            iteration_result.seller_result.system_resource_stats.stime,
            iteration_result.buyer_result.system_resource_stats.stime,
            iteration_result.p2p_result.bytes_1to2,
            iteration_result.p2p_result.bytes_2to1,
            iteration_result.p2p_result.count_1to2,
            iteration_result.p2p_result.count_2to1,
            iteration_result.seller_result.environment_stats.tx_count,
            iteration_result.buyer_result.environment_stats.tx_count,
            iteration_result.seller_result.environment_stats.tx_fees,
            iteration_result.buyer_result.environment_stats.tx_fees,
            iteration_result.seller_result.environment_stats.funds_diff,
            iteration_result.buyer_result.environment_stats.funds_diff,
        ]

    def __str__(self) -> str:
        iterations = len(self._iteration_results)

        data_body = [
            [str(i)] + self.get_columns(iteration_result) for i, iteration_result in enumerate(self._iteration_results)
        ]

        data_footer: List[List[Any]] = [[
            'Avg',
            sum([r.seller_result.realtime for r in self._iteration_results]) / iterations,
            sum([r.buyer_result.realtime for r in self._iteration_results]) / iterations,
            sum([r.seller_result.system_resource_stats.utime for r in self._iteration_results]) / iterations,
            sum([r.buyer_result.system_resource_stats.utime for r in self._iteration_results]) / iterations,
            sum([r.seller_result.system_resource_stats.stime for r in self._iteration_results]) / iterations,
            sum([r.buyer_result.system_resource_stats.stime for r in self._iteration_results]) / iterations,
            sum([r.p2p_result.bytes_1to2 for r in self._iteration_results]) / iterations,
            sum([r.p2p_result.bytes_2to1 for r in self._iteration_results]) / iterations,
            sum([r.p2p_result.count_1to2 for r in self._iteration_results]) / iterations,
            sum([r.p2p_result.count_2to1 for r in self._iteration_results]) / iterations,
            sum([r.seller_result.environment_stats.tx_count for r in self._iteration_results]) / iterations,
            sum([r.buyer_result.environment_stats.tx_count for r in self._iteration_results]) / iterations,
            sum([r.seller_result.environment_stats.tx_fees for r in self._iteration_results]) / iterations,
            sum([r.buyer_result.environment_stats.tx_fees for r in self._iteration_results]) / iterations,
            sum([r.seller_result.environment_stats.funds_diff for r in self._iteration_results]) / iterations,
            sum([r.buyer_result.environment_stats.funds_diff for r in self._iteration_results]) / iterations,
        ]] + [[
            'StdDev',
            stdev([r.seller_result.realtime for r in self._iteration_results]),
            stdev([r.buyer_result.realtime for r in self._iteration_results]),
            stdev([r.seller_result.system_resource_stats.utime for r in self._iteration_results]),
            stdev([r.buyer_result.system_resource_stats.utime for r in self._iteration_results]),
            stdev([r.seller_result.system_resource_stats.stime for r in self._iteration_results]),
            stdev([r.buyer_result.system_resource_stats.stime for r in self._iteration_results]),
            stdev([r.p2p_result.bytes_1to2 for r in self._iteration_results]),
            stdev([r.p2p_result.bytes_2to1 for r in self._iteration_results]),
            stdev([r.p2p_result.count_1to2 for r in self._iteration_results]),
            stdev([r.p2p_result.count_2to1 for r in self._iteration_results]),
            stdev([r.seller_result.environment_stats.tx_count for r in self._iteration_results]),
            stdev([r.buyer_result.environment_stats.tx_count for r in self._iteration_results]),
            stdev([r.seller_result.environment_stats.tx_fees for r in self._iteration_results]),
            stdev([r.buyer_result.environment_stats.tx_fees for r in self._iteration_results]),
            stdev([r.seller_result.environment_stats.funds_diff for r in self._iteration_results]),
            stdev([r.buyer_result.environment_stats.funds_diff for r in self._iteration_results]),
            ]
        ]

        return tabulate(
            headers=['#'] + self.get_headers(),
            tabular_data=data_body + data_footer
        )
