#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import threading
from typing import Dict, Any, Protocol, Union
from abc import abstractmethod


class CTRL(Protocol):
    lock: Union[threading.Lock, threading.RLock]
    setpoint: Dict[str, Any]
    actualvalue: Dict[str, Any]
    connected: bool

    @abstractmethod
    def start_request(self) -> None:
        ...

    @abstractmethod
    def stop_request(self) -> None:
        ...


if __name__ == "__main__":
    pass
