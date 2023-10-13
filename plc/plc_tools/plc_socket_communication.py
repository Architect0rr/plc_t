"""tools for socket communication in plc

Author: Daniel Mohr
Date: 2013-05-14
"""

import pickle
import socket
import struct
import threading

from typing import Any, List


class tools_for_socket_communication:
    def __init__(self):
        self.send_data_to_socket_lock = threading.Lock()

    def send_data_to_socket(self, s: socket.socket, msg: bytes) -> None:
        self.send_data_to_socket_lock.acquire()  # lock
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = s.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalsent = totalsent + sent
        self.send_data_to_socket_lock.release()  # release the lock

    def create_send_format(self, data) -> bytes:
        s: bytes = pickle.dumps(data, -1)
        asd = bytearray(struct.pack(b"!i", len(s)))
        asd.extend(s)
        return bytes(asd)

    def recv_sock(self, s: socket.socket, num: int) -> bytes:
        return s.recv(num)

    def receive_data_from_socket(self, s: socket.socket, bufsize=4096, max_tries=1024 * 1024) -> Any:
        self.send_data_to_socket_lock.acquire()  # lock
        data: bytes = b""
        expected_length = 4
        tries = 0
        while (len(data) < expected_length) and (tries < max_tries):
            data += self.recv_sock(s, min(expected_length - len(data), bufsize))
            tries += 1
        if tries >= max_tries:
            raise socket.timeout
        expected_length += struct.unpack("!i", (data[0:4]))[0]
        while (len(data) < expected_length) and (tries < max_tries):
            data += self.recv_sock(s, min(expected_length - len(data), bufsize))
            tries += 1
        self.send_data_to_socket_lock.release()  # release the lock
        if tries >= max_tries:
            raise socket.timeout
        return pickle.loads((data[4:]))

    def receive_data_from_socket2(self, s: socket.socket, bufsize: int = 4096, _data: str = "") -> List[Any]:
        data = _data.encode("utf-8")
        self.send_data_to_socket_lock.acquire()  # lock
        expected_length = 4
        while len(data) < expected_length:
            data += s.recv(bufsize)
        expected_length += struct.unpack("!i", (data[0:4]))[0]
        while len(data) < expected_length:
            data += s.recv(bufsize)
        v = pickle.loads((data[4:expected_length]))
        data = data[expected_length:]
        self.send_data_to_socket_lock.release()  # release the lock
        return [data, v]
