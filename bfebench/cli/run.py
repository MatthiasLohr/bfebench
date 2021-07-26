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
from argparse import ArgumentParser, Namespace

from bfebench import data_providers, environments, protocols
from bfebench.component import get_component_subclasses, init_component_subclass
from bfebench.simulation import Simulation
from .command import SubCommand


logger = logging.getLogger(__name__)


class RunCommand(SubCommand):
    def __init__(self, argument_parser: ArgumentParser) -> None:
        super().__init__(argument_parser)

        self._data_providers_available = get_component_subclasses(data_providers, data_providers.DataProvider)
        self._environments_available = get_component_subclasses(environments, environments.Environment)
        self._protocols_available = get_component_subclasses(protocols, protocols.Protocol)

        argument_parser.add_argument('environment', choices=self._environments_available.keys())
        argument_parser.add_argument('-e', '--environment-parameter', nargs=2, action='append',
                                     metavar=('KEY', 'VALUE'),
                                     dest='environment_parameters', default=[],
                                     help='pass additional parameters to the environment')
        argument_parser.add_argument('protocol', choices=self._protocols_available.keys())
        argument_parser.add_argument('-p', '--protocol-parameter', nargs=2, action='append', dest='protocol_parameters',
                                     default=[], metavar=('KEY', 'VALUE'),
                                     help='pass additional parameters to the protocol')
        argument_parser.add_argument('seller_strategy')
        argument_parser.add_argument('buyer_strategy')
        argument_parser.add_argument('--data-provider', choices=self._data_providers_available.keys(),
                                     default=data_providers.RandomDataProvider.name)
        argument_parser.add_argument('-d', '--data-provider-parameter', nargs=2, action='append',
                                     metavar=('KEY', 'VALUE'),
                                     dest='data_provider_parameters', default=[],
                                     help='pass additional parameters to the data provider')
        argument_parser.add_argument('-n', '--iterations', help='Number of exchanges to be simulated', type=int,
                                     default=1)

    def __call__(self, args: Namespace) -> int:
        environment = init_component_subclass(
            self._environments_available.get(args.environment),
            args.environment_parameters
        )

        protocol = init_component_subclass(
            self._protocols_available.get(args.protocol),
            args.protocol_parameters
        )

        seller_strategy = protocol.get_seller_strategies().get(args.seller_strategy)
        if seller_strategy is None:
            logger.error('could not find a seller strategy "%s"' % args.seller_strategy)
            logger.error('use `bfebench list-strategies %s` to list available strategies' % args.protocol)
            return 1

        buyer_strategy = protocol.get_buyer_strategies().get(args.buyer_strategy)
        if buyer_strategy is None:
            logger.error('could not find a buyer strategy "%s"' % args.buyer_strategy)
            logger.error('use `bfebench list-strategies %s` to list available strategies' % args.protocol)
            return 1

        data_provider = init_component_subclass(
            self._data_providers_available.get(args.data_provider),
            args.data_provider_parameters
        )

        simulation = Simulation(
            environment=environment,
            protocol=protocol,
            data_provider=data_provider,
            seller_strategy=seller_strategy,
            buyer_strategy=buyer_strategy,
            iterations=args.iterations,
        )
        simulation_result = simulation.run()

        print(simulation_result)

        return 0
