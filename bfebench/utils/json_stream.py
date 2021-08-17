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
import socket
from pathlib import Path
from threading import Thread
from typing import Any, Optional


class JsonObjectSocketStream(object):
    def __init__(self, socket_path: str, chunk_size: int = 4096) -> None:
        self._socket_path = socket_path
        self._chunk_size = chunk_size
        self._buffer = b''

    @property
    def socket_path(self) -> str:
        return self._socket_path

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def socket_connection(self) -> socket.socket:
        raise NotImplementedError()

    def receive_object(self) -> Any:
        object_end_pos = 0

        while True:
            chunk = self.socket_connection.recv(self.chunk_size)

            if chunk == b'':
                raise IOError('socket is closed')

            self._buffer += chunk

            while True:
                new_object_end_pos = self._buffer.find(b'}', object_end_pos)
                if new_object_end_pos == -1:
                    break

                object_end_pos = new_object_end_pos
                try:
                    json_object = json.loads(self._buffer[0:new_object_end_pos + 1])
                    self._buffer = self._buffer[new_object_end_pos + 1:]
                    return json_object
                except json.JSONDecodeError:
                    pass

    def send_object(self, obj: Any) -> int:
        return self.socket_connection.send(json.dumps(obj).encode('utf-8'))


class JsonObjectUnixDomainSocketServerStream(JsonObjectSocketStream):
    def __init__(self, socket_path: str, chunk_size: int = 4096) -> None:
        super().__init__(socket_path, chunk_size)
        self._socket_connection: Optional[socket.socket] = None

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.bind(self.socket_path)
        self._socket.listen(1)
        Thread(target=self._accept).start()

    def _accept(self) -> None:
        self._socket_connection, _ = self._socket.accept()

    @property
    def socket_connection(self) -> socket.socket:
        if self._socket_connection is None:
            raise IOError('no active connection')
        return self._socket_connection

    def __del__(self) -> None:
        if self._socket_connection is not None:
            self._socket_connection.close()
        self._socket.close()
        Path(self.socket_path).unlink()


class JsonObjectUnixDomainSocketClientStream(JsonObjectSocketStream):
    def __init__(self, socket_path: str, chunk_size: int = 4096) -> None:
        super().__init__(socket_path, chunk_size)

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(self.socket_path)

    @property
    def socket_connection(self) -> socket.socket:
        return self._socket

    def __del__(self) -> None:
        self._socket.close()
