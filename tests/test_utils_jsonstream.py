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

import os
import socket
from shutil import rmtree
from tempfile import mkdtemp
from threading import Thread
from typing import Any, Optional
from unittest import TestCase

from bfebench.utils.jsonstream import json_object_socket_stream


class JsonObjectSocketStreamTest(TestCase):
    SOCKET_NAME = 'bfebench-test.ipc'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._tmp_dir: Optional[str] = None
        self._writer_socket: Optional[socket.socket] = None
        self._reader_socket: Optional[socket.socket] = None

    def setUp(self) -> None:
        self._tmp_dir = mkdtemp(prefix='bfebench-test-')
        self._writer_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._writer_socket.bind(self._get_socket_path())
        self._writer_socket.listen()

        self._reader_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._reader_socket.connect(self._get_socket_path())

    def tearDown(self) -> None:
        if self._writer_socket is not None:
            self._writer_socket.close()
            self._writer_socket = None

        if self._reader_socket is not None:
            self._reader_socket.close()
            self._reader_socket = None

        if self._tmp_dir is not None:
            rmtree(self._tmp_dir)
            self._tmp_dir = None

    def _get_socket_path(self) -> str:
        if self._tmp_dir is None:
            raise ValueError('_tmp_dir should not be None here')
        return os.path.join(self._tmp_dir, self.SOCKET_NAME)

    def _send_to_socket(self, data: bytes) -> None:
        if self._writer_socket is None:
            raise ValueError('_send_to_socket should not be None here')
        JsonObjectSocketStreamTestSenderThread(self._writer_socket, data).start()

    def _get_reader_socket(self) -> socket.socket:
        if self._reader_socket is None:
            raise ValueError('_reader_socket should not be None here')
        return self._reader_socket

    def test_single_empty(self) -> None:
        self._send_to_socket(b'{}')
        result = [x for x in json_object_socket_stream(self._get_reader_socket())]
        self.assertEqual(result, [{}])

    def test_double_empty(self) -> None:
        self._send_to_socket(b'{}{}')
        result = [x for x in json_object_socket_stream(self._get_reader_socket())]
        self.assertEqual(result, [{}, {}])

    def test_double_empty_next(self) -> None:
        self._send_to_socket(b'{}{}')
        generator = json_object_socket_stream(self._get_reader_socket())
        self.assertEqual({}, next(generator))
        self.assertEqual({}, next(generator))


class JsonObjectSocketStreamTestSenderThread(Thread):
    def __init__(self, sender_socket: socket.socket, data: bytes) -> None:
        super().__init__(daemon=True)
        self._sender_socket = sender_socket
        self._data = data

    def run(self) -> None:
        connection, address = self._sender_socket.accept()
        connection.send(self._data)
        connection.close()
