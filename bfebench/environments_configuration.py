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

from typing import Any, Dict

import yaml
from web3 import Web3
from web3.providers.rpc import HTTPProvider

from .environment import Environment
from .errors import EnvironmentsConfigurationError


class EnvironmentsConfiguration(object):
    def __init__(self, filename: str) -> None:
        with open(filename, "r") as fp:
            data = yaml.safe_load(fp)

        if data is None:
            raise EnvironmentsConfigurationError("%s does not seem to contain valid YAML" % filename)

        self._operator_environment = self._yaml2environment(data.get("operator"))
        self._seller_environment = self._yaml2environment(data.get("seller"))
        self._buyer_environment = self._yaml2environment(data.get("buyer"))

    @staticmethod
    def _yaml2environment(data: Dict[str, Any]) -> Environment:
        endpoint_config = data.get("endpoint")
        if endpoint_config is None:
            raise ValueError("no endpoint configuration provided")

        wallet_config = data.get("wallet")
        if wallet_config is None:
            raise ValueError("no wallet configuration provided")

        return Environment(
            web3=Web3(HTTPProvider(endpoint_config.get("url", "http://localhost:8545/"))),
            wallet_address=wallet_config.get("address"),
            private_key=wallet_config.get("privateKey"),
        )

    @property
    def operator_environment(self) -> Environment:
        return self._operator_environment

    @property
    def seller_environment(self) -> Environment:
        return self._seller_environment

    @property
    def buyer_environment(self) -> Environment:
        return self._buyer_environment
