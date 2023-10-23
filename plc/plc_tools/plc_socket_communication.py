#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Daniel Mohr
#
# Copyright (C) 2023 Perevoshchikov Egor
#
# This file is part of PlasmaLabControl.
#
# PlasmaLabControl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PlasmaLabControl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PlasmaLabControl.  If not, see <http://www.gnu.org/licenses/>.

"""
tools for socket communication in plc
"""

import pickle
import socket
import struct
import threading
import functools
from typing import Any, List, TypeVar, Callable


T = TypeVar("T")


def socketlock(fn: Callable[..., T]):  # type: ignore
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        self: socket_communication = args[0]
        self.socket_lock.acquire()
        fr: T = fn(*args, **kwargs)
        self.socket_lock.release()
        return fr

    return wrapper


class socket_communication:
    def __init__(self) -> None:
        self.socket_lock = threading.RLock()
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.setblocking(False)
        self.socket.settimeout(5)

    @socketlock
    def __recv(self, num: int) -> bytes:
        return self.socket.recv(num)

    @socketlock
    def __send(self, data: bytes) -> int:
        return self.socket.send(data)

    def send(self, msg: bytes) -> None:
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = self.__send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalsent = totalsent + sent

    def create_send_format(self, data: Any) -> bytes:
        s: bytes = pickle.dumps(data, -1)
        asd = bytearray(struct.pack(b"!i", len(s)))
        asd.extend(s)
        return bytes(asd)

    def receive(self, bufsize=4096, max_tries=1024 * 1024) -> Any:
        data: bytes = b""
        expected_length = 4
        tries = 0
        while (len(data) < expected_length) and (tries < max_tries):
            data += self.__recv(min(expected_length - len(data), bufsize))
            tries += 1
        if tries >= max_tries:
            raise socket.timeout
        expected_length += struct.unpack("!i", (data[0:4]))[0]
        while (len(data) < expected_length) and (tries < max_tries):
            data += self.__recv(min(expected_length - len(data), bufsize))
            tries += 1
        if tries >= max_tries:
            raise socket.timeout
        return pickle.loads((data[4:]))

    def receive_data2(self, bufsize: int = 4096, _data: str = "") -> List[Any]:
        data = _data.encode("utf-8")
        expected_length = 4
        while len(data) < expected_length:
            data += self.__recv(bufsize)
        expected_length += struct.unpack("!i", (data[0:4]))[0]
        while len(data) < expected_length:
            data += self.__recv(bufsize)
        v = pickle.loads((data[4:expected_length]))
        data = data[expected_length:]
        return [data, v]


if __name__ == "__main__":
    pass
