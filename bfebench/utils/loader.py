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

import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import Any, Dict, Type


def get_named_subclasses(package: ModuleType, base_cls: Type[Any]) -> Dict[str, Type[Any]]:
    subclasses = {}

    for module_info in pkgutil.iter_modules(package.__path__):  # type: ignore
        module = importlib.import_module('%s.%s' % (package.__name__, module_info.name))
        for cls_name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, base_cls) and hasattr(cls, 'name') and getattr(cls, 'name') is not None:
                subclasses.update({getattr(cls, 'name'): cls})

    return subclasses
