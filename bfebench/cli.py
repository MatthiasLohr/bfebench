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
import logging

from . import data_providers
from . import environments
from . import protocols
from .simulation import Simulation
from .component import get_component_subclasses, init_component_subclass

logger = logging.getLogger()


def main() -> int:
    data_providers_available = get_component_subclasses(data_providers, data_providers.DataProvider)
    environments_available = get_component_subclasses(environments, environments.Environment)
    protocols_available = get_component_subclasses(protocols, protocols.Protocol)

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('environment', choices=environments_available.keys())
    argument_parser.add_argument('-e', '--environment-parameter', nargs=2, action='append', metavar=('KEY', 'VALUE'),
                                 dest='environment_parameters', default=[],
                                 help='pass additional parameters to the environment')
    argument_parser.add_argument('protocol', choices=protocols_available.keys())
    argument_parser.add_argument('-p', '--protocol-parameter', nargs=2, action='append', dest='protocol_parameters',
                                 default=[], metavar=('KEY', 'VALUE'),
                                 help='pass additional parameters to the protocol')
    argument_parser.add_argument('--data-provider', choices=data_providers_available.keys(),
                                 default=data_providers.RandomDataProvider.name)
    argument_parser.add_argument('-d', '--data-provider-parameter', nargs=2, action='append', metavar=('KEY', 'VALUE'),
                                 dest='data_provider_parameters', default=[],
                                 help='pass additional parameters to the data provider')

    args = argument_parser.parse_args()

    environment = init_component_subclass(
        environments_available.get(args.environment),
        args.environment_parameters
    )

    protocol = init_component_subclass(
        protocols_available.get(args.protocol),
        args.protocol_parameters
    )

    data_provider = init_component_subclass(
        data_providers_available.get(args.data_provider),
        args.data_provider_parameters
    )

    simulation = Simulation(environment, protocol, data_provider)
    simulation_result = simulation.run()

    print(simulation_result)

    return 0
