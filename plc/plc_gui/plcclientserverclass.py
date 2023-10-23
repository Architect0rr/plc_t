#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Daniel Mohr
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
client server communication classes for plc
"""

import time
import shlex
import socket
import logging
import threading
import subprocess
from queue import Queue
import tkinter
import tkinter.ttk
from abc import abstractmethod
from typing import Callable, List, TypeVar
import functools

from .read_config_file import read_config_file
from ..plc_tools.plc_socket_communication import socket_communication, socketlock
from .misc.splash import Splasher

T = TypeVar("T")


def if_connect(fn: Callable[..., bool]):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> bool:
        self: socket_communication_class = args[0]
        if self.connected:
            return fn(*args, **kwargs)
        else:
            self.log.warning("Not connected")
            return False

    return wrapper


def data_lock(fn: Callable[..., T]):  # type: ignore
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        self: socket_communication_class = args[0]
        self.datalock.acquire()
        fr = fn(*args, **kwargs)
        self.datalock.release()
        return fr

    return wrapper


def general_lock(fn: Callable[..., T]):  # type: ignore
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        self: socket_communication_class = args[0]
        self.lock.acquire()
        fr = fn(*args, **kwargs)
        self.lock.release()
        return fr

    return wrapper


def ee_report(fn: Callable[..., T]):  # type: ignore
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        self: socket_communication_class = args[0]
        self.log.warning("Entered")
        fr = fn(*args, **kwargs)
        self.log.warning("Exited")
        return fr

    return wrapper


class socket_communication_class(socket_communication):
    """
    base class for continued socket communication
    """

    def __init__(self, log: logging.Logger, config: read_config_file, confsect: str, bufsize: int = 4096) -> None:
        super().__init__()
        self.lock = threading.RLock()
        self.datalock = threading.RLock()
        self.update_thread_lock = threading.RLock()

        # flags
        self.server_started: bool = False
        self.connected: bool = False

        self.log = log
        self.actualvalue = None
        self.setpoint = None
        self.bufsize = bufsize  # read/receive Bytes at once

        self.lastupdate = time.time()
        self.updatethreadrunning = False
        self.updatethreadsleeptime = 0.001
        self.serialnumber = "-1"
        self.myservername = "server"
        self.prc_srv: subprocess.Popen

        self.trigger_out: bool = config.values.getboolean(confsect, "trigger_out")
        self.cmd: str = config.values.get(confsect, "server_command")
        self.ip: str = config.values.get(confsect, "server_ip")
        self.sport: int = config.values.getint(confsect, "server_port")
        self.server_max_start_time: float = config.values.getfloat(confsect, "server_max_start_time")
        self.update_intervall: float = config.values.getint(confsect, "update_intervall") / 1000.0
        self.logfile: str = config.values.get(confsect, "server_logfile")
        self.datalogfile: str = config.values.get(confsect, "server_datalogfile")
        self.rf: str = config.values.get(confsect, "server_runfile")
        self.start_server: bool = config.values.getboolean(confsect, "start_server")
        self.dev: str = config.values.get(confsect, "server_device")
        self.st = config.values.get(confsect, "server_timedelay")

    def update(self) -> bool:
        return self.socket_communication_with_server()

    @if_connect
    @data_lock
    def get_actualvalues(self) -> bool:
        try:
            self.send(b"getact")
            self.actualvalue = self.receive(self.bufsize)
            return True
        except Exception:
            self.log.exception("Could not get actualvalues from server!")
            return False

    @if_connect
    def socket_communication_with_server(self) -> bool:
        if self.setpoint is not None:
            # set self.setpoint
            ts = bytearray(b"p ")
            ts.extend(self.create_send_format(self.setpoint))
            if self.trigger_out:
                ts.extend(b"!w2d")
                self.send(bytes(ts))
            else:
                self.send(bytes(ts))
            self.myextra_socket_communication_with_server()
        # read self.actualvalue
        self.get_actualvalues()
        return True

    @abstractmethod
    def set_default_values(self):
        ...

    @abstractmethod
    def myextra_socket_communication_with_server(self):
        ...

    @abstractmethod
    def actualvalue2setpoint(self):
        ...

    def start_request(self, simulate: bool = False, debug: bool = True) -> bool:
        self.log.debug("Controller start requested")
        return self.start(simulate, debug)

    def stop_request(self) -> bool:
        self.log.debug("Controller stop requested")
        return self.stop()

    @socketlock
    @data_lock
    def connect(self) -> bool:
        if not self.connected:
            self.log.debug(f"Trying to connect to {self.ip}:{self.sport}")
            try:
                self.socket: socket.socket
                self.socket.connect((self.ip, self.sport))
                self.log.debug("Connected")
                self.connected = True
                return True
            except Exception:
                self.log.exception(f"Cannot connect to {self.myservername} at {self.ip}:{self.sport}")
                return False
        else:
            return False

    def server_start(self, simulate: bool = False, debug: bool = True) -> bool:
        self.log.debug("Server was not launched, launching it")
        c: List[str] = [self.cmd]
        if self.dev != "-1":
            c += ["-device", self.dev]
        # if self.serialnumber != "-1":
        #     # acceleration sensor
        #     c += ["-SerialNumber", self.serialnumber]
        #     c += ["-datalogformat", f"{self.datalogformat}"]
        #     c += ["-maxg", f"{self.maxg}"]
        c += [
            "-logfile",
            self.logfile,
            "-datalogfile",
            self.datalogfile,
            "-runfile",
            self.rf,
            "-ip",
            self.ip,
            "-port",
            "%s" % self.sport,
            "-debug",
            "1",
        ]
        if debug:
            c += ["-debug", "1"]
        if simulate:
            c += ["-simulate"]
        if self.st != "-1":
            c += ["-timedelay", "%s" % self.st]
        self.log.debug(f"Executing '{shlex.join(c)}'")
        self.prc_srv = subprocess.Popen(c)
        t0 = time.time()
        self.prc_srv.poll()
        self.log.debug(f"Waiting for server to start for {self.server_max_start_time} secs")
        while (self.prc_srv.returncode is None) and (time.time() - t0 < self.server_max_start_time):
            time.sleep(0.01)
            self.prc_srv.poll()

        time.sleep(0.5)
        self.prc_srv.poll()
        if self.prc_srv.returncode is None:
            self.log.debug(f"{self.myservername} seems to work!")
            self.server_started = True
            return True
        else:
            if self.prc_srv.returncode == 0:
                self.log.debug(f"By any reason {self.myservername} returned 0")
            else:
                self.log.warning(f"{self.myservername} was terminated with status: {self.prc_srv.returncode}")
            return False

    @general_lock
    def start(self, simulate: bool = False, debug: bool = True) -> bool:
        self.log.debug("Started")
        if not self.server_started:
            if not self.server_start(simulate, debug):
                return False
        if not self.connect():
            return False
        self.log.debug("Updating values")
        self.get_actualvalues()
        self.actualvalue2setpoint()
        self.log.debug("Starting updating thread")
        self.updatethreadrunning = True
        self.updating_thread = threading.Thread(target=self.updatethread)
        self.updating_thread.daemon = True
        self.updating_thread.start()
        self.log.debug("Update thread running")
        return True

    def updatethread(self) -> None:
        """
        if necessary write values self.setpoint to device
        and read them from device to self.actualvalue
        """
        while True:
            self.update_thread_lock.acquire()
            if not self.updatethreadrunning:
                self.update_thread_lock.release()
                return
            self.update_thread_lock.release()
            self.update()
            time.sleep(self.updatethreadsleeptime)

    @if_connect
    def __stop(self) -> bool:
        self.update_thread_lock.acquire()
        self.updatethreadrunning = False
        self.update_thread_lock.release()
        self.log.debug("Joining update thread")
        self.updating_thread.join()
        self.log.debug(f"Disconnecting from '{self.myservername}' {self.ip}:{self.sport}")
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception:
            self.log.warning("Bad socket close")
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.log.debug("Stopped.")
        return True

    def stop(self) -> bool:
        if self.server_started:
            self.log.debug("Server started, trying to stop it")
            self.prc_srv.poll()
            if self.prc_srv.returncode is None:
                self.log.debug("Terminating server")
                self.prc_srv.terminate()
                # time.sleep(1)
                self.prc_srv.poll()
                if self.prc_srv.returncode is None:
                    self.prc_srv.kill()
                    self.log.debug("Server killed")
                else:
                    self.log.debug("Server terminated")
            else:
                self.log.debug(f"Server has already exited with {self.prc_srv.returncode}")
            self.server_started = False
        else:
            self.log.debug("Server was not started")
        return self.__stop()


class scs_gui(tkinter.ttk.Frame):
    def __init__(self, _root: tkinter.LabelFrame, backend: socket_communication_class, splasher: Splasher) -> None:
        super().__init__(_root)
        self.root = _root
        self.backend = backend
        self.splasher = splasher
        self.start_button = tkinter.Button(self, text="Start", command=self.start)
        self.start_button.grid(row=0, column=0)
        self.stop_button = tkinter.Button(self, text="Stop", command=self.stop, state=tkinter.DISABLED)
        self.stop_button.grid(row=0, column=1)
        self.debug_on = tkinter.BooleanVar(value=True)
        self.debug_chbox = tkinter.Checkbutton(self, text="Debug", variable=self.debug_on)
        self.debug_chbox.grid(row=1, column=0)
        self.simulate_on = tkinter.BooleanVar(value=True)
        self.simulate_chbox = tkinter.Checkbutton(self, text="Simulate", variable=self.simulate_on)
        self.simulate_chbox.grid(row=1, column=1)
        backend.set_default_values()

    def __start(self, q: Queue) -> bool:
        sim = self.simulate_on.get()
        deb = self.debug_on.get()
        rt = self.backend.start_request(sim, deb)
        self.splasher.splash_set_stop()
        q.put(rt)
        return rt

    def __stop(self, q: Queue) -> bool:
        rt = self.backend.stop_request()
        # self.backend.log.warning("GUI: splash setting stop")
        self.splasher.splash_set_stop()
        # self.backend.log.warning("GUI: splash setted stop, getting item from queue")
        q.put(rt)
        # self.backend.log.warning("GUI: got item from queue")
        return rt

    def start(self) -> None:
        q: Queue = Queue()
        thr = threading.Thread(target=self.__start, args=(q,))
        thr.start()
        self.splasher.splash_start()
        self.splasher.splash_stop()
        thr.join()
        rt: bool = q.get()
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     future = executor.submit(self.__start)
        #     self.splasher.splash_start()
        #     self.splasher.splash_stop()
        #     rt: bool = future.result()
        if rt:
            self.start_button.configure(state=tkinter.DISABLED)
            self.stop_button.configure(state=tkinter.NORMAL)
        else:
            self.start_button.configure(state=tkinter.NORMAL)
            self.stop_button.configure(state=tkinter.DISABLED)

    def stop(self) -> None:
        q: Queue = Queue()
        thr = threading.Thread(target=self.__stop, args=(q,))
        thr.start()
        self.splasher.splash_start()
        self.splasher.splash_stop()
        thr.join()
        rt: bool = q.get()
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     future = executor.submit(self.__stop)
        #     self.splasher.splash_start()
        #     self.backend.log.warning("Splash start ended")
        #     self.splasher.splash_stop()
        #     self.backend.log.warning("Splash stopped")
        #     rt: bool = future.result()
        if rt:
            self.stop_button.configure(state=tkinter.DISABLED)
            self.start_button.configure(state=tkinter.NORMAL)
        else:
            self.stop_button.configure(state=tkinter.NORMAL)
            self.start_button.configure(state=tkinter.DISABLED)


if __name__ == "__main__":
    pass
