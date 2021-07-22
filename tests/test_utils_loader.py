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

from unittest import TestCase

from bfebench import environments
from bfebench import protocols
from bfebench.utils.loader import get_named_subclasses


class GetNamedSubclassesTest(TestCase):
    def test_get_named_subclasses_environments(self) -> None:
        environments_available = get_named_subclasses(environments, environments.Environment)
        self.assertEqual(environments_available, {
            'Py-EVM': environments.PyEVMEnvironment
        })

    def test_get_named_subclasses_protocols(self) -> None:
        protocols_available = get_named_subclasses(protocols, protocols.Protocol)
        self.assertEqual(protocols_available, {
            'FairSwap': protocols.FairSwap
        })
