#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2012-09-18, 2013-02-04, 2013-04-22, 2014-07-22, 2017-05-30

__logs2housekeeping_date__ = "2017-05-30"
__logs2housekeeping_version__ = __logs2housekeeping_date__

import argparse
import os
import tarfile
import time
import logging
import logging.handlers
#import string
import re
import io
import PIL.Image

def main():
    # command line parameter
    parser = argparse.ArgumentParser(
        description='logs2housekeeping.py',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n" % __logs2housekeeping_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    parser.add_argument('-f',
                        nargs="+",
                        type=str,
                        required=True,
                        dest='file',
                        help='will convert this/theses file(s)',
                        metavar='file')
    parser.add_argument('-outfile',
                        nargs=1,
                        default="data.txt",
                        type=str,
                        required=False,
                        dest='outfile',
                        help='Set the output file. Default: data.txt',
                        metavar='file')
    args = parser.parse_args()
    configname = ""
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.outfile,str):
        args.outfile = args.outfile[0]
    # logging
    log = logging.getLogger('logs2housekeeping')
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
    log.info("start logging in rawmovies2recordings: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    # do something
    fd = io.StringIO()
    for f in args.file:
        log.debug("file: %s" % f)
        if os.path.isfile(f):
            p = False
            fdt = open(f,'r')
            lines = fdt.readlines()
            fdt.close()
            for l in lines:
                # plc
                # 1347252790.953912 plc.plc_gui INFO set flow rate to 40959 (2.500000 V, 500.000000 msccm)
                r = re.findall("([0-9\.]+) [^\n]* set flow rate to ([^\n]*)",l)
                if r:
                    fd.write("%s\tset flow rate to %s\n" % (r[0][0],r[0][1]))
                # 1347255907.964994 plc.rf_gen_ctrl INFO to rf-gen 0: @X08@P00000000@D
                r = re.findall("([0-9\.]+) [^\n]* to rf-gen ([0-9]+): ([^\n]*)",l)
                if r:
                    fd.write("%s\tto rf-gen %s: %s\n" % (r[0][0],r[0][1],r[0][2]))
                # 1347255907.965462 plc.rf_gen_ctrl INFO to rf-dc 0: #O#D0000000000000000
                r = re.findall("([0-9\.]+) [^\n]* to rf-dc ([0-9]+): ([^\n]*)",l)
                if r:
                    fd.write("%s\tto rf-dc %s: %s\n" % (r[0][0],r[0][1],r[0][2]))
                # 1347256512.197234 plc.plc_gui INFO shake dispenser1
                r = re.findall("([0-9\.]+) [^\n]* shake dispenser([0-9]+)",l)
                if r:
                    fd.write("%s\tshake dispenser%s\n" % (r[0][0],r[0][1]))
                # 1347257788.947600 plc.plc_gui DEBUG choose setpoints 14: parabola 12 -- few particles 60Pa RF 1000 - 4 electrodes
                r = re.findall("([0-9\.]+) [^\n]* choose setpoints ([0-9]+): ([^\n]*)",l)
                if r:
                    fd.write("%s\tchoose setpoints %s: %s\n" % (r[0][0],r[0][1],r[0][2]))
                # 1347257798.898997 plc.plc_gui DEBUG set setpoints 14: parabola 12 -- few particles 60Pa RF 1000 - 4 electrodes
                r = re.findall("([0-9\.]+) [^\n]* set setpoints ([0-9]+): ([^\n]*)",l)
                if r:
                    fd.write("%s\tchoose set %s: %s\n" % (r[0][0],r[0][1],r[0][2]))
                # MPC
                # 1347250951.324165 MPC0006 [I] Transmitted:@Q000D0000000000000000A07FA094C20BD000120C620CB20D220D8IFC.
                r = re.findall("([0-9\.]+) [^\n]* Transmitted:([^\n]*).",l)
                if r:
                    fd.write("%s\tMPC transmitted: %s\n" % (r[0][0],r[0][1]))
    contents = fd.getvalue()
    scontents = string.join(sorted(contents.split("\n")),"\n")
    fd.close()
    fd = open(args.outfile,'a')
    fd.write(scontents)
    fd.close()

if __name__ == "__main__":
    main()
