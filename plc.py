#!/usr/bin/python
"""PlasmaLabControl

Author: Daniel Mohr.

License: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.

Copyright (C) 2012, 2013, 2014 Daniel Mohr and PlasmaLab (FKZ 50WP0700 and FKZ 50WM1401)

Full license notice: LICENSE.txt
"""

__plc_date__ = "2013-01-26"
__plc_version__ = __plc_date__

import argparse
import logging

# import logging.handlers
# import Queue
import os
import time

import plc_gui
import plc_gui.read_config_file
import plc_tools.plclogclasses

# from plc_tools.plclogclasses import QueuedWatchedFileHandler


def main() -> None:
    # command line parameter
    parser = argparse.ArgumentParser(
        description='plc - PlasmaLabControl. For more help\ntype "pydoc plc"',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007." % __plc_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-debug", nargs=1, default=0, type=int, required=False, dest="debug", help="Set debug level. 0 no debug info (default); 1 debug to STDOUT.", metavar="debug_level"
    )
    parser.add_argument(
        "-system_config",
        nargs=1,
        default="/etc/plc.cfg",
        type=str,
        required=False,
        dest="system_config",
        help="Set system wide config file to use. This will be read first. (default: '/etc/plc.cfg')",
        metavar="file",
    )
    parser.add_argument(
        "-config",
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
    fh.setFormatter(logging.Formatter("%(created)f %(name)s %(levelname)s %(message)s"))
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    else:
        ch.setLevel(logging.WARNING)  # logging.WARNING = 30
    ch.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S"))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    log.info("start logging in plc: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.info("running with pid %d" % os.getpid())
    # start gui
    plc_gui.start_gui(args, configname=configname)
    fh.flush()
    ch.flush()
    log.info("stop plc: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime()))
    log.info("stop logging in plc: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    fh.close()
    ch.close()
    fh.flush()
    ch.flush()


if __name__ == "__main__":
    main()
