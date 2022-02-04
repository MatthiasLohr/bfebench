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

from . import errors, protocols

__all__ = ["errors", "protocols"]


# https://docs.python.org/3/library/logging.html#logrecord-attributes
logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler(sys.stderr)
log_formatter = logging.Formatter(fmt="%(asctime)s %(name)-44s [%(levelname)s] %(message)s")
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
