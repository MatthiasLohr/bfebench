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
import time
from multiprocessing import Process, Queue
from resource import getrusage, RUSAGE_SELF
from typing import NamedTuple, Optional

from .environment import Environment
from .strategy import Strategy
from .utils.json_stream import JsonObjectSocketStream


logger = logging.getLogger(__name__)


class ResourceUsage(NamedTuple):
    """
    https://man7.org/linux/man-pages/man2/getrusage.2.html
    """

    """real time"""
    realtime: float = 0.0

    """user CPU time used"""
    utime: float = 0.0

    """system CPU time used"""
    stime: float = 0.0

    """maximum resident set size"""
    maxrss: int = 0

    """integral shared memory size"""
    ixrss: int = 0

    """integral unshared data size"""
    idrss: int = 0

    """integral unshared stack size"""
    isrss: int = 0

    """page reclaims (soft page faults)"""
    minflt: int = 0

    """page faults (hard page faults)"""
    majflt: int = 0

    """swaps"""
    nswap: int = 0

    """block input operations"""
    inblock: int = 0

    """block output operations"""
    oublock: int = 0

    """IPC messages sent"""
    msgsnd: int = 0

    """IPC messages received"""
    msgrcv: int = 0

    """signals received"""
    nsignals: int = 0

    """voluntary context switches"""
    nvcsw: int = 0

    """involuntary context switches"""
    nivcsw: int = 0


class StrategyProcess(Process):
    def __init__(self, strategy: Strategy, environment: Environment, p2p_stream: JsonObjectSocketStream) -> None:
        super().__init__()
        self._environment = environment
        self._strategy = strategy
        self._p2p_stream = p2p_stream
        self._resource_usage: Optional[ResourceUsage] = None
        self._result_queue: Queue[ResourceUsage] = Queue()

    def run(self) -> None:
        time_start = time.time()
        resources_start = getrusage(RUSAGE_SELF)
        self._strategy.run(self._environment, self._p2p_stream)
        resources_end = getrusage(RUSAGE_SELF)
        time_end = time.time()

        self._result_queue.put(ResourceUsage(
            realtime=time_end - time_start,
            utime=resources_end.ru_utime - resources_start.ru_utime,
            stime=resources_end.ru_stime - resources_start.ru_stime,
            maxrss=resources_end.ru_maxrss - resources_start.ru_maxrss,
            ixrss=resources_end.ru_ixrss - resources_start.ru_ixrss,
            idrss=resources_end.ru_idrss - resources_start.ru_idrss,
            isrss=resources_end.ru_isrss - resources_start.ru_isrss,
            minflt=resources_end.ru_minflt - resources_start.ru_minflt,
            majflt=resources_end.ru_majflt - resources_start.ru_majflt,
            nswap=resources_end.ru_nswap - resources_start.ru_nswap,
            inblock=resources_end.ru_inblock - resources_start.ru_inblock,
            oublock=resources_end.ru_oublock - resources_start.ru_oublock,
            msgsnd=resources_end.ru_msgsnd - resources_start.ru_msgsnd,
            msgrcv=resources_end.ru_msgrcv - resources_start.ru_msgrcv,
            nsignals=resources_end.ru_nsignals - resources_start.ru_nsignals,
            nvcsw=resources_end.ru_nvcsw - resources_start.ru_nvcsw,
            nivcsw=resources_end.ru_nivcsw - resources_start.ru_nivcsw
        ))

    def get_resource_usage(self) -> ResourceUsage:
        if self._resource_usage is None:
            self._resource_usage = self._result_queue.get(block=True)
        return self._resource_usage
