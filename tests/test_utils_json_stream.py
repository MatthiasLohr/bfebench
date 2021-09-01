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
from shutil import rmtree
from tempfile import mkdtemp
from time import sleep
from unittest import TestCase

from bfebench.utils.json_stream import (
    JsonObjectUnixDomainSocketClientStream,
    JsonObjectUnixDomainSocketServerStream,
    JsonObjectSocketStreamForwarder
)


class JsonObjectSocketStream(TestCase):
    def setUp(self) -> None:
        self._tmp_dir = mkdtemp(prefix='bfebench-test-')

    def tearDown(self) -> None:
        rmtree(self._tmp_dir)

    @property
    def tmp_dir(self) -> str:
        return self._tmp_dir

    def test_server_client(self) -> None:
        # init
        server = JsonObjectUnixDomainSocketServerStream(os.path.join(self._tmp_dir, 'socket'))
        client = JsonObjectUnixDomainSocketClientStream(os.path.join(self._tmp_dir, 'socket'))

        # provide time to set up the server
        sleep(0.1)

        # send message from client to server
        client.send_object({'foo': 'bar'})
        received, bytes_count = server.receive_object()
        self.assertEqual(received, {'foo': 'bar'})
        self.assertEqual(bytes_count, 14)

        # send message from server to client
        server.send_object({'reply': 42})
        received, bytes_count = client.receive_object()
        self.assertEqual(received, {'reply': 42})
        self.assertEqual(bytes_count, 13)


class JsonObjectSocketStreamForwarderTest(TestCase):
    def setUp(self) -> None:
        self._tmp_dir = mkdtemp(prefix='bfebench-test-')

    def tearDown(self) -> None:
        rmtree(self._tmp_dir, ignore_errors=True)

    @property
    def tmp_dir(self) -> str:
        return self._tmp_dir

    def test_forward(self) -> None:
        s1 = JsonObjectUnixDomainSocketServerStream(os.path.join(self._tmp_dir, 's1'))
        s2 = JsonObjectUnixDomainSocketServerStream(os.path.join(self._tmp_dir, 's2'))

        forwarder = JsonObjectSocketStreamForwarder(s1, s2)
        forwarder.start()

        sleep(0.1)

        c1 = JsonObjectUnixDomainSocketClientStream(os.path.join(self._tmp_dir, 's1'))
        c2 = JsonObjectUnixDomainSocketClientStream(os.path.join(self._tmp_dir, 's2'))

        sleep(0.1)
        c1.send_object({'foo': 'bar'})
        received, bytes_count = c2.receive_object()
        self.assertEqual(received, {'foo': 'bar'})
        self.assertEqual(bytes_count, 14)

        stats = forwarder.get_stats()
        self.assertEqual(stats.count_1to2, 1)
        self.assertEqual(stats.bytes_1to2, 14)
