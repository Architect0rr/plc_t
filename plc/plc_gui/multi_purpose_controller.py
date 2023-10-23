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
class for multi purpose controller (blue box)
"""

import logging
from typing import Dict, List, Any

from .plcclientserverclass import data_lock, general_lock, socket_communication_class
from .read_config_file import read_config_file
from .base_controller import controller


class multi_purpose_controller(socket_communication_class, controller):
    """
    class for multi purpose controller (blue box)
    """

    def __init__(self, log: logging.Logger, config: read_config_file, bufsize: int = 4096):
        super().__init__(log, config, "mpc", bufsize)

        self.myservername = "multi_purpose_controller_server"
        self.actualvalue: Dict[str, Any] = {
            "DO": 4 * [None],
            "R": 2 * [None],
            "U05": None,
            "U15": None,
            "U24": None,
            "DAC": 4 * [0.0],
            "DI": 4 * [None],
            "ADC": 8 * [0],
        }  # dict of values on device
        self.setpoint: Dict[str, Any] = {
            "DO": 4 * [None],
            "R": 2 * [None],
            "U05": None,
            "U15": None,
            "U24": None,
            "DAC": 4 * [0.0],
        }  # dict of requested values, which will be updated to device
        self.ports: List[str] = ["DO", "R", "U05", "U15", "U24", "DAC", "DI", "ADC"]
        self.ports_without_channel: List[str] = ["U05", "U15", "U24"]
        self.setpoint_port: List[str] = ["DO", "R", "U05", "U15", "U24", "DAC"]
        self.actualvalue_port: List[str] = ["DO", "R", "U05", "U15", "U24", "DAC", "DI", "ADC"]

    @data_lock
    @general_lock
    def set_default_values(self) -> None:
        """set default values

        set setpoint[...] to 0 or False
        if connected to real device, get actualvalue[...] from it
        otherwise set actualvalue[...] to  0 or False
        """
        port = "DO"
        for channel in range(4):
            self.setpoint[port][channel] = None
        port = "R"
        for channel in range(2):
            self.setpoint[port][channel] = None
        for port in ["U05", "U15", "U24"]:
            self.setpoint[port] = None
        port = "DAC"
        for channel in range(4):
            self.setpoint[port][channel] = None
        if self.socket is not None:
            self.get_actualvalues()
        else:
            port = "DO"
            for channel in range(4):
                self.actualvalue[port][channel] = False
            port = "R"
            for channel in range(2):
                self.actualvalue[port][channel] = False
            for port in ["U05", "U15", "U24"]:
                self.actualvalue[port] = False
            port = "DAC"
            for channel in range(4):
                self.actualvalue[port][channel] = 0
            port = "DI"
            for channel in range(4):
                self.actualvalue[port][channel] = False
            port = "ADC"
            for channel in range(8):
                self.actualvalue[port][channel] = 0

    @data_lock
    def actualvalue2setpoint(self) -> None:
        port = "DO"
        for channel in range(4):
            self.setpoint[port][channel] = self.actualvalue[port][channel]
        port = "DAC"
        for channel in range(4):
            self.setpoint[port][channel] = self.actualvalue[port][channel]
        for port in ["U05", "U15", "U24"]:
            self.setpoint[port] = self.actualvalue[port]
        port = "DAC"
        for channel in range(4):
            self.setpoint[port][channel] = self.actualvalue[port][channel]


if __name__ == "__main__":
    pass
