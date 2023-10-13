#!/usr/bin/env python3
# Author: Daniel Mohr
# Date: 2013-05-13, 2014-07-22

__digital_controller_server_date__ = "2014-07-22"
__digital_controller_server_version__ = __digital_controller_server_date__

import os
import re
import sys
import csv
import time
import errno
import random
import signal
import socket
import struct
import tempfile
import argparse
import threading
import socketserver
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, List

from plc.plc_tools import server_base
from plc.plc_tools import plc_socket_communication
from plc.plc_tools.plclogclasses import QueuedWatchedFileHandler


class controller_class(server_base.controller_class):
    """controller_class

    This class is for communicating to a device. This means
    setvalues are required by the user and will be set in some
    intervals. The actualvalues are the actualvalues which were
    set before.

    Author: Daniel Mohr
    Date: 2012-09-30
    """

    def myinit(self, A: str, B: str, C: str, D: str, simulate: bool = False) -> None:
        self.simulate = simulate
        self.shake_dispenser_lock = threading.Lock()
        self.write_to_device_lock = threading.Lock()
        self.actualvaluelock.acquire()  # lock for running
        self.actualvalue: Dict[str, Any] = {}
        if A is not None:
            self.actualvalue["A"] = self.str2boolarray(A)
        else:
            self.actualvalue["A"] = 8 * [False]
        if B is not None:
            self.actualvalue["B"] = self.str2boolarray(B)
        else:
            self.actualvalue["B"] = 8 * [False]
        if C is not None:
            self.actualvalue["C"] = self.str2boolarray(C)
        else:
            self.actualvalue["C"] = 8 * [False]
        if D is not None:
            self.actualvalue["D"] = self.str2boolarray(D)
        else:
            self.actualvalue["D"] = 8 * [False]
        self.actualvalue["dispenser"] = {
            "n": None,
            "ton": None,
            "shake": False,
            "port": None,
            "channel": None,
            "toff": None,
        }
        self.setpointlock.acquire()  # lock for running
        self.setpoint = self.actualvalue.copy()
        self.setpointlock.release()  # release the lock
        self.actualvalue = {
            "A": 8 * [None],
            "B": 8 * [None],
            "dispenser": {"n": None, "ton": None, "shake": False, "port": None, "channel": None, "toff": None},
            "C": 8 * [None],
            "D": 8 * [None],
        }
        self.actualvaluelock.release()  # release the lock

    def set_actualvalue_to_the_device(self) -> None:
        # will set the actualvalue to the device
        self.set_actualvalue_to_the_device_lock.acquire()  # lock to write data
        # write actualvalue to the device
        self.actualvaluelock.acquire()  # lock to get new settings
        actualvalue = self.actualvalue.copy()
        self.actualvaluelock.release()  # release the lock
        s = []
        self.setpointlock.acquire()  # lock to get new settings
        for i in ["A", "B", "C", "D"]:
            if actualvalue[i] != self.setpoint[i]:
                v = self.setpoint[i][:]  # copy the values, not the adress
                actualvalue[i][:] = v
                s += ["@%s%02X" % (i, self.boolarray2int(v))]
        self.setpointlock.release()  # release the lock
        # write to device
        self.write_to_device(s)

        self.communication_problem: int
        if self.communication_problem == -1:
            self.communication_problem = 0
            self.log.warning("write everything to device")
            # try it again
            s = []
            for i in ["A", "B", "C", "D"]:
                s += ["@%s%02X" % (i, self.boolarray2int(actualvalue[i][:]))]
            self.write_to_device(s)
        self.actualvaluelock.acquire()  # lock to get new settings
        self.actualvalue = actualvalue
        self.actualvaluelock.release()  # release the lock
        self.shake_dispenser()
        self.set_actualvalue_to_the_device_lock.release()  # release the lock

    def shake_dispenser(self) -> None:
        # self.log.debug("shake_dispenser_lock")
        self.shake_dispenser_lock.acquire()  # lock to set and/or shake dispenser
        self.setpointlock.acquire()  # lock to get new settings
        self.actualvaluelock.acquire()  # lock to get new settings
        if self.actualvalue["dispenser"] != self.setpoint["dispenser"]:
            # self.log.debug("start shake")
            self.actualvalue["dispenser"]["n"] = self.setpoint["dispenser"]["n"]
            self.actualvalue["dispenser"]["ton"] = self.setpoint["dispenser"]["ton"]
            self.actualvalue["dispenser"]["port"] = self.setpoint["dispenser"]["port"]
            self.actualvalue["dispenser"]["channel"] = self.setpoint["dispenser"]["channel"]
            self.actualvalue["dispenser"]["toff"] = self.setpoint["dispenser"]["toff"]
        if (
            self.setpoint["dispenser"]["shake"]
            and (self.actualvalue["dispenser"]["n"] is not None)
            and (self.actualvalue["dispenser"]["ton"] is not None)
            and (self.actualvalue["dispenser"]["port"] is not None)
            and (self.actualvalue["dispenser"]["channel"] is not None)
            and (self.actualvalue["dispenser"]["toff"] is not None)
        ):
            self.log.debug(
                "shake with %d %f %f on %s %d"
                % (
                    self.actualvalue["dispenser"]["n"],
                    self.actualvalue["dispenser"]["ton"],
                    self.actualvalue["dispenser"]["toff"],
                    self.actualvalue["dispenser"]["port"],
                    self.actualvalue["dispenser"]["channel"],
                )
            )
            self.setpoint["dispenser"]["shake"] = False
            self.actualvalue["dispenser"]["shake"] = True
            # t0 = time.time()
            for i in range(self.actualvalue["dispenser"]["n"]):
                t1 = time.time()
                self.actualvalue[self.actualvalue["dispenser"]["port"]][
                    self.actualvalue["dispenser"]["channel"]
                ] = True  # ON
                s = [
                    "@%s%02X"
                    % (
                        self.actualvalue["dispenser"]["port"],
                        self.boolarray2int(self.actualvalue[self.actualvalue["dispenser"]["port"]]),
                    )
                ]
                self.write_to_device(s)
                t = self.actualvalue["dispenser"]["ton"] - (time.time() - t1)
                if t > 0:
                    time.sleep(t)
                t2 = time.time()
                self.actualvalue[self.actualvalue["dispenser"]["port"]][
                    self.actualvalue["dispenser"]["channel"]
                ] = False  # OFF
                s = [
                    "@%s%02X"
                    % (
                        self.actualvalue["dispenser"]["port"],
                        self.boolarray2int(self.actualvalue[self.actualvalue["dispenser"]["port"]]),
                    )
                ]
                self.write_to_device(s)
                t = self.actualvalue["dispenser"]["toff"] - (time.time() - t2)
                if t > 0:
                    time.sleep(t)
            self.actualvalue[self.actualvalue["dispenser"]["port"]][
                self.actualvalue["dispenser"]["channel"]
            ] = False  # OFF
            s = [
                "@%s%02X"
                % (
                    self.actualvalue["dispenser"]["port"],
                    self.boolarray2int(self.actualvalue[self.actualvalue["dispenser"]["port"]]),
                )
            ]
            self.write_to_device(s)
            self.actualvalue["dispenser"]["shake"] = False
            # self.log.debug("stop shake")
        # self.log.debug("shake_dispenser_lock.release")
        self.actualvaluelock.release()  # release the lock
        self.setpointlock.release()  # release the lock
        self.shake_dispenser_lock.release()  # release the lock

    def wrd(self, data: str) -> int | None:
        data_by = data.encode() if data is not None else b""
        return self.device.write(data_by)

    def write_to_device(self, s: List[str]) -> None:
        if len(s) == 0:
            return
        if self.device is None or self.devicename == "":
            if self.simulate:
                self.log.warning("no device given; can't write to device; will simulate some delay!")
                time.sleep(random.randint(240, 1000) / 10000.0)
            else:
                self.log.warning("no device given; can't write to device!")
            self.log.debug("out: %s" % "".join(s))
            return
        self.write_to_device_lock.acquire()  # lock

        self.deviceopen: bool
        if not self.deviceopen:
            self.device.port = self.devicename
            self.device.open()
            self.deviceopen = True
        for i in range(len(s)):
            self.wrd(s[i])
            self.device.flush()
            r = self.device.read(2)
            t = time.time()
            if r != "Qy":
                self.log.warning("communication problem with device %s" % self.devicename)
                self.communication_problem += 1
                if self.communication_problem >= 3:
                    self.log.warning("%d communication problems; will restart the device" % self.communication_problem)
                    # self.device.flushInput()
                    # self.device.flushOutput()
                    self.device.flush()
                    self.device.close()
                    self.device.open()
                    self.communication_problem = -1
            else:
                self.datalog.debug("%f SENDRECEIVE: %s%s" % (t, s[i], r))
        self.write_to_device_lock.release()  # release the lock

    def set_setpoint_human_readable(self, port: str, channel: str | int, v=False) -> None:
        if (port is not None) and (channel is not None):
            self.log.debug("set port %s channel %s to %s" % (port, channel, v))
            self.setpointlock.acquire()  # lock to set
            self.setpoint[port][channel] = v
            self.setpointlock.release()  # release the lock

    def set_setpoint_int(self, _v: str):
        v = _v.encode("utf-8")
        self.setpointlock.acquire()  # lock to set
        self.setpoint["A"] = self.int2boolarray(struct.unpack("B", v[0])[0])  # type: ignore
        self.setpoint["B"] = self.int2boolarray(struct.unpack("B", v[1])[0])  # type: ignore
        self.setpoint["C"] = self.int2boolarray(struct.unpack("B", v[2])[0])  # type: ignore
        self.setpoint["D"] = self.int2boolarray(struct.unpack("B", v[3])[0])  # type: ignore
        self.setpointlock.release()  # release the lock


