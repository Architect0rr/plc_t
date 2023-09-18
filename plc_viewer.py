#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-10-20, 2014-07-22

__plc_viewer_date__ = "2014-07-22"
__plc_viewer_version__ = __plc_viewer_date__

import argparse
import os
import time
import logging
import logging.handlers
import sys
import types

from plc_tools.plc_viewer_gui import gui
from plc_tools.plc_viewer_main_file import main_file
from plc_tools.plc_viewer_main_directory import main_directory

def main():
    # command line parameter
    parser = argparse.ArgumentParser(
        description='plc-viewer',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\nThe gamma value in the gui will only be recognized after changing the scale.\n\nExamples:\n plc_viewer.py -f /home/mohr/examplecams/\n plc_viewer.py -s 0.2 -ca 3\n plc_viewer.py -absolutscale 300 -camcolumn 4" % __plc_viewer_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-f',
                        nargs="+",
                        default="./",
                        type=str,
                        required=False,
                        dest='dir',
                        help='will play this directory or this file. default: ./',
                        metavar='dir')
    parser.add_argument('-scale',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='scale',
                        help='Set the scale factor x. default: x = 1.0',
                        metavar='x')
    parser.add_argument('-absolutscale',
                        nargs=1,
                        default=-1,
                        type=int,
                        required=False,
                        dest='absolutscale',
                        help='Set the absolut scale to x pixel width. default: x = -1 (dissabled)',
                        metavar='x')
    parser.add_argument('-timeratefactor',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='timeratefactor',
                        help='Set the time rate factor x. default: x = 1.0',
                        metavar='x')
    parser.add_argument('-camcolumn',
                        nargs=1,
                        default=3,
                        type=int,
                        required=False,
                        dest='camcolumn',
                        help='Set the number of columns for the cams. default: c = 3',
                        metavar='c')
    parser.add_argument('-config',
                        nargs=1,
                        default="./plc.cfg",
                        type=str,
                        required=False,
                        dest='config',
                        help='Set the config as used by measuring. (default: \'./plc.cfg\')',
                        metavar='file')
    parser.add_argument('-index',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='index',
                        help='If set to 1: create only index and exit.',
                        metavar='i')
    parser.add_argument('-create_info_graphics',
                        nargs=1,
                        default=-1,
                        type=int,
                        required=False,
                        dest='create_info_graphics',
                        help='0 do not create info graphics (default for viewing a file); 1 create info graphics (default for viewing a directory).',
                        metavar='c')
    parser.add_argument('-gamma',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='gamma',
                        help='Set the gamma value to v. default: v = 1.0',
                        metavar='v')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    args = parser.parse_args()
    configname = ""
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.dir,str):
        args.dir = args.dir[0]
    if not isinstance(args.timeratefactor,float):
        args.timeratefactor = args.timeratefactor[0]
    if not isinstance(args.scale,float):
        args.scale = args.scale[0]
    if not isinstance(args.camcolumn,int):
        args.camcolumn = args.camcolumn[0]
    if not isinstance(args.index,int):
        args.index = args.index[0]
    if not isinstance(args.absolutscale,int):
        args.absolutscale = args.absolutscale[0]
    if args.absolutscale == -1:
        args.absolutscale = None
    if type(args.config) == list:
        args.config = args.config[0]
    if not isinstance(args.create_info_graphics,int):
        args.create_info_graphics = args.create_info_graphics[0]
    if not isinstance(args.gamma,float):
        args.gamma = args.gamma[0]
    # logging
    log = logging.getLogger('plc_viewer')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.WARNING) # logging.WARNING = 30
    ch.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(ch)
    log.info("start logging in plc_viewer: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    if os.path.isdir(args.dir):
        if args.create_info_graphics == -1:
            args.create_info_graphics = 1
        main_directory(log,args)
    elif os.path.isfile(args.dir):
        if args.create_info_graphics == -1:
            args.create_info_graphics = 0
        main_file(log,args)
    else:
        log.error("\"%s\" is not directory and is not a file!" % args.dir)
        sys.exit(1)
    log.debug("exit")
    sys.exit(0)

if __name__ == "__main__":
    main()

##plc.log:
##1347252790.953912 plc.plc_gui INFO set flow rate to 40959 (2.500000 V, 500.000000 msccm)
##1347255907.964994 plc.rf_gen_ctrl INFO to rf-gen 0: @X08@P00000000@D
##1347255907.965462 plc.rf_gen_ctrl INFO to rf-dc 0: #O#D0000000000000000
##1347256512.197234 plc.plc_gui INFO shake dispenser1
##1347257788.947600 plc.plc_gui DEBUG choose setpoints 14: parabola 12 -- few particles 60Pa RF 1000 - 4 electrodes
##1347257798.898997 plc.plc_gui DEBUG set setpoints 14: parabola 12 -- few particles 60Pa RF 1000 - 4 electrodes

##MPC0006.log:
##1347250951.324165 MPC0006 [I] Transmitted:@Q000D0000000000000000A07FA094C20BD000120C620CB20D220D8IFC.


##zyflex_plc.cfg
##[RF-Generator]
##maxcurrent = 2500
##maxcurrent_tmp = 3000
##[RF-Generator 1]
##gen_device = /dev/RF_GEN_02
##dc_device = /dev/RF_DC_02
##[RF-Generator 2]
##power_controller = -1
##[RF-Generator 3]
##power_controller = -1
##[gas system]
##mass_flow_controller_status_controller = mpc
##mass_flow_controller_status_port = U15
##mass_flow_controller_status_channel = -1
##mass_flow_controller_measure_rate_controller = mpc
##mass_flow_controller_measure_rate_port = ADC
##mass_flow_controller_measure_rate_channel = 0
