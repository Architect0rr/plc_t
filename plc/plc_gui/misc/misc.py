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


from multiprocessing import Process
from threading import Thread
from typing import List

proccesses_to_join: List[Process] = []
threads_to_join: List[Thread] = []
