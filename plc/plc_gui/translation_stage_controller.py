"""class for translation stage controller (trinamix_tmcm_351)

Author: Daniel Mohr
Date: 2013-03-05
"""

import time
import serial
import logging
import threading
from typing import List, Dict


from .read_config_file import read_config_file
from .base_controller import CTRL


class TSC(CTRL):
    """class for translation stage controller (trinamix_tmcm_351)

    Author: Daniel Mohr
    Date: 2012-08-27
    """

    def __init__(self, config: read_config_file, controller: Dict[str, CTRL], log: logging.Logger) -> None:
        self.lock = threading.RLock()
        self.readbytes = 4096  # read this number of bytes at a time
        self.readbytes = 16384  # read this number of bytes at a time
        self.debug = True
        self.log = log
        self.config = config
        self.pc = controller[self.config.values.get("translation stage controller", "power_controller")]
        self.pp = self.config.values.get("translation stage controller", "power_port")
        self.pca = self.config.values.getint("translation stage controller", "power_channel")
        self.lastupdate = time.time()
        self.devicename = self.config.values.get("translation stage controller", "devicename")
        self.boudrate = self.config.values.getint("translation stage controller", "boudrate")
        databits: List[int] = [0, 1, 2, 3, 4, serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS]
        self.databits = databits[int(self.config.values.get("translation stage controller", "databits"))]
        self.parity = serial.PARITY_NONE
        if self.config.values.get("translation stage controller", "stopbits") == "1":
            self.stopbits: float = serial.STOPBITS_ONE
        elif self.config.values.get("translation stage controller", "stopbits") == "1.5":
            self.stopbits = serial.STOPBITS_ONE_POINT_FIVE
        elif self.config.values.get("translation stage controller", "stopbits") == "2":
            self.stopbits = serial.STOPBITS_TWO

        self.readtimeout = self.config.values.getfloat("translation stage controller", "readtimeout")
        self.writetimeout = self.config.values.getint("translation stage controller", "writetimeout")
        self.update_intervall = self.config.values.getint("translation stage controller", "update_intervall")
        self.setpoint: Dict[str, None] = {}
        self.actualvalue: Dict[str, None] = {}
        self.connected: bool = False

    def __write(self, s: str) -> int:
        d = self.device.write(s.encode("utf-8"))
        return d if d is not None else 0

    def __read(self) -> str:
        return self.device.read(self.readbytes).decode("utf-8")

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        self._x = value
        self.log.debug(f"X pos changed to {value}, writting to device")
        self.__x_write()
        self._x = 0

    def __x_write(self) -> None:
        self.__write(f"AMVP REL,0,{self._x}\r")
        self.log.debug(f"From device: {self.__read()}")

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        self._y = value
        self.log.debug(f"X pos changed to {value}, writting to device")
        self.__y_write()
        self._y = 0

    def __y_write(self) -> None:
        self.__write(f"AMVP REL,1,{self._y}\r")
        self.log.debug(f"From device: {self.__read()}")

    @property
    def z(self) -> int:
        return self._z

    @z.setter
    def z(self, value: int) -> None:
        self._z = value
        self.log.debug(f"X pos changed to {value}, writting to device")
        self.__z_write()
        self._z = 0

    def __z_write(self) -> None:
        self.__write(f"AMVP REL,2,{self._z}\r")
        self.log.debug(f"From device: {self.__read()}")

    def power(self, state: bool) -> None:
        self.pc.setpoint[self.pp][self.pca] = state

    # def set_default_values(self) -> None:
    #     """set default values

    #     set setpoint[...] to None
    #     set actualvalue[...] to None

    #     Author: Daniel Mohr
    #     Date: 2012-08-27
    #     """
    #     self.x = 0
    #     self.y = 0
    #     self.z = 0

    def start_request(self) -> bool:
        return self.start()

    def stop_request(self) -> bool:
        return self.stop()

    def start(self) -> bool:
        self.device = serial.Serial(
            port=self.devicename,
            baudrate=self.boudrate,
            bytesize=self.databits,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.readtimeout,
            write_timeout=self.writetimeout,
        )
        self.log.debug("Starting translation stage controlling on port %s" % self.devicename)
        try:
            self.device.open()
            self.device.write(b"\x01\x8b\x00\x00\x00\x00\x00\x00\x8c\r")  # 0x018b 0x0000 0x0000 0x0000 0x8c
            self.connected = True
            self.log.debug("Connected")
            return True
        except Exception:
            self.connected = False
            self.log.debug("Cannot connect")
            return False

    def stop(self) -> bool:
        if self.device.is_open:
            self.device.close()
            self.connected = False
            self.log.debug("Stopped translation stage controlling on port %s" % self.devicename)
        else:
            self.connected = False
        return True
