#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-03-05, 2014-07-22

__translation_stage_scan_date__ = "2014-07-22"
__translation_stage_scan_version__ = __translation_stage_scan_date__

import argparse
import logging
import os
import re
import serial
import tempfile
import time

from plc_tools.plclogclasses import QueuedWatchedFileHandler

def main():
    help = ""
    help += "Examples: (After the given delays the position should be reached.)\n"
    help += " translation_stage_scan.py -repeat 1 -steps -1000000 -delay 33\n"
    help += " translation_stage_scan.py -repeat 10 -steps -100000 -delay 3.4\n"
    help += " translation_stage_scan.py -repeat 100 -steps -10000 -delay 0.4\n"
    help += " translation_stage_scan.py -repeat 1000 -steps -1000 -delay 0.1\n"
    help += " translation_stage_scan.py -repeat 10000 -steps -100 -delay 0.036\n"
    help += " translation_stage_scan.py -repeat 100000 -steps -10 -delay 0.036 # caution: heat!! \n"
    help += " translation_stage_scan.py -repeat 1000000 -steps -1 -delay 0.036 # caution: heat!!! \n"
    parser = argparse.ArgumentParser(
        description="translation_stage_scan.py is a simple tool to perform a scan with the translation stage. The device must be already powered.\nThis script initialize repeatedly some steps and a delay. Optionally the default position should be reached after all.\n\nA quick and dirty measurement gives us 1000000 steps for 7.8 cm in about 33 seconds.\n\nThe timestamps of the positions in the log file are only based on the commands. From 'initiated next position' it takes some time to perform your choosen steps. They should be reached exactly in this time. The position information is given at the time of the answer from the device; not when it is reached! So again, the timestamp of 'initiated next position' added by the necessary time delay to perform your choosen steps should be the time when the device reached the next position.",
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__translation_stage_scan_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-direction',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='direction',
                        help='Set the directions. (0: x; 1: y; 2: z) default: 1',
                        metavar='xyz')
    parser.add_argument('-repeat',
                        nargs=1,
                        default=2,
                        type=int,
                        required=False,
                        dest='repeat',
                        help='Set the number of repeatations. default: 2',
                        metavar='n')
    parser.add_argument('-steps',
                        nargs=1,
                        default=100,
                        type=int,
                        required=False,
                        dest='steps',
                        help='Set the number of steps to do each time. default: 100',
                        metavar='n')
    parser.add_argument('-delay',
                        nargs=1,
                        default=0.1,
                        type=float,
                        required=False,
                        dest='delay',
                        help='Set the delay between the repeatations in seconds. default: 0.1',
                        metavar='t')
    parser.add_argument('-set_zero_position',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='set_zero_position',
                        help='If set to 1 the zero position will be set at the beginning of the communication. default: 1',
                        metavar='x')
    parser.add_argument('-go_back',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='go_back',
                        help='If set to 1 go back to the start position after all. default: 1',
                        metavar='x')
    parser.add_argument('-go_direct_back',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='go_direct_back',
                        help='If set to 1 go direct back to the start position after all. default: 1',
                        metavar='x')

    parser.add_argument('-device',
                        nargs=1,
                        default="/dev/TSCftBNKEKX",
                        type=str,
                        required=False,
                        dest='device',
                        help='Set the external device dev to communicate with the box. default: /dev/TSCftBNKEKX',
                        metavar='dev')
    parser.add_argument('-baudrate',
                        nargs=1,
                        default=9600,
                        type=int,
                        required=False,
                        dest='baudrate',
                        help='Set the baudrate. default: 9600',
                        metavar='n')
    parser.add_argument('-databits',
                        nargs=1,
                        default=8,
                        type=int,
                        required=False,
                        dest='databits',
                        help='Set the databits. default: 8',
                        metavar='n')
    parser.add_argument('-stopbits',
                        nargs=1,
                        default="1",
                        type=str,
                        required=False,
                        dest='stopbits',
                        help='Set the stopbits. (possible values: 1, 1.5, 2) default: 1',
                        metavar='n')
    parser.add_argument('-logfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"translation_stage_scan.log"),
                        type=str,
                        required=False,
                        dest='logfile',
                        help='Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"translation_stage_scan.log"),
                        metavar='f')
    args = parser.parse_args()
    if not isinstance(args.direction,int):
        args.direction = args.direction[0]
    if not isinstance(args.repeat,int):
        args.repeat = args.repeat[0]
    if not isinstance(args.steps,int):
        args.steps = args.steps[0]
    if not isinstance(args.delay,float):
        args.delay = args.delay[0]
    if not isinstance(args.set_zero_position,int):
        args.set_zero_position = args.set_zero_position[0]
    if not isinstance(args.go_back,int):
        args.go_back = args.go_back[0]
    if not isinstance(args.go_direct_back,int):
        args.go_direct_back = args.go_direct_back[0]

    if not isinstance(args.device,str):
        args.device = args.device[0]
    if not isinstance(args.baudrate,int):
        args.baudrate = args.baudrate[0]
    if not isinstance(args.databits,int):
        args.databits = args.databits[0]
    if not isinstance(args.stopbits,str):
        args.stopbits = args.stopbits[0]
    if not isinstance(args.logfile,str):
        args.logfile = args.logfile[0]
    # logging
    log = logging.getLogger('tss')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    fh = QueuedWatchedFileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(created)f %(levelname)s %(message)s'))
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    ch.setFormatter(logging.Formatter('%(asctime)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    # setting variables
    stopbits = serial.STOPBITS_ONE
    if args.stopbits == "1":
        stopbits = serial.STOPBITS_ONE
    elif args.stopbits == "1.5":
        stopbits = serial.STOPBITS_ONE_POINT_FIVE
    elif args.stopbits == "2":
        stopbits = serial.STOPBITS_TWO
    parity = serial.PARITY_NONE
    
    device = serial.Serial(port=None,
                           baudrate=args.baudrate,
                           bytesize=args.databits,
                           parity=parity,
                           stopbits=stopbits,
                           timeout=0,
                           writeTimeout=0)
    device.port = args.device
    readbytes = 16384

    direction = args.direction # 0: x; 1: y; 2: z
    n = args.repeat
    steps = args.steps
    delay = args.delay
    
    device.open()
    # switch to ASCII mode
    device.write("\x01\x8b\x00\x00\x00\x00\x00\x00\x8c\r") # 0x018b 0x0000 0x0000 0x0000 0x8c
    time.sleep(0.1)
    r = device.read(readbytes)
    # get position
    device.write("AGAP 0,%d\r" % direction)
    time.sleep(0.055)
    rd = device.read(readbytes)
    r = re.findall("AGAP ([\+\-0-9]+),([\+\-0-9]+)\rBA ([\+\-0-9]+) ([\+\-0-9]+)",rd)
    if r:
        log.debug("position: %s" % r[0][3])
    else:
        log.info("cannot get position")
    if args.set_zero_position == 1:
        # set position
        log.debug("set position to 0")
        device.write("ASAP 0,%d,0\r" % direction)
        time.sleep(0.10)
        rd= device.read(readbytes)
    # get position
    device.write("AGAP 0,%d\r" % direction)
    time.sleep(0.055)
    startposition = None
    rd= device.read(readbytes)
    r = re.findall("AGAP ([\+\-0-9]+),([\+\-0-9]+)\rBA ([\+\-0-9]+) ([\+\-0-9]+)",rd)
    if r:
        log.info("startposition: %s" % r[0][3])
        startposition = r[0][3]
    else:
        log.info("cannot get position")

    # make steps
    log.debug("make steps...")
    make_steps(n,direction,steps,device,readbytes,log,delay)
    if args.go_back == 1:
        if args.go_direct_back == 1:
            if startposition != None:
                log.debug("go direct back to absolut startposition %s" % startposition)
                write2dev_string = "AMVP ABS,%d,%s\r" % (direction,startposition)
                device.write(write2dev_string) # ca. max. 19 Zeichen
                time.sleep(0.055)
                rd = device.read(readbytes) # ca. max. 35 Zeichen
                r = re.findall("AMVP ABS,([\+\-0-9]+),([\+\-0-9]+)\rBA ([\+\-0-9]+) ([\+\-0-9]+)",rd)
                if r:
                    log.info("position: %s" % r[0][3])
                else:
                    log.debug("write: '%s'" % write2dev_string.replace("\r",""))
                    log.debug("read: '%s'" % rd.replace("\r","\n"))
            else:
                log.debug("go direct back by %d relative steps" % (-n*steps))
                make_steps(1,direction,-n*steps,device,readbytes,log,delay)
        else:
            log.debug("go back\n")
            make_steps(n,direction,-steps,device,readbytes,log,delay)

    device.close()
    log.debug("Program is ready. Device may be still busy!")

def make_steps(n,direction,steps,device,readbytes,log,delay):
    t0 = time.time()
    for i in range(n):
        write2dev_string = "AMVP REL,%d,%d\r" % (direction,steps)
        device.write(write2dev_string) # ca. max. 19 Zeichen
        log.debug("initiated next position")
        time.sleep(0.055)
        rd = device.read(readbytes) # ca. max. 35 Zeichen
        r = re.findall("AMVP REL,([\+\-0-9]+),([\+\-0-9]+)\rBA ([\+\-0-9]+) ([\+\-0-9]+)",rd)
        if r:
            log.info("position: %s" % r[0][3])
        else:
            log.debug("write: '%s'\n" % write2dev_string.replace("\r",""))
            log.debug("read: '%s'\n" % rd.replace("\r","\n"))
        t1 = time.time()
        time.sleep(max(0,delay-(t1-t0)))
        t0 = time.time()

if __name__ == "__main__":
    main()
