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

import json
import logging
import os
import socket
from shutil import rmtree
from tempfile import mkdtemp
from threading import Thread
from typing import Any, Dict, Optional

from eth_tester import EthereumTester, PyEVMBackend  # type: ignore
from web3 import IPCProvider, EthereumTesterProvider
from web3.providers.base import BaseProvider

from .common import Environment


logger = logging.getLogger(__name__)


class PyEVMEnvironment(Environment):
    name = 'Py-EVM'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._tmp_dir: Optional[str] = None
        self._eth_tester: Optional[EthereumTester] = None
        self._socket_handler: Optional[PyEVMSocketListener] = None

    def set_up(self) -> None:
        self._tmp_dir = mkdtemp(prefix='bfebench-')
        self._eth_tester = EthereumTester(backend=PyEVMBackend())
        self._socket_handler = PyEVMSocketListener(self._get_socket_path(), self._eth_tester)
        self._socket_handler.start()

    def tear_down(self) -> None:
        if self._tmp_dir is not None:
            rmtree(self._tmp_dir)
            self._tmp_dir = None

    def _get_socket_path(self) -> str:
        if self._tmp_dir is None:
            raise ValueError('tmp dir should not be None')
        return os.path.join(self._tmp_dir, 'pyevm.ipc')

    def _get_web3_provider(self) -> BaseProvider:
        return IPCProvider(self._get_socket_path())


class PyEVMSocketListener(Thread):
    def __init__(self, socket_path: str, eth_tester: EthereumTester):
        super().__init__(daemon=True)
        self._socket_path = socket_path
        self._eth_tester = eth_tester

    def run(self) -> None:
        ipc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ipc_socket.bind(self._socket_path)
        ipc_socket.listen(1)
        while True:
            connection, address = ipc_socket.accept()
            connection_listener = PyEVMConnectionListener(connection, self._eth_tester)
            connection_listener.start()


class PyEVMConnectionListener(Thread):
    def __init__(self, connection: socket.socket, eth_tester: EthereumTester):
        super().__init__(daemon=True)
        self._connection = connection
        self._eth_tester = eth_tester
        self._eth_provider = EthereumTesterProvider(self._eth_tester)

    def run(self) -> None:

        active = True
        request_data = b''

        while active:
            buffer = self._connection.recv(4096)
            if buffer == b'':
                active = False

            request_data += buffer
            try:
                json_object = json.loads(request_data)
                self._handle_request(json_object)
                request_data = b''
            except json.JSONDecodeError:
                pass

    def _handle_request(self, request_object: Dict[str, Any]) -> None:
        result = self._eth_provider.make_request(
            request_object.get('method'),
            request_object.get('params')
        )
        self._connection.send(json.dumps(result).encode('utf-8'))