controller: controller_class


class ThreadedTCPRequestHandler(
    socketserver.BaseRequestHandler, plc_socket_communication.tools_for_socket_communication
):
    def handle(self) -> None:
        global controller
        self.send_data_to_socket_lock = threading.Lock()
        bufsize = 4096  # read/receive Bytes at once
        controller.log.debug(f"Starting connection to {self.client_address[0],}:{self.client_address[1]}")
        data = ""
        while controller.running:
            self.request.settimeout(1)
            # get some data
            d = ""
            try:
                d = bytes(self.request.recv(bufsize)).decode("utf-8")
                if not d:
                    break
            except Exception:
                pass
            # analyse data
            response: bytearray = bytearray()
            if len(d) > 0:
                data += d
                found_something = True
            else:
                found_something = False
            while found_something:
                found_something = False
                if (len(data) >= 2) and (data[0].lower() == "p"):
                    # packed data; all settings at once
                    found_something = True
                    [data, v] = self.receive_data_from_socket2(self.request, bufsize, data[2:])
                    controller.set_setpoint(s=v)
                elif (len(data) >= 4) and (data[0:4].lower() == "!w2d"):
                    # trigger writing setvalues to the external device
                    found_something = True
                    controller.set_actualvalue_to_the_device()
                    data = data[4:]
                elif (len(data) >= 6) and (data[0:6].lower() == "getact"):
                    # sends the actual values back
                    found_something = True
                    data = data[6:]
                    response.extend(self.create_send_format(controller.get_actualvalue()))
                elif (len(data) >= 5) and (data[0].lower() == "s"):
                    found_something = True
                    controller.set_setpoint_int(data[1:5])
                    data = data[5:]
                elif (len(data) >= 9) and (data[0].lower() == "a"):
                    # A00000000
                    found_something = True
                    for i in range(8):
                        if data[1 + i] == "1":
                            controller.set_setpoint_human_readable(port="A", channel=i, v=True)
                        else:
                            controller.set_setpoint_human_readable(port="A", channel=i, v=False)
                    data = data[9:]
                elif (len(data) >= 9) and (data[0].lower() == "b"):
                    # B00000000
                    found_something = True
                    for i in range(8):
                        if data[1 + i] == "1":
                            controller.set_setpoint_human_readable("B", i, True)
                        else:
                            controller.set_setpoint_human_readable("B", i, False)
                    data = data[9:]
                elif (len(data) >= 9) and (data[0].lower() == "c"):
                    # C00000000
                    found_something = True
                    for i in range(8):
                        if data[1 + i] == "1":
                            controller.set_setpoint_human_readable("C", i, True)
                        else:
                            controller.set_setpoint_human_readable("C", i, False)
                    data = data[9:]
                elif (len(data) >= 9) and (data[0].lower() == "d"):
                    # D00000000
                    found_something = True
                    for i in range(8):
                        if data[1 + i] == "1":
                            controller.set_setpoint_human_readable("D", i, True)
                        else:
                            controller.set_setpoint_human_readable("D", i, False)
                    data = data[9:]
                elif (len(data) >= 20) and (data[0:10].lower() == "_dispenser"):
                    found_something = True
                    # _dispenser00111222
                    controller.set_setpoint_human_readable("dispenser", "shake", False)
                    controller.set_setpoint_human_readable("dispenser", "port", bool(data[10]))
                    controller.set_setpoint_human_readable("dispenser", "channel", bool(int(data[11])))
                    controller.set_setpoint_human_readable("dispenser", "n", bool(int(data[12:14])))
                    controller.set_setpoint_human_readable("dispenser", "ton", bool(int(data[14:17]) / 1000))
                    controller.set_setpoint_human_readable("dispenser", "toff", bool(int(data[17:20]) / 1000))
                    data = data[20:]
                elif (len(data) >= 10) and (data[0:10].lower() == "!dispenser"):
                    # !dispenser
                    # do the shake
                    found_something = True
                    if (
                        controller.actualvalue["dispenser"]["n"] is not None
                        and controller.actualvalue["dispenser"]["ton"] is not None
                        and controller.actualvalue["dispenser"]["port"] is not None
                        and controller.actualvalue["dispenser"]["channel"] is not None
                        and controller.actualvalue["dispenser"]["toff"] is not None
                    ):
                        controller.set_setpoint_human_readable("dispenser", "shake", True)
                    data = data[10:]
                elif (len(data) >= 12) and (data[0:9].lower() == "timedelay"):
                    found_something = True
                    v = int(data[9:12])
                    controller.log.debug("set timedelay/updatedelay to %d milliseconds" % v)
                    controller.updatedelay = v / 1000.0
                    data = data[12:]
                elif (len(data) >= 4) and (data[0:4].lower() == "quit"):
                    found_something = True
                    response.extend(b"quitting")
                    controller.log.info("Quitting")
                    data = data[4:]
                    controller.running = False
                    self.server.shutdown()
                elif (len(data) >= 7) and (data[0:7].lower() == "version"):
                    found_something = True
                    a = f"digital_controller_server Version: {__digital_controller_server_version__}"
                    response.extend(a.encode("utf-8"))
                    controller.log.debug(a)
                    data = data[7:]
                if len(data) == 0:
                    break
            time.sleep(random.randint(1, 100) / 1000.0)
            if len(response) > 0:
                self.send_data_to_socket(self.request, response)

    def send_data_to_socket(self, s: socket.socket, msg: bytes) -> None:
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = s.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def finish(self):
        global controller
        controller.log.debug("stop connection to %s:%s" % (self.client_address[0], self.client_address[1]))
        try:
            self.request.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def main():
    global controller
    # command line parameter
    help = ""
    help += "Over the given port on the given address a socket communication is "
    help += "lisening with the following commands: (This is a prefix-code. Upper or lower letters do not matter.)\n"
    help += "  p[pickle data] : Set all setpoints at once. You have all setpoints in one\n"
    help += "                   object:\n"
    help += "                   a = {'A': 8*[False], 'B': 8*[False], 'dispenser': {'n': False, 'ton': False, 'shake': False, 'port': False, 'channel': False, 'toff': False}, 'C': 8*[False], 'D': 8*[False]}\n"
    help += "                   Now you can generate the [pickle data]==v by:\n"
    help += "                   s = pickle.dumps(a,-1); v='%d %s' % (len(s),s)\n"
    help += "  s[unsigned char][unsigned char][unsigned char][unsigned char] :\n"
    help += "                   set the 4 ports to the On/Off values on the ports\n"
    help += "  [A|B|C|D][0|1][0|1][0|1][0|1][0|1][0|1][0|1][0|1] :\n"
    help += "                   set the channels on the port [A|B|C|D] to On/Off\n"
    help += "  _dispenserPC00111222 : Choose the values for the dispenser shake. P is the\n"
    help += "                   port [A|B|C|D] and C is the channel [0|1|2|3|4|5|6|7].\n"
    help += "                   00 are 2 digits for the number of shakes; 111 are 3\n"
    help += "                   digits for the T_on time in milliseconds; 222 are 3\n"
    help += "                   digits for the T_off time in milliseconds.\n"
    help += "  !dispenser : shake the dispenser with the choosen values\n"
    help += "  !w2d : trigger writing setvalues to the external device\n"
    help += "  getact : sends the actual values back as [pickle data]\n"
    help += "  timedelay000 : set the time between 2 actions to 000 milliseconds.\n"
    help += "  quit : quit the server\n"
    help += "  version : response the version of the server\n"
    parser = argparse.ArgumentParser(
        description="digital_controller_server is a socket server to control the digital controller on an serial interface. On start every settings are assumed to 0 or the given values and set to the device. A friendly kill (SIGTERM) should be possible.",
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s"
        % (__digital_controller_server_date__, help),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # device /dev/DOCU0001
    # IP to listen
    # port to listen
    # logfile /data/logs/DOCU0001.log
    # delay time between 2 actions
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
        default=os.path.join(tempfile.gettempdir(), "digital_controller.log"),
        type=str,
        required=False,
        dest="logfile",
        help="Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s"
        % os.path.join(tempfile.gettempdir(), "digital_controller.log"),
        metavar="f",
    )
    parser.add_argument(
        "-datalogfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "digital_controller.data"),
        type=str,
        required=False,
        dest="datalogfile",
        help="Set the datalogfile to f. Only the measurements will be logged here. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s"
        % os.path.join(tempfile.gettempdir(), "digital_controller.data"),
        metavar="f",
    )
    parser.add_argument(
        "-runfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "digital_controller.pids"),
        type=str,
        required=False,
        dest="runfile",
        help='Set the runfile to f. If an other process is running with a given pid and writing to the same device, the program will not start. Setting f="" will disable this function. default: %s'
        % os.path.join(tempfile.gettempdir(), "digital_controller.pids"),
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
        default=15112,
        type=int,
        required=False,
        dest="port",
        help="Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15112",
        metavar="p",
    )
    parser.add_argument(
        "-timedelay",
        nargs=1,
        default=0.05,
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
        "-A",
        nargs=1,
        default="00000000",
        type=str,
        required=False,
        dest="A",
        help='Set the default values for the digital controller port A; "0" for channel off and "1" for channel on; "10000000" means only channel 0 to ON. default: d = "00000000"',
        metavar="d",
    )
    parser.add_argument(
        "-B",
        nargs=1,
        default="00000000",
        type=str,
        required=False,
        dest="B",
        help='Set the default values for the digital controller port B; "0" for channel off and "1" for channel on; "10000000" means only channel 0 to ON. default: d = "00000000"',
        metavar="d",
    )
    parser.add_argument(
        "-C",
        nargs=1,
        default="00000000",
        type=str,
        required=False,
        dest="C",
        help='Set the default values for the digital controller port C; "0" for channel off and "1" for channel on; "10000000" means only channel 0 to ON. default: d = "00000000"',
        metavar="d",
    )
    parser.add_argument(
        "-D",
        nargs=1,
        default="00000000",
        type=str,
        required=False,
        dest="D",
        help='Set the default values for the digital controller port D; "0" for channel off and "1" for channel on; "10000000" means only channel 0 to ON. default: d = "00000000"',
        metavar="d",
    )
    parser.add_argument(
        "-debug",
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
        help="By specifying this flag a random sleep simulates the communication to the device.",
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
    if not isinstance(args.A, str):
        args.A = args.A[0]
    if not isinstance(args.B, str):
        args.B = args.B[0]
    if not isinstance(args.C, str):
        args.C = args.C[0]
    if not isinstance(args.D, str):
        args.D = args.D[0]
    if not isinstance(args.debug, int):
        args.debug = args.debug[0]
    if not isinstance(args.simulate, bool):
        args.simulate = args.simulate[0]
    # logging
    log = logging.getLogger("dcs")
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
    log.info("Started")
    log.info(f"Logging to '{args.logfile}' and data to '{args.datalogfile}'")

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
                if (Path("/proc") / str(os.getpid())).exists():  # checking /proc available
                    ng = Path("/proc") / str(int(row[0]))
                    if ng.exists():  # check if other pid is running
                        with (ng / "cmdline").open("rt") as ff:
                            cmdline = ff.read(1024 * 1024)
                        f.close()
                        if re.findall(__file__, cmdline):
                            rr = True
                            log.debug(f"Process {int(row[0])} is running (proc)")
                else:  # /proc is not available; try kill, which only works on posix systems
                    try:
                        os.kill(int(row[0]), 0)
                    except OSError as err:
                        if err.errno == errno.ESRCH:
                            pass  # not running
                        elif err.errno == errno.EPERM:
                            pass  # no permission to signal this process; assuming it is another kind of process
                        else:
                            raise  # unknown error
                    else:  # other pid is running
                        rr = True  # assuming this is the same kind of process
                        log.debug(f"Process {int(row[0])} is running (kill)")
                if rr and row[1] != args.device:  # checking if same device
                    runinfo += [[row[0], row[1]]]
                elif rr:
                    r = True
            if r:
                log.error("Other process is running. Exiting.")
                sys.exit(1)
    f = open(args.runfile, "w")
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
            time.sleep(0.024)  # time for first communication with device
            sys.exit(0)
        log.removeHandler(ch)
        # threads in the default process are dead
        # in particular this means QueuedWatchedFileHandler is not working anymore
        fh.startloopthreadagain()
        fhd.startloopthreadagain()
        log.info("removed console log handler")
    else:
        log.info("due to debug=1 will _not_ go to background (fork)")

    # controller = controller_class(log=log,device=args.device,updatedelay=args.timedelay,A=args.A,B=args.B,C=args.C,D=args.D)
    controller = controller_class(
        log, datalog, args.device, args.timedelay, args.A, args.B, args.C, args.D, args.simulate
    )
    try:
        server = ThreadedTCPServer((args.ip, args.port), ThreadedTCPRequestHandler)
    except socket.error:
        log.exception(f"Probably port {args.port} is in use already")
        raise

    def shutdown(signum, frame):
        global controller
        controller.log.info(f"Got signal {signum}")
        controller.log.debug(f"Number of threads: {threading.activeCount()}")
        controller.log.info("Will exit the program")
        controller.shutdown()

    signal.signal(signal.SIGTERM, shutdown)

    ip, port = server.server_address
    log.info("listen at %s:%d" % (ip, port))
    # start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    while controller.running:
        time.sleep(1)  # it takes at least 1 second to exit
    log.debug("exit")
    time.sleep(0.001)
    fhd.flush()
    fhd.close()
    fh.flush()
    fh.close()
    if args.debug != 0:
        ch.flush()
        ch.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
