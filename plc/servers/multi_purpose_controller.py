#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2014 Daniel Mohr
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

__multi_purpose_controller_server_date__ = "2023-10-23"
__multi_purpose_controller_server_version__ = __multi_purpose_controller_server_date__

import re
import os
import csv
import sys
import time
import errno
import struct
import socket
import pickle
import signal
import random
import logging
import argparse
import tempfile
import threading
import socketserver
from pathlib import Path
from typing import NoReturn, Dict, Any, Tuple

from ..plc_tools import server_base
from ..plc_tools.conversion import volt2dac, adcstring2volt
from ..plc_tools.plclogclasses import QueuedWatchedFileHandler
from ..plc_tools.plc_socket_communication import socket_communication


def get_s(actualvalue):
    s = ""
    st = list("0000")
    if actualvalue["DO"][3]:
        st[2] = "1"
    if actualvalue["DO"][2]:
        st[3] = "1"
    s += "%X" % int("".join(st), 2)
    st = list("0000")
    if actualvalue["DO"][1]:
        st[0] = "1"
    if actualvalue["DO"][0]:
        st[1] = "1"
    if actualvalue["R"][1]:
        st[2] = "1"
    if actualvalue["R"][0]:
        st[3] = "1"
    s += "%X" % int("".join(st), 2)
    st = list("0000")
    if actualvalue["U15"]:
        st[1] = "1"
    if actualvalue["U05"]:
        st[2] = "1"
    if actualvalue["U24"]:
        st[3] = "1"
    s += "%X" % int("".join(st), 2)
    return s


