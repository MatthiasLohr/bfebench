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

from enum import IntEnum
from typing import Any

from ..fairswap.util import B032


class FileSale(object):
    class AppState(object):
        def __init__(self) -> None:
            self.file_root = B032
            self.ciphertext_root = B032
            self.key_commit = B032
            self.key = B032
            self.price = 0
            self.phase = FileSale.Phase.IDLE

        def __iter__(self) -> Any:
            yield self.file_root
            yield self.ciphertext_root
            yield self.key_commit
            yield self.key
            yield self.price
            yield self.phase.value

    class Phase(IntEnum):
        IDLE = 0
        INITIALIZED = 1
        ACCEPTED = 2
        KEY_REVEALED = 3
