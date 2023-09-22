#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Daniel Mohr
#
# Copyright (C) 2023 Egor Perevoshchikov
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
class for digital controller (red box)
"""

import logging
from typing import List, Dict, Any

from .read_config_file import read_config_file
from . import plcclientserverclass


class digital_controller(plcclientserverclass.socket_communication_class):
    """
    class for digital controller (red box)
    """

    def __init__(self, log: logging.Logger, config: read_config_file, bufsize: int = 4096):
        super().__init__(log, config, "dc", bufsize)

        self.myservername = "digital_controller_server"
        # setpoint/actualvalue:
        self.setpoint: Dict[str, Any] = {
            "A": 8 * [None],
            "B": 8 * [None],
            "dispenser": {"n": None, "ton": None, "shake": False, "port": None, "channel": None, "toff": None},
            "C": 8 * [None],
            "D": 8 * [None],
        }  # dict of requested values, which will be updated to device
        self.actualvalue: Dict[str, Any] = {
            "A": 8 * [None],
            "B": 8 * [None],
            "dispenser": {"n": None, "ton": None, "shake": False, "port": None, "channel": None, "toff": None},
            "C": 8 * [None],
            "D": 8 * [None],
        }  # dict of values on device
        self.ports: List[str] = ["A", "B", "C", "D"]

    def set_default_values(self) -> None:
        """set default values

        set setpoint[...] to 0 or False
        if connected to real device, get actualvalue[...] from it
        otherwise set actualvalue[...] to  0 or False

        Author: Daniel Mohr
        Date: 2012-11-27
        """
        self.lock.acquire()  # lock
        for port in self.ports:
            for channel in range(8):
                self.setpoint[port][channel] = None
        if self.connected:
            self.socketlock.acquire()  # lock
            self.get_actualvalues()
            self.socketlock.release()  # release the lock
        else:
            for port in self.ports:
                for channel in range(8):
                    self.actualvalue[port][channel] = False
        self.lock.release()  # release the lock

    def myextra_socket_communication_with_server(self) -> None:
        self.setpoint["dispenser"]["shake"] = False

    def actualvalue2setpoint(self) -> None:
        for port in self.ports:
            for channel in range(8):
                self.setpoint[port][channel] = self.actualvalue[port][channel]
