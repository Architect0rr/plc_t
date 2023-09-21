"""tools for socket communication in plc

Author: Daniel Mohr
Date: 2013-05-14
"""

import pickle
import socket
import struct
import threading


class tools_for_socket_communication:
    def __init__(self):
        self.send_data_to_socket_lock = threading.Lock()

    def send_data_to_socket(self, s, msg):
        self.send_data_to_socket_lock.acquire()  # lock
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = s.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
        self.send_data_to_socket_lock.release()  # release the lock

    def create_send_format(self, data):
        s = pickle.dumps(data, -1)
        return "%s%s" % (struct.pack("!i", len(s)), s)

    def recv_sock(self, s: socket.socket, num: int) -> str:
        return s.recv(num).decode("utf-8")

    def receive_data_from_socket(self, s: socket.socket, bufsize=4096, max_tries=1024 * 1024):
        self.send_data_to_socket_lock.acquire()  # lock
        data: str = ""
        expected_length = 4
        tries = 0
        while (len(data) < expected_length) and (tries < max_tries):
            data += self.recv_sock(s, min(expected_length - len(data), bufsize))
            tries += 1
        if tries >= max_tries:
            raise socket.timeout
        expected_length += struct.unpack("!i", (data[0:4]).encode("utf-8"))[0]
        while (len(data) < expected_length) and (tries < max_tries):
            data += self.recv_sock(s, min(expected_length - len(data), bufsize))
            tries += 1
        self.send_data_to_socket_lock.release()  # release the lock
        if tries >= max_tries:
            raise socket.timeout
        return pickle.loads((data[4:]).encode("utf-8"))

    def receive_data_from_socket2(self, s, bufsize=4096, data=""):
        self.send_data_to_socket_lock.acquire()  # lock
        expected_length = 4
        while len(data) < expected_length:
            data += s.recv(bufsize)
        expected_length += struct.unpack("!i", (data[0:4]).encode("utf-8"))[0]
        while len(data) < expected_length:
            data += s.recv(bufsize)
        v = pickle.loads((data[4:expected_length]).encode("utf-8"))
        data = data[expected_length:]
        self.send_data_to_socket_lock.release()  # release the lock
        return [data, v]
