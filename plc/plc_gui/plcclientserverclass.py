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

import logging
import socket
import subprocess
import threading
import time
import tkinter
from typing import List
import tkinter.ttk
from abc import abstractmethod
import shlex

from .read_config_file import read_config_file
from ..plc_tools import plc_socket_communication


class socket_communication_class(plc_socket_communication.tools_for_socket_communication):
    """
    base class for continued socket communication
    """

    def __init__(self, log: logging.Logger, config: read_config_file, confsect: str, bufsize: int = 4096):
        self.lock = threading.Lock()
        self.lock.acquire()  # lock

        self.updatelock = threading.Lock()
        self.socketlock = threading.Lock()
        self.get_actualvalues_lock = threading.Lock()
        self.send_data_to_socket_lock = threading.Lock()
        self.updatethread_lock = threading.Lock()
        self.log = log
        self.actualvalue = None
        self.setpoint = None
        self.bufsize = bufsize  # read/receive Bytes at once

        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lastupdate = time.time()
        self.updatethreadrunning = False
        self.updatethreadsleeptime = 0.001
        self.serialnumber = "-1"
        self.myservername = "server"
        self.server_started: bool = False
        self.connected: bool = False

        self.trigger_out: bool = config.values.getboolean(confsect, "trigger_out")
        self.cmd: str = config.values.get(confsect, "server_command")
        self.ip: str = config.values.get(confsect, "server_ip")
        self.sport: int = config.values.getint(confsect, "server_port")
        self.server_max_start_time: float = config.values.getfloat(confsect, "server_max_start_time")
        self.update_intervall: float = config.values.getint(confsect, "update_intervall") / 1000.0
        self.logfile = config.values.get(confsect, "server_logfile")
        self.datalogfile = config.values.get(confsect, "server_datalogfile")
        self.rf = config.values.get(confsect, "server_runfile")
        self.start_server: bool = config.values.getboolean(confsect, "start_server")
        self.dev: str = config.values.get(confsect, "server_device")
        self.st = config.values.get(confsect, "server_timedelay")

        self.lock.release()  # release the lock

    def update(self) -> None:
        self.updatelock.acquire()  # lock
        self.socket_communication_with_server()
        self.updatelock.release()  # release the lock

    def get_actualvalues(self) -> None:
        self.get_actualvalues_lock.acquire()  # lock
        if self.connected:
            try:
                self.send_data_to_socket(self.socket, b"getact")
                self.actualvalue = self.receive_data_from_socket(self.socket, self.bufsize)
            except Exception:
                self.log.error("Could not get actualvalues from server!")
        self.get_actualvalues_lock.release()  # release the lock

    def socket_communication_with_server(self) -> None:
        self.socketlock.acquire()  # lock
        if self.connected:
            if self.setpoint is not None:
                # set self.setpoint
                ts = bytearray(b"p ")
                ts.extend(self.create_send_format(self.setpoint))
                if self.trigger_out:
                    ts.extend(b"!w2d")
                    self.send_data_to_socket(self.socket, bytes(ts))
                else:
                    self.send_data_to_socket(self.socket, bytes(ts))
                self.myextra_socket_communication_with_server()
            # read self.actualvalue
            self.get_actualvalues()
            self.reading_last = time.time()
        self.socketlock.release()  # release the lock

    @abstractmethod
    def set_default_values(self):
        ...

    @abstractmethod
    def myextra_socket_communication_with_server(self):
        ...

    @abstractmethod
    def actualvalue2setpoint(self):
        ...

    def start_request(self) -> None:
        self.lock.acquire()  # lock
        self.log.debug("Controller start requested, starting backgroud thread")
        starttimer = threading.Thread(target=self.start)
        starttimer.daemon = True
        starttimer.start()
        self.lock.release()  # release the lock

    def start(self) -> None:
        self.lock.acquire()  # lock
        self.socketlock.acquire()  # lock
        self.log.debug("Started")
        if not self.server_started:
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
            if self.st != "-1":
                c += ["-timedelay", "%s" % self.st]
            self.log.debug(f"Executing '{shlex.join(c)}'")
            prc_srv = subprocess.Popen(c)
            t0 = time.time()
            prc_srv.poll()
            self.log.debug(f"Waiting for server to start for {self.server_max_start_time} secs")
            while (prc_srv.returncode is None) and (time.time() - t0 < self.server_max_start_time):
                time.sleep(0.01)
                prc_srv.poll()
            prc_srv.poll()
            if prc_srv.returncode is None:
                self.log.debug(f"{self.myservername} does not work until now!")
            else:
                if prc_srv.returncode == 0:
                    self.log.debug(f"{self.myservername} seems to work")
                else:
                    self.log.warning(f"{self.myservername} was terminated with status: {prc_srv.returncode}")
            time.sleep(0.05)
        if not self.connected:
            self.log.debug(f"Trying to connect to {self.ip}:{self.sport}")
            try:
                self.socket.connect((self.ip, self.sport))
                self.log.debug("Connected")
                self.connected = True
            except Exception:
                self.log.warning(f"Cannot connect to {self.myservername} at {self.ip}:{self.sport}")
                return
        self.log.debug("Updating values")
        self.get_actualvalues()
        self.actualvalue2setpoint()
        # self.correct_state_intern()
        self.socketlock.release()  # release the lock
        self.lock.release()  # release the lock
        self.log.debug("Starting updating thread")
        self.updatethreadrunning = True
        self.updating_thread = threading.Thread(target=self.updatethread)
        self.updating_thread.daemon = True
        self.updating_thread.start()

    def updatethread(self) -> None:
        """if necessary write values self.setpoint to device
        and read them from device to self.actualvalue

        Author: Daniel Mohr
        Date: 2013-01-10
        """
        self.updatethread_lock.acquire()  # lock
        while self.updatethreadrunning:
            self.socket_communication_with_server()
            nextupdate = self.lastupdate + self.update_intervall
            self.lastupdate = time.time()
            time.sleep(self.updatethreadsleeptime)
            while self.updatethreadrunning and (time.time() < nextupdate):
                time.sleep(self.updatethreadsleeptime)
        self.updatethread_lock.release()  # release the lock

    def stop_request(self) -> None:
        self.log.debug("Controller stop requested")
        self.log.debug("Starting stop thread")
        starttimer = threading.Thread(target=self.stop)
        starttimer.daemon = True
        starttimer.start()

    def stop(self) -> None:
        self.updatethreadrunning = False
        self.log.debug("Joining update thread")
        self.updating_thread.join()
        time.sleep(0.001)
        self.lock.acquire()  # lock
        self.socketlock.acquire()  # lock
        if self.connected:
            self.log.debug(f"Disconnecting from '{self.myservername}' {self.ip}:{self.sport}")
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except Exception:
                self.log.warning("Bad socket close")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketlock.release()  # release the lock
        # self.correct_state_intern()
        self.log.debug("Stopped.")
        self.lock.release()  # release the lock


class scs_gui(tkinter.ttk.Frame):
    def __init__(self, _root: tkinter.LabelFrame, backend: socket_communication_class) -> None:
        super().__init__(_root)
        self.root = _root
        self.backend = backend
        self.start_button = tkinter.Button(self.root, text="Start", command=self.start)
        self.stop_button = tkinter.Button(self.root, text="Stop", command=self.stop, state=tkinter.DISABLED)
        self.start_button.grid(row=0, column=0)
        self.stop_button.grid(row=0, column=1)
        backend.set_default_values()

    def start(self) -> None:
        self.start_button.configure(state=tkinter.DISABLED)
        self.stop_button.configure(state=tkinter.NORMAL)
        self.backend.start_request()

    def stop(self) -> None:
        self.stop_button.configure(state=tkinter.DISABLED)
        self.start_button.configure(state=tkinter.NORMAL)
        self.backend.stop_request()
