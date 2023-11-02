#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Daniel Mohr
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

from .plcclientserverclass import socket_communication_class, if_connect, data_lock
from .read_config_file import read_config_file
from .base_controller import CTRL


class digital_controller(socket_communication_class, CTRL):
    """
    class for digital controller (red box)
    """

    def __init__(self, log: logging.Logger, config: read_config_file, bufsize: int = 4096) -> None:
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
        self.set_default_values()

    @if_connect
    def set_default_values(self) -> bool:
        """set default values

        set setpoint[...] to 0 or False
        if connected to real device, get actualvalue[...] from it
        otherwise set actualvalue[...] to  0 or False
        """
        self.datalock.acquire()
        for port in self.ports:
            for channel in range(8):
                self.setpoint[port][channel] = None
        self.datalock.release()
        self.get_actualvalues()
        return True

    @data_lock
    def myextra_socket_communication_with_server(self) -> None:
        self.setpoint["dispenser"]["shake"] = False

    @data_lock
    def actualvalue2setpoint(self) -> None:
        for port in self.ports:
            for channel in range(8):
                self.setpoint[port][channel] = self.actualvalue[port][channel]


if __name__ == "__main__":
    pass
