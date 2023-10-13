"""draft for our servers

Author: Daniel Mohr
Date: 2013-05-13
"""

import time
import serial
import logging
import threading
from abc import abstractmethod
from typing import Dict, Any, List


class controller_class:
    def __init__(
        self, log: logging.Logger, datalog: logging.Logger, device: str, updatedelay: float = 1, *args
    ) -> None:
        self.log: logging.Logger = log
        self.datalog: logging.Logger = datalog
        self.devicename: str = device
        self.deviceopen: bool = False
        self.boudrate: int = 9600
        self.databits = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE  # serial.STOPBITS_ONE_POINT_FIVE serial.STOPBITS_TWO
        self.readtimeout: float = 0.1
        self.writetimeout: float = 0.1
        self.sleeptime: float = 0.001
        self.minsleeptime: float = 0.000001
        self.device: serial.Serial = serial.Serial(
            port=None,
            baudrate=self.boudrate,
            bytesize=self.databits,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.readtimeout,
            write_timeout=self.writetimeout,
        )
        self.device.port = self.devicename
        self.communication_problem: int = 0
        self.actualvaluelock: threading.Lock = threading.Lock()
        self.setpointlock: threading.Lock = threading.Lock()
        self.updatelock: threading.Lock = threading.Lock()
        self.set_actualvalue_to_the_device_lock: threading.Lock = threading.Lock()
        self.send_data_to_socket_lock: threading.Lock = threading.Lock()
        self.actualvalue: Dict[str, Any] = {}
        self.myinit(*args)
        self.set_actualvalue_to_the_device()
        self.updatedelay: float = updatedelay  # seconds
        self.running: bool = True
        self.lastupdate: float = time.time()
        self.updatethread: threading.Thread = threading.Thread(target=self.updateloop)
        self.updatethread.daemon = True
        self.updatethread.start()

    @abstractmethod
    def myinit(self, *args) -> None:
        ...

    @abstractmethod
    def set_actualvalue_to_the_device(self) -> None:
        ...

    def str2boolarray(self, A: str) -> List[bool]:
        n = len(A)
        r = n * [False]
        for i in range(n):
            if A[i] == "1":
                r[i] = True
        return r

    def str2bool(self, s: str) -> bool:
        if s == "1":
            r = True
        else:
            r = False
        return r

    def str2float(self, s: str) -> List[float]:
        a = s.split(",")
        b: List[float] = []
        for i in range(len(a)):
            b[i] = float(a[i])
        return b

    def boolarray2str(self, A: List[bool]) -> str:
        n = len(A)
        r = ""
        for i in range(n):
            if A[(n - 1) - i]:
                r += "1"
            else:
                r += "0"
        return r

    def boolarray2int(self, A: List[bool]) -> int:
        return int(self.boolarray2str(A), 2)

    def boolarray2hex(self, A: List[bool]) -> str:
        return "%02X" % self.boolarray2int(A)

    def int2boolarray(self, i: int) -> List[bool]:
        s = "{0:08b}".format(i)
        A = 8 * [False]
        for i in range(8):
            if s[i] == "1":
                A[i] = True
        return A

    def updateloop(self) -> None:
        """update

        will update every updatedelay seconds

        Author: Daniel Mohr
        Date: 2013-01-25
        """
        global controller
        self.updatelock.acquire()  # lock for running
        while self.running:
            self.set_actualvalue_to_the_device()
            nextupdate = self.lastupdate + self.updatedelay
            self.lastupdate = time.time()
            time.sleep(self.minsleeptime)
            while self.running and (time.time() < nextupdate):
                time.sleep(self.sleeptime)
        self.updatelock.release()  # release the lock

    def shutdown(self) -> None:
        self.log.info("shutdown")
        self.running = False
        time.sleep(2 * self.sleeptime)
        if self.device.is_open:
            self.device.close()
            self.deviceopen = False

    def set_setpoint(self, s: Dict[str, Any]) -> None:
        if s is not None:
            self.setpointlock.acquire()  # lock to set
            self.setpoint = s.copy()
            self.setpointlock.release()  # release the lock

    def get_setpoint(self) -> Dict[str, Any]:
        """get_setpoint

        So far as I know, this function is useless.
        It only exist due to completeness.

        Author: Daniel Mohr
        Date: 2012-09-30
        """
        self.setpointlock.acquire()  # lock to set
        s = self.setpoint
        self.setpointlock.release()  # release the lock
        return s

    def get_actualvalue(self) -> Dict[str, Any]:
        self.actualvaluelock.acquire()  # lock to get new settings
        a = self.actualvalue.copy()
        self.actualvaluelock.release()  # release the lock
        return a
