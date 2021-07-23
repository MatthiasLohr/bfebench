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
from typing import Any, Dict, List, Optional, Type, TypeVar

from .errors import BaseError


class Component(object):
    def __init__(self, **kwargs: Any) -> None:
        if len(kwargs) > 0:
            raise BaseError('Component %s does not accept the following parameters: %s' % (
                self.__class__.__name__,
                ', '.join(kwargs.keys())
            ))


T = TypeVar('T', bound=Component)


def get_component_subclasses(package: ModuleType, base_cls: Type[T]) -> Dict[str, Type[T]]:
    subclasses = {}

    for module_info in pkgutil.iter_modules(package.__path__):  # type: ignore
        module = importlib.import_module('%s.%s' % (package.__name__, module_info.name))
        for cls_name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, base_cls) and hasattr(cls, 'name') and getattr(cls, 'name') is not None:
                subclasses.update({getattr(cls, 'name'): cls})

    return subclasses


def init_component_subclass(cls: Optional[Type[T]], parameters: List[List[str]]) -> T:
    if cls is None:
        raise BaseError('Class not found!')

    args: Dict[str, str] = {}

    for key, value in parameters:
        args.update({key: value})

    return cls(**args)
