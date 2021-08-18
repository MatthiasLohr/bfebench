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
from typing import Any, Optional, Tuple


class JsonObjectSocketStreamError(IOError):
    pass


class JsonObjectSocketStreamClosedUnexpectedly(JsonObjectSocketStreamError):
    pass


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

    def receive_object(self) -> Tuple[Any, int]:
        object_end_pos = 0

        while True:
            chunk = self.socket_connection.recv(self.chunk_size)

            if chunk == b'':
                if self._buffer == b'':
                    return None, 0
                else:
                    raise JsonObjectSocketStreamClosedUnexpectedly

            self._buffer += chunk

            while True:
                new_object_end_pos = self._buffer.find(b'}', object_end_pos)
                if new_object_end_pos == -1:
                    break

                object_end_pos = new_object_end_pos
                try:
                    bytes_count = new_object_end_pos + 1
                    json_object = json.loads(self._buffer[0:bytes_count])
                    self._buffer = self._buffer[new_object_end_pos + 1:]
                    return json_object, bytes_count
                except json.JSONDecodeError:
                    pass

    def send_object(self, obj: Any) -> int:
        return self.socket_connection.send(json.dumps(obj).encode('utf-8'))

    def close(self) -> None:
        self.socket_connection.close()


class JsonObjectUnixDomainSocketServerStream(JsonObjectSocketStream):
    def __init__(self, socket_path: str, chunk_size: int = 4096) -> None:
        super().__init__(socket_path, chunk_size)
        self._socket_connection: Optional[socket.socket] = None

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.bind(self.socket_path)
        self._socket.listen(1)

        self._accepting_thread = Thread(target=self._accept, daemon=True)
        self._accepting_thread.start()

    def _accept(self) -> None:
        self._socket_connection, _ = self._socket.accept()

    @property
    def socket_connection(self) -> socket.socket:
        self._accepting_thread.join()
        if self._socket_connection is None:
            raise IOError('no active connection')
        return self._socket_connection

    def close(self) -> None:
        if self._socket_connection is not None:
            self._socket_connection.close()
        self._socket.close()

    def __del__(self) -> None:
        self.close()
        Path(self.socket_path).unlink(missing_ok=True)


class JsonObjectUnixDomainSocketClientStream(JsonObjectSocketStream):
    def __init__(self, socket_path: str, chunk_size: int = 4096) -> None:
        super().__init__(socket_path, chunk_size)

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(self.socket_path)

    @property
    def socket_connection(self) -> socket.socket:
        return self._socket

    def close(self) -> None:
        self._socket.close()

    def __del__(self) -> None:
        self.close()


class JsonObjectSocketStreamForwarder(object):
    class Counter(object):
        def __init__(self) -> None:
            self.bytes = 0
            self.objects = 0

    def __init__(self, stream1: JsonObjectSocketStream, stream2: JsonObjectSocketStream) -> None:
        self._stream1 = stream1
        self._stream2 = stream2

        self._counter_1to2 = JsonObjectSocketStreamForwarder.Counter()
        self._counter_2to1 = JsonObjectSocketStreamForwarder.Counter()

        self._thread_1to2 = Thread(
            target=self._forward,
            args=(self._stream1, self._stream2, self._counter_1to2),
            daemon=True
        )
        self._thread_2to1 = Thread(
            target=self._forward,
            args=(self._stream2, self._stream1, self._counter_2to1),
            daemon=True
        )

    @property
    def bytes_1to2(self) -> int:
        return self._counter_1to2.bytes

    @property
    def bytes_2to1(self) -> int:
        return self._counter_2to1.bytes

    @property
    def objects_1to2(self) -> int:
        return self._counter_1to2.objects

    @property
    def objects_2to1(self) -> int:
        return self._counter_2to1.objects

    def start(self) -> None:
        self._thread_1to2.start()
        self._thread_2to1.start()

    @staticmethod
    def _forward(source: JsonObjectSocketStream, target: JsonObjectSocketStream,
                 counter: 'JsonObjectSocketStreamForwarder.Counter') -> None:
        while True:
            received, bytes_count = source.receive_object()
            if received is None:  # socket has been closed cleanly
                break
            counter.objects += 1
            counter.bytes += bytes_count
            target.send_object(received)
