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

from bfebench.environments_configuration import EnvironmentsConfiguration


class EnvironmentsConfigurationTest(TestCase):
    def test_missing_file(self) -> None:
        self.assertRaises(FileNotFoundError, EnvironmentsConfiguration, "/some/imaginary/file.yaml")

    def test_load(self) -> None:
        ec = EnvironmentsConfiguration("./tests/testdata/environment-configuration.yaml")

        # operator configuration
        self.assertEqual(
            ec.operator_environment.wallet_address,
            "0xeEC9205723a4E629FDDD13A02673Fb354fDCA0e2",
        )
        self.assertEqual(
            ec.operator_environment.private_key,
            "0xaafd5345c05ca07f930f0c8bc91769dab1761f2a5376a710a79d5e26de7f6b9b",
        )

        # seller configuration
        self.assertEqual(
            ec.seller_environment.wallet_address,
            "0xB5dEaA160B6B018D4A7F1Ef9c323a116E59F7545",
        )
        self.assertEqual(
            ec.seller_environment.private_key,
            "0x60f0d57b9d72f429e9eda5213c3df17377b970ef55d5a1a4ef57f01d445258d2",
        )

        # buyer configuration
        self.assertEqual(
            ec.buyer_environment.wallet_address,
            "0x98D5858f0347eCdEBBBa41067814C48Ed9B34153",
        )
        self.assertEqual(ec.buyer_environment.private_key, None)
