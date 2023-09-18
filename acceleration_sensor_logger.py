#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-01-26, 2014-07-22

__acceleration_sensor_logger_date__ = "2014-07-22"
__acceleration_sensor_logger_version__ = __acceleration_sensor_logger_date__

import argparse
import logging
import logging.handlers
import struct
import sys
import time
import usb
import os
import tempfile

from plc_tools.plclogclasses import QueuedWatchedFileHandler

MAX_ISERIAL_LEN=8

def main():
    # command line parameter
    help = ""
    help += "This is a simple command line program. You can plot the logfile with gnuplot.\n\n"
    help += "A few examples:\n\n"
    help += "  plot 'acceleration.log' using 1:2 with lines title 'x',\\\n"
    help += "       'acceleration.log' using 1:3 with lines title 'y',\\\n"
    help += "       'acceleration.log' using 1:4 with lines title 'z'\n\n"
    help += "  plot 'acceleration.log' using ($1-1350411408.795725):2 with lines title 'x',\\\n"
    help += "       'acceleration.log' using ($1-1350411408.795725):3 with lines title 'y',\\\n"
    help += "       'acceleration.log' using ($1-1350411408.795725):4 with lines title 'z'\n\n"
    help += "  set xdata time ; set timefmt '%s' ; set format x '%H:%M'\n"
    help += "  plot 'acceleration.log' using 1:2 with lines title 'x',\\\n"
    help += "       'acceleration.log' using 1:3 with lines title 'y',\\\n"
    help += "       'acceleration.log' using 1:4 with lines title 'z'\n"
    help += "\nYou need access to the device of the sensor.\n"
    help += "For example you can use the following udev rule:\n"
    help += "  SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"07c0\", ATTRS{idProduct}==\"1116\", MODE:=\"666\", GROUP=\"users\"\n"
    parser = argparse.ArgumentParser(
        description='acceleration_sensor_logger.py logs measurements from the JoyWarrior24F14 to a logfile. You need access to the device.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__acceleration_sensor_logger_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-logfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"acceleration.log"),
                        type=str,
                        required=False,
                        dest='logfile',
                        help='Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"acceleration.log"),
                        metavar='f')
    parser.add_argument('-idVendor',
                        nargs=1,
                        default='0x07c0',
                        type=str,
                        required=False,
                        dest='idVendor',
                        help='Set the idVendor of the acceleration sensor. default: 0x07c0',
                        metavar='x')
    parser.add_argument('-idProduct',
                        nargs=1,
                        default='0x1116',
                        type=str,
                        required=False,
                        dest='idProduct',
                        help='Set the idProduct of the acceleration sensor. default: 0x1116',
                        metavar='x')
    parser.add_argument('-listsensors',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='listsensors',
                        help='Will list the acceleration sensor(s) and exit.')
    parser.add_argument('-SerialNumber',
                        nargs=1,
                        default='',
                        type=str,
                        required=False,
                        dest='SerialNumber',
                        help='Set the SerialNumber of the acceleration sensor. If given try to find this sensor otherwise use the one given by id.',
                        metavar='x')
    parser.add_argument('-id',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='id',
                        help='Set the id to i. If there are more than 1 acceleration sensor and there is no SerialNumber or the SerialNumber was not found, the i-th one will be choosen.',
                        metavar='i')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    args = parser.parse_args()
    if not isinstance(args.logfile,str):
        args.logfile = args.logfile[0]
    if not isinstance(args.idVendor,str):
        args.idVendor = args.idVendor[0]
    if not isinstance(args.idProduct,str):
        args.idProduct = args.idProduct[0]
    if not isinstance(args.listsensors,bool):
        args.listsensors = args.listsensors[0]
    if not isinstance(args.SerialNumber,str):
        args.SerialNumber = args.SerialNumber[0]
    if not isinstance(args.id,int):
        args.id = args.id[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]

    # logging
    log = logging.getLogger()
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    #fh = logging.handlers.WatchedFileHandler(args.logfile)
    fh = QueuedWatchedFileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(created)f %(message)s'))
    log.addHandler(fh)
    # create console handler
    ch = logging.StreamHandler()
    if args.debug == 1:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.WARNING) # logging.WARNING = 30
    ch.setFormatter(logging.Formatter('%(asctime)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(ch)

    # find our device idVendor=0x07c0, idProduct=0x1116
    dev = usb.core.find(idVendor=int(args.idVendor,16), idProduct=int(args.idProduct,16), find_all=True)
    dev_iSerialNumber = []
    for d in dev:
        dev_iSerialNumber += [str(usb.util.get_string(d,MAX_ISERIAL_LEN,d.iSerialNumber))]
    if args.listsensors:
        for i in range(len(dev)):
            if dev[i].is_kernel_driver_active(0):
                dev[i].detach_kernel_driver(0)
                log.warning('detached kernel driver for 0')
            if dev[i].is_kernel_driver_active(1):
                dev[i].detach_kernel_driver(1)
                log.warning('detached kernel driver for 1')
        print("id: SerialNumber, bMaxPower (mA)")
        for i in range(len(dev)):
            dev[i].set_configuration()
            cfg = dev[i].get_active_configuration()
            print(("%d: %s, %d" % (i,dev_iSerialNumber[i],2*int(cfg.bMaxPower))))
        sys.exit(0)
    index = None
    if len(dev) > 1:
        log.warning('found %d acceleration sensors' % len(dev))
        try:
            index = dev_iSerialNumber.index(args.SerialNumber)
        except:
            pass
    if index != None:
        log.debug('use %d. sensor (SerialNumber: %s)' % ((index+1),dev_iSerialNumber[index]))
        dev = dev[index]
    else:
        log.debug('use %d. sensor (SerialNumber: %s)' % ((args.id+1),dev_iSerialNumber[args.id]))
        dev = dev[args.id]

    # was it found?
    if dev is None:
        raise ValueError('Device was not found.')

    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)
        log.warning('detached kernel driver for 0')

    if dev.is_kernel_driver_active(1):
        dev.detach_kernel_driver(1)
        log.warning('detached kernel driver for 1')

    dev.set_configuration()

    cfg = dev.get_active_configuration()
    interface_number=0
    alternate_setting = usb.control.get_interface(dev, interface_number)

    intf = usb.util.find_descriptor(cfg, bInterfaceNumber = interface_number, bAlternateSetting=alternate_setting)

    usb.util.claim_interface(dev, intf)

    ep = usb.util.find_descriptor(intf, custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    assert ep is not None

    import math
    while True:
        try:
            data = ep.read(7)	
            x = struct.unpack("h",data[0:2])[0]
            y = struct.unpack("h",data[2:4])[0]
            z = struct.unpack("h",data[4:6])[0]
            x = 2 * float(x - 2**13) / 2**13
            y = -2 * float(y - 2**13) / 2**13 # y is inverted
            z = 2 * float(z - 2**13) / 2**13
            log.info("%+1.5f %+1.5f %+1.5f" % (x,y,z))
        except:
            break
        #time.sleep(1)

    log.debug("done!")

if __name__ == "__main__":
    main()
