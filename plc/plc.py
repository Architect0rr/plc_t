#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2014, 2017 Daniel Mohr and PlasmaLab (FKZ 50WP0700 and FKZ 50WM1401)
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
plc - PlasmaLabControl

Copyright (C) 2012, 2013, 2014 Daniel Mohr and PlasmaLab (FKZ 50WP0700 and FKZ 50WM1401)

Copyright (C) 2023 Perevoshchikov Egor

License: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.

Full license notice: LICENSE
"""

__plc_date__ = "2013-01-26"
__plc_version__ = __plc_date__

import argparse
import logging

import os
import sys
import time
from typing import Literal

import plc_gui
import plc_gui.read_config_file
import plc_tools.plclogclasses


def main() -> Literal[0]:
    parser = argparse.ArgumentParser(
        description='plc - PlasmaLabControl. For more help\ntype "pydoc plc"',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007." % __plc_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--debug", choices=[0, 1], default=1, type=int, required=False, dest="debug", help="Set debug level. 0 no debug info (default); 1 debug to STDOUT.", metavar="debug_level"
    )
    parser.add_argument(
        "--system_config",
        nargs=1,
        default="/etc/plc.cfg",
        type=str,
        required=False,
        dest="system_config",
        help="Set system wide config file to use. This will be read first. (default: '/etc/plc.cfg')",
        metavar="file",
    )
    parser.add_argument(
        "--config",
        nargs=1,
        default="~/.plc.cfg",
        type=str,
        required=False,
        dest="config",
        help="Set user config file to use. This will be read after the system wide config file. (default: '~/.plc.cfg')",
        metavar="file",
    )
    args = parser.parse_args()
    configname: str = ""
    if not isinstance(args.debug, int):
        args.debug = args.debug[0]
    if type(args.system_config) == list:
        args.system_config = args.system_config[0]
        configname = "%s%s" % (configname, args.system_config)
    if type(args.config) == list:
        args.config = args.config[0]
        configname = "%s%s" % (configname, args.config)
    configs = plc_gui.read_config_file.read_config_file(system_wide_ini_file=args.system_config, user_ini_file=args.config)
    # logging
    log = logging.getLogger("plc")
    log.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    # create file handler
    # fh = logging.handlers.WatchedFileHandler(configs.values.get('ini','log_file'))
    fh = plc_tools.plclogclasses.QueuedWatchedFileHandler(configs.values.get("ini", "log_file"))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    else:
        ch.setLevel(logging.WARNING)  # logging.WARNING = 30
    ch.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    log.info("start logging in plc: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.info("running with pid %d" % os.getpid())
    # start gui
    log.debug("Starting GUI")
    plc_gui.PLC.main(args, log.getChild("gui"), configname)
    # after gui
    log.debug("Flushing log handlers")
    fh.flush()
    ch.flush()
    log.info("stop plc: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime()))
    log.info("stop logging in plc: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    fh.close()
    ch.close()
    fh.flush()
    ch.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
