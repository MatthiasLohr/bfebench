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

import argparse

from . import data_providers
from . import environments
from . import protocols
from .utils.loader import get_named_subclasses


def main() -> int:
    data_providers_available = get_named_subclasses(data_providers, data_providers.DataProvider)
    environments_available = get_named_subclasses(environments, environments.Environment)
    protocols_available = get_named_subclasses(protocols, protocols.Protocol)

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('environment', choices=environments_available.keys())
    argument_parser.add_argument('protocol', choices=protocols_available.keys())
    argument_parser.add_argument('--data-provider', choices=data_providers_available.keys(),
                                 default=data_providers.RandomDataProvider.name)
    args = argument_parser.parse_args()

    print('Hello world!')

    return 0
