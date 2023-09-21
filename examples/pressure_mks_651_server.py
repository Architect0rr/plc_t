#!/usr/bin/python -O
# Author: Richard Schlitz, Daniel Mohr
# Date: 2013-10-04, 2014-07-22

__mks_651_server_date__ = "2014-07-22"
__mks_651_server_version__ = __mks_651_server_date__

import argparse
import pickle
import csv
import errno
import logging
import logging.handlers
import os
import re
import serial
import signal
import socket
import socketserver
import sys
import tempfile
import threading
import time
from typing import Literal, Dict, List

import plc_tools.server_base
from plc_tools.plclogclasses import QueuedWatchedFileHandler
import plc_tools.plc_socket_communication


class controller_class:
    """controller_class

    This class is for communicating to a device. This means
    setvalues are required by the user and will be set in some
    intervals. The actualvalues are the actualvalues which were
    set before.
    """

    def __init__(self, log: logging.Logger, datalog: logging.Logger, device: str, updatedelay: float = 1):
        global controller
        self.log: logging.Logger = log
        self.datalog: logging.Logger = datalog
        self.devicename: str = device
        self.deviceopen: bool = False
        self.boudrate: int = 9600
        self.databits: Literal[8] = serial.EIGHTBITS
        self.parity: Literal["N"] = serial.PARITY_NONE
        self.stopbits: Literal[1] = serial.STOPBITS_ONE  # serial.STOPBITS_ONE_POINT_FIVE serial.STOPBITS_TWO
        self.readtimeout: int = 1
        self.writetimeout: int = 1
        self.device: serial.Serial = serial.Serial(
            port=None, baudrate=self.boudrate, bytesize=self.databits, parity=self.parity, stopbits=self.stopbits, timeout=self.readtimeout, write_timeout=self.writetimeout
        )
        self.device.port = self.devicename
        self.communication_problem: int = 0
        self.lock: threading.Lock = threading.Lock()
        self.updatelock: threading.Lock = threading.Lock()
        self.set_actualvalue_to_the_device_lock: threading.Lock = threading.Lock()
        self.get_actualvalue_from_the_device_lock: threading.Lock = threading.Lock()
        self.write_to_device_lock: threading.Lock = threading.Lock()
        self.full_scale_values: List[float] = [
            0.1,
            0.2,
            0.5,
            1.0,
            2.0,
            5.0,
            10.0,
            50.0,
            100.0,
            500.0,
            1000.0,
            5000.0,
            10000.0,
            1.3332,
            2.6664,
            13.332,
            133.32,
            1333.2,
            6666.0,
            13332.0,
        ]
        self.unit_list: List[str] = ["00-Torr", "01-mTorr", "02-mbar", "03-ubar", "04-KPa", "05-Pa", "06-cmH2O", "07-inH2O"]
        # 'M' is key, is command/first byte of the answer string from the device
        # 'R37' is the question to get the status of the device -> write R37 -> answer: MXYZ
        # XYZ string is decomposed using the decompose_m_string routine and sets the status of
        # all values in the actualvalue variable with actualvalue[key][0]==None
        # Normal structure of actualvalue is:
        # 'F' is the command to set the value and is the key to answer and data
        # self.actualvalue['F'][0] contains the request to the device to obtain the real value
        # self.actualvalue['F'][1] contains the data returned by the device
        #
        # according to that to write a new 'F' and check whether its value is updated:
        # self.write_to_device(self.actualvalue['F'][1](->data),'F'(->command),self.actualvalue['F'](->question))
        # writes 'F' + data and 'R34' to the device and returns the answer which is 01...07
        self.actualvalue: Dict[str, List[str]] = {
            "M": ["R37", ""],
            "O": ["", ""],  # "O": [None, ""],
            "C": ["", ""],  # "C": [None, ""],
            "H": ["", ""],  # "H": [None, ""],
            "D1": ["", ""],  # "D1": [None, ""],
            "D2": ["", ""],  # "D2": [None, ""],
            "D3": ["", ""],  # "D3": [None, ""],
            "D4": ["", ""],  # "D4": [None, ""],
            "D5": ["", ""],  # "D5": [None, ""],
            "T1": ["R26", ""],
            "T2": ["R27", ""],
            "T3": ["R28", ""],
            "T4": ["R29", ""],
            "T5": ["R30", ""],
            "S1": ["R1", ""],
            "S2": ["R2", ""],
            "S3": ["R3", ""],
            "S4": ["R4", ""],
            "S5": ["R10", ""],
            "E": ["R33", ""],
            "F": ["R34", ""],
            "V": ["R51", ""],
            "X1": ["R41", ""],
            "X2": ["R42", ""],
            "X3": ["R43", ""],
            "X4": ["R44", ""],
            "X5": ["R45", ""],
            "M1": ["R46", ""],
            "M2": ["R47", ""],
            "M3": ["R48", ""],
            "M4": ["R49", ""],
            "M5": ["R50", ""],
        }
        self.pressure: str = ""
        self.vent: str = ""
        self.get_actualvalue_from_the_device()
        self.setpoint: Dict[str, List[str]] = {
            "M": ["R37", ""],
            "O": ["", ""],  # "O": [None, ""],
            "C": ["", ""],  # "C": [None, ""],
            "H": ["", ""],  # "H": [None, ""],
            "D1": ["", ""],  # "D1": [None, ""],
            "D2": ["", ""],  # "D2": [None, ""],
            "D3": ["", ""],  # "D3": [None, ""],
            "D4": ["", ""],  # "D4": [None, ""],
            "D5": ["", ""],  # "D5": [None, ""],
            "T1": ["R26", ""],
            "T2": ["R27", ""],
            "T3": ["R28", ""],
            "T4": ["R29", ""],
            "T5": ["R30", ""],
            "S1": ["R1", ""],
            "S2": ["R2", ""],
            "S3": ["R3", ""],
            "S4": ["R4", ""],
            "S5": ["R10", ""],
            "E": ["R33", ""],
            "F": ["R34", ""],
            "V": ["R51", ""],
            "X1": ["R41", ""],
            "X2": ["R42", ""],
            "X3": ["R43", ""],
            "X4": ["R44", ""],
            "X5": ["R45", ""],
            "M1": ["R46", ""],
            "M2": ["R47", ""],
            "M3": ["R48", ""],
            "M4": ["R49", ""],
            "M5": ["R50", ""],
        }
        for key in self.actualvalue.keys():
            self.setpoint[key][1] = self.actualvalue[key][1]
        self.set_actualvalue_to_the_device()
        self.updatedelay: float = updatedelay  # seconds
        self.running: bool = True
        self.lastupdate: float = 0
        self.updatetimer: threading.Timer = threading.Timer(self.updatedelay, self.update)
        self.updatetimer.start()

    def wrd(self, data):
        data = data.encode() if data is not None else None
        return self.device.write(data)  # type: ignore

    def update(self) -> None:
        """update

        will update every updatedelay seconds
        """
        global controller
        # print "updating now"
        self.updatetimer.cancel()
        self.updatelock.acquire()  # lock for running
        if self.running:
            if self.lastupdate is None:
                t = self.updatedelay
            else:
                t = max(0.000001, self.updatedelay + self.updatedelay - (time.time() - self.lastupdate))
            self.lastupdate = time.time()
            self.updatetimer = threading.Timer(t, self.update)
            self.updatetimer.start()
            self.set_actualvalue_to_the_device()
        self.updatelock.release()  # release the lock

    def shutdown(self) -> None:
        self.log.info("shutdown")
        self.running = False
        try:
            self.updatetimer.cancel()
        except Exception:
            pass
        if self.device.is_open:
            self.device.close()
            self.deviceopen = False

    def get_actualvalue_from_the_device(self) -> None:
        self.get_actualvalue_from_the_device_lock.acquire()  # lock to read data
        # print self.write_to_device("@253GC?;FF")
        for key in self.actualvalue.keys():
            if self.actualvalue[key][0]:
                if key == "M":
                    stor = self.write_to_device3(key, self.actualvalue[key][0])
                    self.decompose_m_string(stor)
                else:
                    self.actualvalue[key][1] = self.write_to_device3(key, self.actualvalue[key][0])
        self.pressure = self.write_to_device3("P", "R5")
        self.vent = self.write_to_device3("V", "R6")
        self.get_actualvalue_from_the_device_lock.release()  # release the lock

    def decompose_m_string(self, stor: str) -> None:
        if "0" == stor[2]:
            self.actualvalue["H"][1] = "0"
            self.actualvalue["C"][1] = "0"
            self.actualvalue["O"][1] = "1"
            for n in range(1, 6):
                self.actualvalue["D%i" % n][1] = "0"
        elif "1" == stor[2]:
            self.actualvalue["H"][1] = "0"
            self.actualvalue["C"][1] = "1"
            self.actualvalue["O"][1] = "0"
            for n in range(1, 6):
                self.actualvalue["D%i" % n][1] = "0"
        elif "2" == stor[2]:
            self.actualvalue["H"][1] = "1"
            self.actualvalue["C"][1] = "0"
            self.actualvalue["O"][1] = "0"
            for n in range(1, 6):
                self.actualvalue["D%i" % n][1] = "0"
        else:
            self.actualvalue["H"][1] = "0"
            self.actualvalue["C"][1] = "0"
            self.actualvalue["O"][1] = "0"
            for n in range(1, 6):
                if n == int(stor[2]) - 2:
                    self.actualvalue["D%i" % n][1] = "1"
                else:
                    self.actualvalue["D%i" % n][1] = "0"

    def update_setpoint_och(self, var):
        for i in self.setpoint:
            if self.setpoint[i][0] is None:
                if i == var:
                    self.setpoint[i][1] = "1"
                elif self.setpoint[i][1] == "1":
                    self.setpoint[i][1] = "0"

    def set_actualvalue_to_the_device(self):
        # will set the actualvalue to the device
        self.set_actualvalue_to_the_device_lock.acquire()  # lock to write data
        # write actualvalue to the device
        for key in self.actualvalue.keys():
            if "M" != key:
                if float(self.actualvalue[key][1]) != float(self.setpoint[key][1]):
                    if self.actualvalue[key][0]:
                        self.actualvalue[key][1] = self.write_to_device4(self.setpoint[key][1], key, self.setpoint[key][0])
                    elif "1" == self.setpoint[key][1]:
                        self.write_to_device2(key)
                        stor = self.write_to_device3("M", self.actualvalue["M"][0])
                        self.decompose_m_string(stor)
        self.pressure = self.write_to_device3("P", "R5")
        self.vent = self.write_to_device3("V", "R6")
        if self.communication_problem == -1:
            self.communication_problem = 0
            self.log.warning("write everything to device")
            # try it again
            # ?needed for recursion? self.set_actualvalue_to_the_device_lock.release()
            self.set_actualvalue_to_the_device()
        self.set_actualvalue_to_the_device_lock.release()  # release the lock

    def write_to_device2(self, com: str) -> None:
        global controller
        if len(com) == 0:
            return
        self.write_to_device_lock.acquire()
        if not self.deviceopen:
            self.device.open()
            if self.device.is_open:
                self.device.close()
                self.device.open()
            self.deviceopen = True
            self.log.debug("device.isOpen() - %s" % self.device.is_open)

        self.wrd("%s\r\n" % com)
        self.log.debug("SEND: %s\r\n" % com)
        self.device.flush()
        self.write_to_device_lock.release()

    def rdd(self, len: int) -> str:
        return self.device.read(len).decode("utf-8")

    def write_to_device3(self, com: str, answ: str) -> str:
        global controller
        self.write_to_device_lock.acquire()
        if not self.deviceopen:
            self.device.open()
            if self.device.is_open:
                self.device.close()
                self.device.open()
            self.deviceopen = True
            self.log.debug("device.isOpen() - %s" % self.device.is_open)

        self.device.flush()
        self.wrd("%s\r\n" % answ)
        r = self.rdd(len(com))
        if com != r:
            self.log.warning("communication problem with device %s" % self.devicename)
            self.communication_problem += 1
            if self.communication_problem >= 3:
                self.log.warning("%d communication problems; will restart the device" % self.communication_problem)
                self.device.flush()
                self.device.close()
                self.device.open()
                self.communication_problem = -1
            raise RuntimeError("Communication problem")
            r = None
        else:  # if command is recognised read up to "\r" or "\n" + 1 bytes
            dummy = self.rdd(1)
            r = ""
            while not (chr(13) == dummy or chr(10) == dummy):
                r += dummy
                dummy = self.rdd(1)
                # print ord(dummy)
            # dummy = self.rdd(1)
            # print ord(dummy)
            self.datalog.info("SENDRECEIVE: %s%s" % (com, r))
            try:
                fs = self.full_scale_values[int(self.actualvalue["E"][1])]
                unit = self.unit_list[int(self.actualvalue["F"][1])][3:]
                P = fs * float(self.pressure) / 100.0
                self.datalog.info("pressure %8.4f %s" % (P, unit))
            except Exception:
                pass
        self.write_to_device_lock.release()
        return r

    def write_to_device4(self, data: str, com: str, answ: str) -> str:
        global controller
        self.write_to_device_lock.acquire()
        if not self.deviceopen:
            self.device.open()
            if self.device.is_open:
                self.device.close()
                self.device.open()
            self.deviceopen = True
            self.log.debug("device.isOpen() - %s" % self.device.is_open)
        if data:
            self.wrd("%s%s\r\n" % (com, data))
            self.log.debug("SEND: %s%s\r\n" % (com, data))
        self.device.flush()
        # self.log.debug("RECEIVE: %s" % r)
        # time.sleep(0.025) #wait until the command is executed?
        self.wrd("%s\r\n" % answ)
        r = self.rdd(len(com))
        if com != r:
            self.log.warning("communication problem with device %s" % self.devicename)
            self.communication_problem += 1
            if self.communication_problem >= 3:
                self.log.warning("%d communication problems; will restart the device" % self.communication_problem)
                self.device.flush()
                # self.device.flushInput()
                # self.device.flushOutput()
                self.device.close()
                self.device.open()
                self.communication_problem = -1
            raise RuntimeError("Communication problem")
            r = None
        else:  # if command is recognised read up to "\r" or "\n" + 1 bytes
            dummy = self.rdd(1)
            r = ""
            while not (chr(13) == dummy or chr(10) == dummy):
                r += dummy
                dummy = self.rdd(1)
                # print ord(dummy)
            # dummy = self.rdd(1)
            # print ord(dummy)
            self.datalog.info("SENDRECEIVE: %s%s" % (com, r))
            try:
                fs = self.full_scale_values[int(self.actualvalue["E"][1])]
                unit = self.unit_list[int(self.actualvalue["F"][1])][3:]
                P = fs * float(self.pressure) / 100.0
                self.datalog.info("pressure %8.4f %s" % (P, unit))
            except Exception:
                pass
        self.write_to_device_lock.release()
        return r

    # def write_to_device(self, data, com, answ):
    #     global controller
    #     if len(com) == 0:
    #         return
    #     if self.device is None or self.devicename == "":
    #         self.log.warning("no device given; can't write to device!")
    #         self.log.debug("out: %s" % com)
    #         return
    #     self.write_to_device_lock.acquire()
    #     if not self.deviceopen:
    #         self.device.open()
    #         if self.device.is_open:
    #             self.device.close()
    #             self.device.open()
    #         self.deviceopen = True
    #         self.log.debug("device.isOpen() - %s" % self.device.is_open)
    #     if data:
    #         self.wrd("%s%s\r\n" % (com, data))
    #         self.log.debug("SEND: %s%s\r\n" % (com, data))
    #     elif not (data or answ):
    #         self.wrd("%s\r\n" % com)
    #         self.log.debug("SEND: %s\r\n" % com)
    #     self.device.flush()
    #     # self.log.debug("RECEIVE: %s" % r)
    #     if answ:
    #         # time.sleep(0.025) #wait until the command is executed?
    #         self.wrd("%s\r\n" % answ)
    #         r = self.rdd(len(com))
    #         if com != r:
    #             self.log.warning("communication problem with device %s" % self.devicename)
    #             self.communication_problem += 1
    #             if self.communication_problem >= 3:
    #                 self.log.warning("%d communication problems; will restart the device" % self.communication_problem)
    #                 self.device.flush()
    #                 # self.device.flushInput()
    #                 # self.device.flushOutput()
    #                 self.device.close()
    #                 self.device.open()
    #                 self.communication_problem = -1
    #             r = None
    #         else:  # if command is recognised read up to "\r" or "\n" + 1 bytes
    #             dummy = self.rdd(1)
    #             r = ""
    #             while not (chr(13) == dummy or chr(10) == dummy):
    #                 r += dummy
    #                 dummy = self.rdd(1)
    #                 # print ord(dummy)
    #             # dummy = self.rdd(1)
    #             # print ord(dummy)
    #             self.datalog.info("SENDRECEIVE: %s%s" % (com, r))
    #             try:
    #                 fs = self.full_scale_values[int(self.actualvalue["E"][1])]
    #                 unit = self.unit_list[int(self.actualvalue["F"][1])][3:]
    #                 P = fs * float(self.pressure) / 100.0
    #                 self.datalog.info("pressure %8.4f %s" % (P, unit))
    #             except:
    #                 pass
    #     self.write_to_device_lock.release()
    #     if answ:
    #         return r

    def open_vent(self):
        self.lock.acquire()
        self.update_setpoint_och("O")
        self.lock.release()

    def close_vent(self):
        self.lock.acquire()
        self.update_setpoint_och("C")
        self.lock.release()

    def stop_vent(self):
        self.lock.acquire()
        self.update_setpoint_och("H")
        self.lock.release()

    def set_setpoint(self, s=None):
        if s is not None:
            self.setpoint = s

    def get_actualvalue(self):
        self.lock.acquire()
        a = self.actualvalue
        self.lock.release()
        return a


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler, plc_tools.plc_socket_communication.tools_for_socket_communication):
    def handle(self):
        global controller
        # actual thread information:
        # cur_thread = threading.current_thread()
        # cur_thread.name
        #
        controller.log.debug("start connection to %s:%s" % (self.client_address[0], self.client_address[1]))
        data = ""
        while controller.running:
            self.request.settimeout(1)
            # get some data
            d = ""
            try:
                d = self.request.recv(1024 * 1024)
                if not d:
                    break
            except Exception:
                pass
            # analyse data
            response = ""
            if len(d) > 0:
                data += d
                found_something = True
            else:
                found_something = False
            while found_something:
                found_something = False
                if (len(data) >= 3) and (data[0:3].lower() == "set"):
                    # packed data; all settings at once
                    found_something = True
                    tmpdata = data[3:]
                    r = re.findall("^([0-9]+) ", tmpdata)
                    totalbytes = 0
                    if r:
                        totalbytes = 3 + len(r[0]) + 1 + int(r[0])
                        while len(data) < totalbytes:
                            data += self.request.recv(1024 * 1024)
                        length = int(r[0])
                        data = data[4 + len(r[0]):]
                        v = pickle.loads((data[0:length]).encode("utf-8"))
                        data = data[length:]
                        controller.set_setpoint(s=v)
                elif (len(data) >= 3) and (data[0:3].lower() == "get"):
                    # sends the actual values back
                    found_something = True
                    response += self.create_send_format(controller.get_actualvalue())
                    data = data[3:]
                elif (len(data) >= 6) and (data[0:3].lower() == "std"):
                    found_something = True
                    v = int(data[3:6])
                    controller.log.debug("set timedelay/updatedelay to %d milliseconds" % v)
                    controller.updatedelay = v / 1000.0
                    data = data[6:]
                elif (len(data) >= 4) and (data[0:4].lower() == "quit"):
                    found_something = True
                    a = "quitting"
                    response += a
                    controller.log.info(a)
                    data = data[4:]
                    controller.running = False
                    self.server.shutdown()
                elif (len(data) >= 7) and (data[0:7].lower() == "version"):
                    found_something = True
                    a = "mks_651_server Version: %s" % __mks_651_server_version__
                    response += a
                    controller.log.debug(a)
                    data = data[7:]
                elif (len(data) >= 3) and (data[0:3].lower() == "gap"):  # read pressure
                    found_something = True
                    response += self.create_send_format(controller.pressure)
                    data = data[3:]
                elif (len(data) >= 3) and (data[0:3].lower() == "gav"):  # read vent
                    found_something = True
                    s = pickle.dumps(controller.vent)
                    response += "%d %s" % (len(s), s)
                    data = data[3:]
                elif (len(data) >= 3) and (data[0:3].lower() == "ovn"):  # open vent
                    found_something = True
                    controller.open_vent()
                    data = data[3:]
                elif (len(data) >= 3) and (data[0:3].lower() == "cvn"):  # close vent
                    found_something = True
                    controller.close_vent()
                    data = data[3:]
                elif (len(data) >= 3) and (data[0:3].lower() == "svn"):  # stop vent
                    found_something = True
                    controller.stop_vent()
                    data = data[3:]
                if len(data) == 0:
                    break
            if len(response) > 0:
                # self.request.sendall(response)
                self.send_data_to_socket(self.request, response)
                # controller.log.debug("send to socket \"%s\"" % response)

    def send_data_to_socket(self, s, msg):
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


