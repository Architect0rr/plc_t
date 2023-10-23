#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Daniel Mohr
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
class for electrode motion controller (zpos)
"""

import time
import serial
import logging
from typing import List

from . import read_config_file
from .base_controller import controller


class electrode_motion_controller(controller):
    """
    class for electrode motion controller (zpos)
    """

    def __init__(
        self, power_controller: controller, config: read_config_file.read_config_file, _log: logging.Logger
    ) -> None:
        self.power_controller: controller = power_controller
        self.readbytes = 4096  # read this number of bytes at a time
        self.readbytes = 16384  # read this number of bytes at a time
        self.debug = True
        self.config = config
        self.log = _log
        self.lastupdate = time.time()
        self.devicename = self.config.values.get("electrode motion controller", "devicename")
        self.boudrate = int(self.config.values.get("electrode motion controller", "boudrate"))
        databits: List[int] = [0, 1, 2, 3, 4, serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS]
        self.databits: int = databits[int(self.config.values.get("electrode motion controller", "databits"))]
        self.parity = serial.PARITY_NONE
        if self.config.values.get("electrode motion controller", "stopbits") == "1":
            self.stopbits: float = serial.STOPBITS_ONE
        elif self.config.values.get("electrode motion controller", "stopbits") == "1.5":
            self.stopbits = serial.STOPBITS_ONE_POINT_FIVE
        elif self.config.values.get("electrode motion controller", "stopbits") == "2":
            self.stopbits = serial.STOPBITS_TWO

        self.readtimeout = self.config.values.getfloat("electrode motion controller", "readtimeout")
        self.writetimeout = self.config.values.getfloat("electrode motion controller", "writetimeout")
        self.device = serial.Serial(
            port=None,
            baudrate=self.boudrate,
            bytesize=self.databits,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.readtimeout,
            write_timeout=self.writetimeout,
        )
        self.device.port = self.devicename
        self.T_off = self.config.values.getint("electrode motion controller", "T_off")
        self.update_intervall = self.config.values.getint("electrode motion controller", "update_intervall")
        self.disabled_lower_guard_ring = (
            self.config.values.get("electrode motion controller", "disable_lower_guard_ring") == "1"
        )

        self.emc_pp = self.config.values.get("electrode motion controller", "power_port")
        self.emc_pc = self.config.values.getint("electrode motion controller", "power_channel")
        self.connected: bool = False

    def power_switch(self, s: bool) -> None:
        self.power_controller.setpoint[self.emc_pp][self.emc_pc] = s

    def __write(self, data: str) -> None:
        self.log.debug(f"To dev: '{data}'")
        self.device.write(data.encode("utf-8"))

    def __general_move(self, sym: str, steps: int) -> None:
        if self.connected:
            for i in range(steps):
                self.__write(sym)
            try:
                responce = self.device.read(self.readbytes).decode("utf-8")
                self.log.debug(f"From dev: '{responce}'")
            except Exception:
                pass
        else:
            self.log.error("Cannot move, emc not connected")

    def upper_guard_ring_move(self, steps: int = 0) -> None:
        self.__general_move("K" if steps > 0 else "k", abs(steps))

    def lower_guard_ring_move(self, steps: int = 0) -> None:
        self.__general_move("m" if steps > 0 else "M", abs(steps))

    def lower_electrode_move(self, steps: int = 0) -> None:
        self.__general_move("n" if steps > 0 else "N", abs(steps))

    def upper_electrode_move(self, steps: int = 0) -> None:
        self.__general_move("L" if steps > 0 else "l", abs(steps))

    def start(self) -> bool:
        if not self.connected:
            self.log.debug(f"Starting electrode motion controlling on port {self.devicename}")
            try:
                self.device.open()
                self.log.debug("connect")
                self.connected = True
                return True
            except Exception:
                self.log.debug("cannot connect")
                return False
        else:
            return False

    def stop(self) -> bool:
        if self.connected:
            self.device.close()
            self.log.debug(f"Stoped electrode motion controlling on port {self.devicename}")
            self.connected = False
            return True
        else:
            return False

    def start_request(self) -> bool:
        return self.start()

    def stop_request(self) -> bool:
        return self.stop()


# class emc_gui(ttk.LabelFrame):
#     def __init__(self, _root: ttk.Frame, _backend: electrode_motion_controller, _log: logging.Logger) -> None:
#         super().__init__(_root, text="emc")
#         self.backend: electrode_motion_controller = _backend
#         self.log: logging.Logger = _log

#         self.start_button = tkinter.Button(self, text="open", command=self.start)
#         self.start_button.grid(row=0, column=0)
#         self.stop_button = tkinter.Button(self, text="close", command=self.stop, state=tkinter.DISABLED)
#         self.stop_button.grid(row=0, column=1)

#     def start(self) -> None:
#         self.start_button.configure(state=tkinter.DISABLED)
#         self.stop_button.configure(state=tkinter.NORMAL)
#         self.backend.start()

#     def stop(self) -> None:
#         self.start_button.configure(state=tkinter.NORMAL)
#         self.stop_button.configure(state=tkinter.DISABLED)
#         self.backend.stop()


if __name__ == "__main__":
    pass
