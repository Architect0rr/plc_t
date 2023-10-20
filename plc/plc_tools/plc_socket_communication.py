"""tools for socket communication in plc

Author: Daniel Mohr
Date: 2013-05-14
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
        self.socket.setblocking(False)

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