def shutdown(signum, frame):
    global controller
    controller.log.info("got signal %d" % signum)
    controller.log.debug("number of threads: %d" % threading.activeCount())
    controller.log.info("will exit the program")
    controller.shutdown()


def get_server(args: argparse.Namespace, log: logging.Logger, controller: controller_class) -> ThreadedTCPServer:
    s = True
    while s:
        s = False
        try:
            server = ThreadedTCPServer((args.ip, args.port), ThreadedTCPRequestHandler)
            return server
        except socket.error:
            if not args.choosenextport:
                controller.running = False
            if not args.choosenextport:
                raise
            s = True
            log.error("port %d is in use" % args.port)
            args.port += 1
            log.info("try port %d" % args.port)
    raise RuntimeError("Cannot get server")


def main():
    global controller
    # command line parameter
    help = ""
    help += "Over the given port on the given address a socket communication is "
    help += "listening with the following commands: (This is a prefix-code. Upper or lower letters do not matter.)\n"
    help += "  svn : sends a signal to stop the vent to the server\n"
    help += "  cvn : sends a signal to close the vent to the server\n"
    help += "  ovn : sends a signal to open the vent to the server\n"
    help += "  gap : gets the actual pressure value from the server\n"
    help += "  gav : gets the actual vent position from the server(in %)\n"
    help += "  set : sets the setpoint values as [pickle data]\n"
    help += "  get : gets the actual values back as [pickle data]\n"
    help += "  std000 : set the time between 2 actions to 000 milliseconds.\n"
    help += "  quit : quit the server\n"
    help += "  version : response the version of the server\n"
    # done ---- (below) (( i hope so :) ))
    parser = argparse.ArgumentParser(
        description="mks_651_server is a socket server to control the MKS-Typ 651C controller on a serial interface. On start all settings are fetched from the controller and the gui is initialized with these. A friendly kill (SIGTERM) should be possible.",
        epilog="Author: Richard Schlitz\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__mks_651_server_date__, help),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # device /dev/MKS_P900_1 (since its connected to the same rs232 - usb converter up to now)
    # IP to listen
    # port to listen
    # logfile /data/logs/mks_651_controller.log
    # delay time between 2 actions
    parser.add_argument("-device", nargs=1, default="", type=str, required=False, dest="device", help="Set the external device dev to communicate with the box.", metavar="dev")
    parser.add_argument(
        "-logfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "mks_651_controller.log"),
        type=str,
        required=False,
        dest="logfile",
        help="Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s"
        % os.path.join(tempfile.gettempdir(), "mks_651_controller.log"),
        metavar="f",
    )
    parser.add_argument(
        "-datalogfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "mks_651_controller.data"),
        type=str,
        required=False,
        dest="datalogfile",
        help="Set the datalogfile to f. Only the measurements will be logged here. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s"
        % os.path.join(tempfile.gettempdir(), "mks_651_controller.data"),
        metavar="f",
    )
    parser.add_argument(
        "-runfile",
        nargs=1,
        default=os.path.join(tempfile.gettempdir(), "mks_651_controller.pids"),
        type=str,
        required=False,
        dest="runfile",
        help='Set the runfile to f. If an other process is running with a given pid and writing to the same device, the program will not start. Setting f="" will disable this function. default: %s'
        % os.path.join(tempfile.gettempdir(), "pressure_controller.pids"),
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
        default=15122,
        type=int,
        required=False,
        dest="port",
        help="Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15122",
        metavar="p",
    )
    parser.add_argument(
        "-timedelay", nargs=1, default=0.05, type=float, required=False, dest="timedelay", help="Set the time between 2 actions to t seconds. default: t = 0.05", metavar="t"
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
        "-debug", nargs=1, default=0, type=int, required=False, dest="debug", help="Set debug level. 0 no debug info (default); 1 debug to STDOUT.", metavar="debug_level"
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
    if not isinstance(args.debug, int):
        args.debug = args.debug[0]
    # logging
    log = logging.getLogger("pcs")
    log.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    # create file handler
    # fh = logging.handlers.WatchedFileHandler(args.logfile)
    fh = QueuedWatchedFileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    # fh.setFormatter(logging.Formatter('%(created)f %(name)s %(levelname)s %(message)s'))
    fh.setFormatter(logging.Formatter("%(created)f %(levelname)s %(message)s"))
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO)  # logging.WARNING = 30
    # ch.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s',datefmt='%H:%M:%S'))
    ch.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    datalog = logging.getLogger("pcsd")
    datalog.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    # create file handler
    fhd = QueuedWatchedFileHandler(args.datalogfile)
    fhd.setLevel(logging.DEBUG)
    fhd.setFormatter(logging.Formatter("%(created)f %(message)s"))
    # add the handlers to log
    datalog.addHandler(fhd)
    log.info("start logging in mks_651_server: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.info('logging to "%s"' % args.logfile)
    signal.signal(signal.SIGTERM, shutdown)
    # check runfile
    ori = [os.getpid(), args.device]
    runinfo = [ori]
    # runinfo = os.getpid(),args.device
    if os.path.isfile(args.runfile):
        # file exists, read it
        f = open(args.runfile, "r")
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
        f.close()
        if r:
            log.debug("other process is running; exit.")
            sys.exit(1)
    f = open(args.runfile, "w")
    writer = csv.writer(f)
    for i in range(len(runinfo)):
        writer.writerows([runinfo[i]])
    f.close()
    # go in background if useful
    if args.debug == 0:
        # go in background
        log.info("go to background (fork)")
        fh.flush()
        if args.debug != 0:
            ch.flush()
        newpid = os.fork()
        if newpid > 0:
            log.info("background process pid = %d" % newpid)
            time.sleep(0.050)  # time for first communication with device
            sys.exit(0)
        elif args.runfile != "":
            nri = [os.getpid(), args.device]
            index = runinfo.index(ori)
            runinfo[index] = nri
            f = open(args.runfile, "w")
            writer = csv.writer(f)
            for i in range(len(runinfo)):
                writer.writerows([runinfo[i]])
                f.close()
        log.removeHandler(ch)
        # threads in the default process are dead
        # in particular this means QueuedWatchedFileHandler is not working anymore
        fh.startloopthreadagain()
        fhd.startloopthreadagain()
    else:
        log.info("due to debug=1 will _not_ go to background (fork)")
    controller = controller_class(log=log, datalog=datalog, device=args.device, updatedelay=args.timedelay)
    server = get_server(args, log, controller)
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
