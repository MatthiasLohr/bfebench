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
import os
from math import log2
from typing import Any

from ..protocol import Protocol
from ...errors import ProtocolInitializationError


DEFAULT_SLICE_COUNT = 4
DEFAULT_TIMEOUT = 60  # 60 seconds

logger = logging.getLogger(__name__)


class Fairswap(Protocol):
    CONTRACT_NAME = 'FileSale'
    CONTRACT_TEMPLATE_FILE = 'fairswap.tpl.sol'

    def __init__(self, slice_count: int = DEFAULT_SLICE_COUNT, timeout: int = DEFAULT_TIMEOUT, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        slice_count = int(slice_count)

        if not log2(slice_count).is_integer():
            raise ProtocolInitializationError('slice_count must be a power of 2')

        self._slice_count = slice_count
        self._timeout = int(timeout)

        file_size = os.path.getsize(self.filename)
        if ((file_size / slice_count) % 32) > 0:
            raise ProtocolInitializationError('file size must be a multiple of 32 bytes * %d slices' % slice_count)

        self._slice_length = int(file_size / slice_count)

        logger.debug('initialized Fairswap with slice_count=%d slice_length=%d timeout=%d' % (
            self.slice_count,
            self.slice_length,
            self.timeout,
        ))

    @property
    def slice_count(self) -> int:
        return self._slice_count

    @property
    def slice_length(self) -> int:
        return self._slice_length

    @property
    def timeout(self) -> int:
        return self._timeout
