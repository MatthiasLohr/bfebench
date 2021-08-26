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

import inspect
from importlib import import_module
from pkgutil import iter_modules
from typing import Dict, Type, TypeVar

from bfebench import protocols
from bfebench.strategy import Strategy
from .common import Protocol


T = TypeVar('T', bound=Type[Strategy])


def get_protocols() -> Dict[str, Type[Protocol]]:
    result = {}

    for module_info in iter_modules(protocols.__path__):  # type: ignore
        if not module_info.ispkg:
            continue
        module = import_module('%s.%s' % (protocols.__name__, module_info.name))
        for cls_name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, Protocol) and hasattr(cls, 'name') and getattr(cls, 'name') is not None:
                result.update({getattr(cls, 'name'): cls})

    return result
