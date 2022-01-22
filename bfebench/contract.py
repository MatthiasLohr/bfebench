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

from __future__ import annotations

import logging
import os
from shutil import rmtree
from tempfile import mkdtemp
from typing import Any, Dict, List

import jinja2
import solcx
from eth_typing.evm import ChecksumAddress
from semantic_version import Version  # type: ignore
from solcx.exceptions import SolcInstallationError  # type: ignore

logger = logging.getLogger(__name__)


class Contract(object):
    def __init__(
        self,
        abi: Dict[str, Any],
        bytecode: str | None = None,
        address: ChecksumAddress | None = None,
    ) -> None:
        self._abi = abi
        self._bytecode = bytecode
        self._address = address

    @property
    def abi(self) -> Dict[str, Any]:
        return self._abi

    @property
    def bytecode(self) -> str | None:
        return self._bytecode

    @property
    def address(self) -> ChecksumAddress | None:
        return self._address

    @address.setter
    def address(self, address: ChecksumAddress) -> None:
        self._address = address


class SolidityContract(Contract):
    pass


class SolidityContractSourceCodeManager(object):
    def __init__(self, allowed_paths: List[str] | None = None) -> None:
        self._source_files: List[str] = []

        if allowed_paths is None:
            self._allowed_paths = []
        else:
            self._allowed_paths = [self._normalize_path(path) for path in allowed_paths]

        self._tmpdir = mkdtemp(prefix="bfebench-solc-")

    def __del__(self) -> None:
        rmtree(self._tmpdir)

    def add_contract_file(self, contract_file: str) -> None:
        self._source_files.append(self._normalize_path(contract_file))

    def add_contract_template_file(
        self, contract_template_file: str, context: dict[str, Any]
    ) -> None:
        if contract_template_file.endswith(".tpl.sol"):
            tmp_source_code_file = os.path.basename(contract_template_file)[:-8]
        else:
            tmp_source_code_file = os.path.basename(contract_template_file) + ".sol"
        tmp_source_code_file_abs = os.path.join(self._tmpdir, tmp_source_code_file)

        with open(contract_template_file, "r") as fp:
            template_code = fp.read()

        template = jinja2.Template(template_code)

        with open(tmp_source_code_file_abs, "w") as fp:
            fp.write(template.render(**context))

        self._source_files.append(tmp_source_code_file_abs)

    def compile(self, solc_version: str) -> dict[str, SolidityContract]:
        self._ensure_solc(solc_version)
        solcx.set_solc_version(solc_version)

        compile_result = solcx.compile_files(
            source_files=self._source_files, allow_paths=self._allowed_paths
        )

        contracts = {}
        for contract_identifier, contract_result in compile_result.items():
            contract_file, contract_name = str(contract_identifier).split(":")
            contracts.update(
                {
                    contract_name: SolidityContract(
                        abi=contract_result.get("abi"),
                        bytecode=contract_result.get("bin"),
                    )
                }
            )
        return contracts

    @staticmethod
    def _ensure_solc(solc_version: str) -> None:
        if Version(solc_version) in solcx.get_installed_solc_versions():
            logger.debug("checking for solc %s: found" % solc_version)
        else:
            logger.debug("checking for solc %s: not found, installing" % solc_version)
            try:
                solcx.install_solc(solc_version)
            except SolcInstallationError:
                logger.debug(
                    "normal installation failed, trying to compile (requires %s"
                    % ", ".join(
                        [
                            "cmake",
                            "libboost-dev",
                            "libboost-filesystem-dev",
                            "libboost-program-options-dev",
                            "libboost-test-dev",
                        ]
                    )
                )
                solcx.compile_solc(Version(solc_version))

    @staticmethod
    def _normalize_path(path: str) -> str:
        return os.path.realpath(path)
