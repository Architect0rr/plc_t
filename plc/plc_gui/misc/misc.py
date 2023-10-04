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
import logging

proccesses_to_join: List[Process] = []
threads_to_join: List[Thread] = []


class bcolors:
    grey = "\x1b[38;20m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    HEADER = "\033[95m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class CustomFormatter(logging.Formatter):
    _format: str = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"

    FORMATS = {
        logging.DEBUG: bcolors.OKBLUE + _format + bcolors.reset,
        logging.INFO: bcolors.OKGREEN + _format + bcolors.reset,
        logging.WARNING: bcolors.yellow + _format + bcolors.reset,
        logging.ERROR: bcolors.red + _format + bcolors.reset,
        logging.CRITICAL: bcolors.bold_red + _format + bcolors.reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