class controller_class(server_base.controller_class):
    """
    controller_class

    This class is for communicating to a device. This means
    setvalues are required by the user and will be set in some
    intervals. The actualvalues are the actualvalues which were
    set before.
    """

    def myinit(self, DO: str, R: str, U05: str, U15: str, U24: str, DAC: str, simulate: bool = False) -> None:
        self.simulate: bool = simulate
        self.actualvaluelock.acquire()  # lock for running
        self.actualvalue: Dict[str, Any] = {
            "DO": 4 * [None],
            "R": 2 * [None],
            "U05": None,
            "U15": None,
            "U24": None,
            "DAC": 4 * [0.0],
            "DI": 4 * [None],
            "ADC": 8 * [0],
        }
        self.actualvaluelock.release()  # release the lock
        self.setpointlock.acquire()  # lock for running
        self.setpoint: Dict[str, Any] = {
            "DO": 4 * [False],
            "R": 2 * [False],
            "U05": False,
            "U15": False,
            "U24": False,
            "DAC": 4 * [0.00015259021896696368],
        }
        if DO is not None:
            self.setpoint["DO"] = self.str2boolarray(DO)
        if R is not None:
            self.setpoint["R"] = self.str2boolarray(R)
        if U05 is not None:
            self.setpoint["U05"] = self.str2bool(U05)
        if U15 is not None:
            self.setpoint["U15"] = self.str2bool(U15)
        if U24 is not None:
            self.setpoint["U24"] = self.str2bool(U24)
        if DAC is not None:
            self.setpoint["DAC"] = self.str2float(DAC)
            for i in range(4):
                self.setpoint["DAC"][i] = min(max(-10.0, self.setpoint["DAC"][i]), +10.0)
        self.setpointlock.release()  # release the lock

    def __write(self, _data: str) -> int:
        data = _data.encode("utf-8")
        rt = self.device.write(data)
        return rt if rt is not None else 0

    def __read(self, size: int) -> str:
        return self.device.read(size).decode("utf-8")

    def set_actualvalue_to_the_device(self) -> None:
        if not self.simulate:
            if self.device is None or self.devicename == "":
                self.log.error("No device")
                raise RuntimeError("No device")
        # will set the actualvalue to the device
        self.set_actualvalue_to_the_device_lock.acquire()  # lock to write data
        # write actualvalue to the device
        self.actualvaluelock.acquire()  # lock to get new settings
        actualvalue = self.actualvalue.copy()
        self.actualvaluelock.release()  # release the lock
        self.setpointlock.acquire()  # lock to get new settings
        actualvalue["DO"][:] = self.setpoint["DO"][:]
        actualvalue["R"][:] = self.setpoint["R"][:]
        actualvalue["U05"] = self.setpoint["U05"]
        actualvalue["U15"] = self.setpoint["U15"]
        actualvalue["U24"] = self.setpoint["U24"]
        actualvalue["DAC"][0:4] = self.setpoint["DAC"][0:4]
        self.setpointlock.release()  # release the lock
        sendreceive = ""
        s: str = "@"
        if self.simulate:
            sendreceive += s
            sendreceive += "Q"
        else:
            self.deviceopen: bool
            if not self.deviceopen:
                self.device.port = self.devicename
                self.device.open()
                self.deviceopen = True
            self.__write(s)
            self.device.flush()
            sendreceive += s
            r = self.__read(1)
            sendreceive += r
            if r != "Q":
                self.log.warning("communication problem with device %s" % self.devicename)

        s = get_s(actualvalue)
        if self.simulate:
            sendreceive += s
            sendreceive += "D"
        else:
            self.__write(s)
            self.device.flush()
            sendreceive += s
            r = self.__read(1)
            sendreceive += r
            if r != "D":
                self.log.warning("communication problem with device %s" % self.devicename)

        s = ""
        for i in range(4):
            v = volt2dac(actualvalue["DAC"][i])
            s += "%04X" % v
        if self.simulate:
            sendreceive += s
            sendreceive += "A"
        else:
            self.__write(s)
            self.device.flush()
            sendreceive += s
            r = self.__read(1)
            sendreceive += r
            if r != "A":
                self.log.warning("communication problem with device %s" % self.devicename)

        if self.simulate:
            # @Q000D8000800080008000A0A03091E20B920BB0000FFFE20CC20D4IFC
            r = ""
            for i in range(32):
                r += "%X" % random.randint(0, 15)
            for i in range(8):
                actualvalue["ADC"][i] = adcstring2volt(r[i * 4 + 0 : i * 4 + 4])
            sendreceive += "I"
            r = ""
            for i in range(2):
                r += "%X" % random.randint(0, 15)
            sendreceive += r
            s = "{0:04b}".format(int(r[1], 16))
            for i in range(4):
                if s[i] == "1":
                    actualvalue["DI"][3 - i] = True
                else:
                    actualvalue["DI"][3 - i] = False
        #     else:  # if no device and not simulate????
        #         sendreceive += "********************************"
        #         sendreceive += "I"
        #         sendreceive += "**"
        else:
            r = self.__read(32)  # ADC
            self.log.info(f"Readed: {r}")
            sendreceive += r
            for i in range(8):
                actualvalue["ADC"][i] = adcstring2volt(r[i * 4 + 0 : i * 4 + 4])
            r = self.__read(1)
            sendreceive += r
            if r != "I":
                self.log.warning("communication problem with device %s" % self.devicename)
            r = self.__read(2)  # DI
            sendreceive += r
            s = "{0:04b}".format(int(r[1], 16))
            for i in range(4):
                if s[i] == "1":
                    actualvalue["DI"][3 - i] = True
                else:
                    actualvalue["DI"][3 - i] = False

        t = time.time()
        self.actualvaluelock.acquire()  # lock to get new settings
        self.actualvalue = actualvalue
        self.actualvaluelock.release()  # release the lock
        if self.simulate:
            # self.log.debug(f"SENDRECEIVE (simulated): {sendreceive}")
            pass
        else:
            # self.log.debug(f"SENDRECEIVE: {sendreceive}")
            self.datalog.debug(f"{t} SENDRECEIVE: {sendreceive}")
        self.set_actualvalue_to_the_device_lock.release()  # release the lock

    def set_setpoint(self, s=None) -> None:
        if s is not None:
            for i in range(4):
                s["DAC"][i] = min(max(-10.0, s["DAC"][i]), +10.0)
            self.setpointlock.acquire()  # lock to set
            self.setpoint = s.copy()
            self.setpointlock.release()  # release the lock


controller: controller_class


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler, socket_communication):
    def handle(self) -> None:
        global controller
        self.send_data_to_socket_lock = threading.Lock()
        bufsize = 4096  # read/receive Bytes at once
        controller.log.debug("start connection to %s:%s" % (self.client_address[0], self.client_address[1]))
        data = b""
        self.request: socket.socket
        while controller.running:
            # self.request.settimeout(10)
            # get some data
            buffer = b""
            try:
                buffer = self.request.recv(bufsize)
                if not buffer:
                    break
            except Exception:
                controller.log.exception("Error in receiving data from plc")
            # analyse data
            if len(buffer) > 0:
                data += buffer
                found_something = True
                # try:
                #     controller.log.debug(f"From plc: {buffer.decode('utf-8')}")
                # except UnicodeDecodeError:
                #     controller.log.debug(f"From plc: {len(buffer)} bytes: {buffer!r}")
            else:
                found_something = False
            while found_something:
                # controller.log.debug("Enter cycle")
                found_something = False
                if (len(data) >= 2) and (data[0:1].lower() == b"p"):
                    # controller.log.debug("Found packed data, will get more")
                    # packed data; all settings at once
                    found_something = True
                    [data, v] = self.receive_data_from_socket2(self.request, bufsize=bufsize, data=data[2:])
                    controller.set_setpoint(s=v)
                elif (len(data) >= 4) and (data[0:4].lower() == b"!w2d"):
                    # controller.log.debug("Write to device requested")
                    # trigger writing setvalues to the external device
                    found_something = True
                    controller.set_actualvalue_to_the_device()
                    data = data[4:]
                elif (len(data) >= 6) and (data[0:6].lower() == b"getact"):
                    # sends the actual values back
                    found_something = True
                    data = data[6:]
                    # controller.log.debug(f"Sending actualvalues, data len: {len(data)}")
                    self.send_data_to_socket(self.request, self.create_send_format(controller.get_actualvalue()))
                elif (len(data) >= 12) and (data[0:9].lower() == b"timedelay"):
                    found_something = True
                    v = int(data[9:12])
                    controller.log.debug("set timedelay/updatedelay to %d milliseconds" % v)
                    controller.updatedelay = v / 1000.0
                    data = data[12:]
                elif (len(data) >= 4) and (data[0:4].lower() == b"quit"):
                    controller.log.debug("Quitting requested")
                    found_something = True
                    a = b"quitting"
                    self.send_data_to_socket(self.request, a)
                    controller.log.info(a)
                    data = data[4:]
                    controller.running = False
                    self.server.shutdown()
                    controller.shutdown()
                elif (len(data) >= 7) and (data[0:7].lower() == b"version"):
                    controller.log.debug("Version requested")
                    found_something = True
                    npr = "multi_purpose_controller_server Version: %s" % __multi_purpose_controller_server_version__
                    a = npr.encode("utf-8")
                    self.send_data_to_socket(self.request, a)
                    controller.log.debug(a)
                    data = data[7:]
                else:
                    pass
                    # try:
                    #     controller.log.debug(f"Nothing was found in {data.decode('utf-8')}")
                    # except UnicodeDecodeError:
                    #     controller.log.debug(f"Nothing was found in {data!r}")
                if len(data) == 0:
                    break
            # time.sleep(random.randint(1, 100) / 1000.0)

    def send_data_to_socket(self, s: socket.socket, msg: bytes) -> None:
        # try:
        #     controller.log.debug(f"To plc: {msg.decode('utf-8')}")
        # except UnicodeDecodeError:
        #     controller.log.debug(f"To plc: {len(msg)} bytes: {msg!r}")
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = s.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive_data_from_socket2(self, s: socket.socket, bufsize: int = 4096, data: bytes = b"") -> Tuple[bytes, Any]:
        expected_length = 4
        while len(data) < expected_length:
            data += s.recv(bufsize)
        expected_length += struct.unpack("!i", (data[0:4]))[0]
        while len(data) < expected_length:
            data += s.recv(bufsize)
        v = pickle.loads((data[4:expected_length]))
        data = data[expected_length:]
        return (data, v)

    def create_send_format(self, data: Any) -> bytes:
        s: bytes = pickle.dumps(data, -1)
        asd = bytearray(struct.pack(b"!i", len(s)))
        asd.extend(s)
        return bytes(asd)

    def finish(self):
        controller.log.debug("stop connection to %s:%s" % (self.client_address[0], self.client_address[1]))
        try:
            self.request.shutdown(socket.SHUT_RDWR)
        except Exception:
            controller.log.exception("Error in shutting down")
            pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def main() -> NoReturn:
    global controller
    # command line parameter
    help = ""
    help += "Over the given port on the given address a socket communication is "
    help += "lisening with the following commands: (This is a prefix-code. Upper or lower letters do not matter.)\n"
    help += "  p[pickle data] : Set all setpoints at once. You have all setpoints in one\n"
    help += "                   object:\n"
    help += "                   a = {'DO':4*[False],'R':2*[False],'U05':False,'U15':False,'U24':False,'DAC':4*[0.0]}\n"
    help += "                   Now you can generate the [pickle data]==v by:\n"
    help += "                   s = pickle.dumps(a,-1); v='%d %s' % (len(s),s)\n"
    help += "  !w2d : trigger writing setvalues to the external device\n"
    help += "  getact : sends the actual values back as [pickle data]\n"
    help += "  timedelay000 : set the time between 2 actions to 000 milliseconds.\n"
    help += "  quit : quit the server\n"
    help += "  version : response the version of the server\n"
    parser = argparse.ArgumentParser(
        description="multi_purpose_controller_server is a socket server to control the multi purpose controller on an serial interface. On start every settings are assumed to 0 or the given values and set to the device. A friendly kill (SIGTERM) should be possible.",
        epilog="Author: Daniel Mohr, Egor Perevoshchikov\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s"
        % (__multi_purpose_controller_server_date__, help),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-device",
        nargs=1,
        default="",
        type=str,
        required=False,
        dest="device",
        help="Set the external device dev to communicate with the box.",
        metavar="dev",
    )
    parser.add_argument(
        "-logfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "multi_purpose_controller.log"),
        type=str,
        required=False,
        dest="logfile",
        help="Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s"
        % os.path.join(tempfile.gettempdir(), "multi_purpose_controller.log"),
        metavar="f",
    )
    parser.add_argument(
        "-datalogfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "multi_purpose_controller.data"),
        type=str,
        required=False,
        dest="datalogfile",
        help="Set the datalogfile to f. Only the measurements will be logged here. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s"
        % os.path.join(tempfile.gettempdir(), "multi_purpose_controller.data"),
        metavar="f",
    )
    parser.add_argument(
        "-runfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "multi_purpose_controller.pids"),
        type=str,
        required=False,
        dest="runfile",
        help='Set the runfile to f. If an other process is running with a given pid and writing to the same device, the program will not start. Setting f="" will disable this function. default: %s'
        % os.path.join(tempfile.gettempdir(), "multi_purpose_controller.pids"),
        metavar="f",
    )
    parser.add_argument(
        "-ip",
        nargs=1,
        default="localhost",
        type=str,
        required=False,
        dest="ip",
        help='Set the IP/host n to listen. If ip == "" the default behavior will be used; typically listen on all possible adresses. default: localhost',
        metavar="n",
    )
    parser.add_argument(
        "-port",
        nargs=1,
        default=15113,
        type=int,
        required=False,
        dest="port",
        help="Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15113",
        metavar="p",
    )
    parser.add_argument(
        "-timedelay",
        nargs=1,
        default=0.062,  # 62 characters with 9600 boud
        type=float,
        required=False,
        dest="timedelay",
        help="Set the time between 2 actions to t seconds. default: t = 0.05",
        metavar="t",
    )
    parser.add_argument(
        "-choosenextport",
        default=False,
        required=False,
        action="store_true",
        dest="choosenextport",
        help="By specifying this flag the next available port after the given one will be choosen. Without this flag a socket.error is raised if the port is not available.",
    )
    parser.add_argument(
        "-DO",
        nargs=1,
        default="0000",
        type=str,
        required=False,
        dest="DO",
        help='Set the default values for the multi purpose controller port DO; "0" for channel off and "1" for channel on; "0001" means only channel 1 to ON. default: d = "0000"',
        metavar="d",
    )
    parser.add_argument(
        "-R",
        nargs=1,
        default="00",
        type=str,
        required=False,
        dest="R",
        help='Set the default values for the multi purpose controller port R; "0" for channel off and "1" for channel on; "01" means only channel 1 to ON. default: d = "00"',
        metavar="d",
    )
    parser.add_argument(
        "-U05",
        nargs=1,
        default="0",
        type=str,
        required=False,
        dest="U05",
        help='Set the default values for the multi purpose controller port U05; "0" for channel off and "1" for channel on. default: d = "0"',
        metavar="d",
    )
    parser.add_argument(
        "-U15",
        nargs=1,
        default="0",
        type=str,
        required=False,
        dest="U15",
        help='Set the default values for the multi purpose controller port U15; "0" for channel off and "1" for channel on. default: d = "0"',
        metavar="d",
    )
    parser.add_argument(
        "-U24",
        nargs=1,
        default="0",
        type=str,
        required=False,
        dest="U24",
        help='Set the default values for the multi purpose controller port U24; "0" for channel off and "1" for channel on. default: d = "0"',
        metavar="d",
    )
    # default="-10,-10,-10,-10",
    parser.add_argument(
        "-DAC",
        nargs=1,
        default="0.00016,0.00016,0.00016,0.00016",
        type=str,
        required=False,
        dest="DAC",
        help='Set the default values for the multi purpose controller port DAC. default: d = "0.00016,0.00016,0.00016,0.00016"',
        metavar="d",
    )
    parser.add_argument(
        "-debug",
        nargs=1,
        default=0,
        type=int,
        required=False,
        dest="debug",
        help="Set debug level. 0 no debug info (default); 1 debug to STDOUT.",
        metavar="debug_level",
    )
    parser.add_argument(
        "-simulate",
        default=False,
        required=False,
        action="store_true",
        dest="simulate",
        help="By specifying this flag simulated values (ADC-values) will be send to a client and a random sleep simulates the communication to the device.",
    )
    args = parser.parse_args()
    if not isinstance(args.device, str):
        args.device = args.device[0]
    if not isinstance(args.logfile, str):
        args.logfile = args.logfile[0]
    if not isinstance(args.datalogfile, str):
        args.datalogfile = args.datalogfile[0]
    if not isinstance(args.runfile, str):
        args.runfile = args.runfile[0]
    if not isinstance(args.ip, str):
        args.ip = args.ip[0]
    if not isinstance(args.port, int):
        args.port = args.port[0]
    if not isinstance(args.timedelay, float):
        args.timedelay = args.timedelay[0]
    if not isinstance(args.choosenextport, bool):
        args.choosenextport = args.choosenextport[0]
    if not isinstance(args.DO, str):
        args.DO = args.DO[0]
    if not isinstance(args.R, str):
        args.R = args.R[0]
    if not isinstance(args.U05, str):
        args.U05 = args.U05[0]
    if not isinstance(args.U15, str):
        args.U15 = args.U15[0]
    if not isinstance(args.U24, str):
        args.U24 = args.U24[0]
    if not isinstance(args.DAC, str):
        args.DAC = args.DAC[0]
    if not isinstance(args.debug, int):
        args.debug = args.debug[0]
    if not isinstance(args.simulate, bool):
        args.simulate = args.simulate[0]
    # logging
    log = logging.getLogger("mpcs")
    log.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    # create file handler
    fh = QueuedWatchedFileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO)  # logging.WARNING = 30
    ch.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    datalog = logging.getLogger("mpcsd")
    datalog.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    # create file handler
    fhd = QueuedWatchedFileHandler(args.datalogfile)
    fhd.setLevel(logging.DEBUG)
    fhd.setFormatter(logging.Formatter("%(message)s"))
    # add the handlers to log
    datalog.addHandler(fhd)
    log.info(
        "start logging in multi_purpose_controller_server: %s"
        % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime())
    )
    log.info('logging to "%s" and data to "%s"' % (args.logfile, args.datalogfile))
    # check runfile
    ori = [os.getpid(), args.device]
    runinfo = [ori]
    runfile = Path(args.runfile)
    if runfile.is_file():
        # file exists, read it
        with runfile.open("r") as f:
            reader = csv.reader(f)
            r = False  # assuming other pid is not running; will be corrected if more information is available
            for row in reader:
                # row[0] should be a pid
                # row[1] should be the device
                rr = False
                if os.path.exists(os.path.join("/proc", "%d" % os.getpid())):  # checking /proc available
                    if os.path.exists(os.path.join("/proc", "%d" % int(row[0]))):  # check if other pid is running
                        ff = open(os.path.join("/proc", "%d" % int(row[0]), "cmdline"), "rt")
                        cmdline = ff.read(1024 * 1024)
                        ff.close()
                        if re.findall(__file__, cmdline):
                            rr = True
                            log.debug("process %d is running (proc)" % int(row[0]))
                else:  # /proc is not available; try kill, which only wirks on posix systems
                    try:
                        os.kill(int(row[0]), 0)
                    except OSError as err:
                        if err.errno == errno.ESRCH:
                            # not running
                            pass
                        elif err.errno == errno.EPERM:
                            # no permission to signal this process; assuming it is another kind of process
                            pass
                        else:
                            # unknown error
                            raise
                    else:  # other pid is running
                        rr = True  # assuming this is the same kind of process
                        log.debug("process %d is running (kill)" % int(row[0]))
                if rr and row[1] != args.device:  # checking iff same device
                    runinfo += [[row[0], row[1]]]
                elif rr:
                    r = True
            if r:
                log.error("other process is running; exit.")
                sys.exit(1)
        with runfile.open("w") as f:
            writer = csv.writer(f)
            for i in range(len(runinfo)):
                writer.writerows([runinfo[i]])
    # go in background if useful
    if args.debug == 0:
        # go in background
        log.info("go to background (fork)")
        newpid = os.fork()
        if newpid > 0:
            log.info("background process pid = %d" % newpid)
            if args.runfile != "":
                nri = [newpid, args.device]
                index = runinfo.index(ori)
                runinfo[index] = nri
                f = open(args.runfile, "w")
                writer = csv.writer(f)
                for i in range(len(runinfo)):
                    writer.writerows([runinfo[i]])
                    f.close()
            time.sleep(0.062)  # time for first communication with device
            sys.exit(0)
        log.removeHandler(ch)
        # threads in the default process are dead
        # in particular this means QueuedWatchedFileHandler is not working anymore
        fh.startloopthreadagain()
        fhd.startloopthreadagain()
        log.info("removed console log handler")
    else:
        log.info("due to debug=1 will _not_ go to background (fork)")
    controller = controller_class(
        log,
        datalog,
        args.device,
        args.timedelay,
        args.DO,
        args.R,
        args.U05,
        args.U15,
        args.U24,
        args.DAC,
        args.simulate,
    )
    try:
        server = ThreadedTCPServer((args.ip, args.port), ThreadedTCPRequestHandler)
    except socket.error:
        log.exception(f"Probably port {args.port} is in use already")
        raise

    ip, port = server.server_address
    log.info("listen at %s:%d" % (ip, port))

    def shutdown(signum, frame) -> None:
        global controller
        controller.log.info("got signal %d" % signum)
        controller.log.debug("number of threads: %d" % threading.activeCount())
        controller.log.info("will exit the program")
        server.shutdown()
        controller.shutdown()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGHUP, shutdown)
    # start a thread with the server -- that thread will then start one
    # more thread for each request
    server.serve_forever()
    # server_thread = threading.Thread(target=server.serve_forever)
    # # Exit the server thread when the main thread terminates
    # server_thread.daemon = True
    # server_thread.start()
    # while controller.running:
    # time.sleep(1)  # it takes at least 1 second to exit
    log.debug("exit")
    # time.sleep(0.001)
    fhd.flush()
    fhd.close()
    fh.flush()
    fh.close()
    if args.debug != 0:
        ch.flush()
        ch.close()
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
