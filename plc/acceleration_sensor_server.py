#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-05-13, 2014-07-22

__acceleration_sensor_server_date__ = "2014-07-22"
__acceleration_sensor_server_version__ = __acceleration_sensor_server_date__

import argparse
import csv
import errno
import logging
import logging.handlers
import math
import os
import re
import serial
import signal
import socket
import socketserver
import string
import struct
import sys
import tempfile
import threading
import time
import types
import usb

from plc_tools.plclogclasses import QueuedWatchedFileHandler
import plc_tools.plc_socket_communication

MAX_ISERIAL_LEN=8

class controller_class():
    """controller_class
    
    This class is for communicating to a device. This means
    setvalues are required by the user and will be set in some
    intervals. The actualvalues are the actualvalues which were
    set before.
    
    Author: Daniel Mohr
    Date: 2012-12-05
    """
    def __init__(self,log=None,datalog=None,idVendor=None,idProduct=None,SerialNumber=None,devid=None,datalogformat=None,maxg=None):
        self.log = log
        self.datalog = datalog
        self.idVendor = idVendor
        self.idProduct = idProduct
        self.SerialNumber = SerialNumber
        self.devid = devid
        self.datalogformat = datalogformat
        self.maxg = maxg
        self.lock = threading.Lock()
        self.ring_buffer_n = 125 # the ring buffer could be used for averaging
        self.ring_buffer_n = 2 # the ring buffer could be used for averaging
        self.ring_buffer = self.ring_buffer_n * [[0,0,0]]
        self.ring_buffer_i = 0
        self.ring_buffer_lock = []
        for i in range(self.ring_buffer_n):
            self.ring_buffer_lock += [threading.Lock()]
        self.running = True
        self.reading_thread = threading.Thread(target=self.reading)
        self.reading_thread.daemon = True # exit thread when the main thread terminates
        self.reading_thread.start()

    def __del__(self):
        self.running = False

    def reading(self):
        while self.running:
            try:
                # find our device idVendor=0x07c0, idProduct=0x1116
                dev = usb.core.find(idVendor=int(self.idVendor,16), idProduct=int(self.idProduct,16), find_all=True)
                dev_iSerialNumber = []
                for d in dev:
                    dev_iSerialNumber += [str(usb.util.get_string(d,MAX_ISERIAL_LEN,d.iSerialNumber))]
                index = None
                if len(dev) > 1:
                    self.log.warning('found %d acceleration sensors' % len(dev))
                    try:
                        index = dev_iSerialNumber.index(self.SerialNumber)
                    except:
                        pass
                if index != None:
                    self.log.debug('use %d. sensor (SerialNumber: %s)' % ((index+1),dev_iSerialNumber[index]))
                    dev = dev[index]
                else:
                    self.log.debug('use %d. sensor (SerialNumber: %s)' % ((self.devid+1),dev_iSerialNumber[self.devid]))
                    dev = dev[self.devid]
            except:
                dev = None
            # was it found?
            if dev is None:
                self.log.debug('Device was not found.')
            else:
                if dev.is_kernel_driver_active(0):
                    dev.detach_kernel_driver(0)
                    self.log.warning('detached kernel driver for 0')

                if dev.is_kernel_driver_active(1):
                    dev.detach_kernel_driver(1)
                    self.log.warning('detached kernel driver for 1')
                dev.set_configuration()
                cfg = dev.get_active_configuration()
                interface_number=0
                alternate_setting = usb.control.get_interface(dev, interface_number)
                intf = usb.util.find_descriptor(cfg, bInterfaceNumber = interface_number, bAlternateSetting=alternate_setting)
                usb.util.claim_interface(dev, intf)
                ep = usb.util.find_descriptor(intf, custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
                assert ep is not None
                self.log.debug("start reading")
                xr = 0
                yr = 0
                zr = 0
                while self.running:
                    try:
                        data = ep.read(7)
                    except:
                        break
                    t = time.time()
                    xr = struct.unpack("h",data[0:2])[0]
                    yr = struct.unpack("h",data[2:4])[0]
                    zr = struct.unpack("h",data[4:6])[0]
                    if self.datalogformat == 0:
                        self.datalog.info("%f %d %d %d" % (t,xr,yr,zr))
                    elif self.datalogformat == 1:
                        [x,y,z] = raw2g(xr,yr,zr,self.maxg)
                        self.datalog.info("%f %+1.5f %+1.5f %+1.5f" % (t,x,y,z))
                    else:
                        [x,y,z] = raw2g(xr,yr,zr,self.maxg)
                        self.datalog.info("%f %d %d %d %+1.5f %+1.5f %+1.5f" % (t,xr,yr,zr,x,y,z))
                    self.lock.acquire() # lock i
                    i = (self.ring_buffer_i+1)%self.ring_buffer_n
                    self.lock.release() # unlock i
                    self.ring_buffer_lock[i].acquire() # lock ring buffer
                    self.ring_buffer[self.ring_buffer_i] = [xr,yr,zr]
                    self.ring_buffer_lock[i].release() # unlock ring buffer
                    self.lock.acquire() # lock i
                    self.ring_buffer_i = i
                    self.lock.release() # unlock i
                if self.running:
                    self.log.warning("lost sensor")
            if self.running:
                self.log.warning("try it again in 3 seconds")
                time.sleep(3)
            else:
                self.log.debug("done!")

    def get_actualvalue(self):
        self.lock.acquire() # lock i
        i = self.ring_buffer_i
        self.lock.release() # unlock i
        self.ring_buffer_lock[i].acquire() # lock ring buffer
        a = self.ring_buffer[i]
        self.ring_buffer_lock[i].release() # unlock ring buffer
        a += [i]
        return a

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler,plc_tools.plc_socket_communication.tools_for_socket_communication):

    def handle(self):
        global controller
        controller.log.debug("start connection to %s:%s" % (self.client_address[0],self.client_address[1]))
        recv_bufsize = 4096 # read/receive Bytes at once
        data = ""
        while controller.running:
            self.request.settimeout(1)
            # get some data
            d = ""
            try:
                d = self.request.recv(recv_bufsize)
                if not d:
                    break
            except: pass
            # analyse data
            response = ""
            if len(d) > 0:
                data += d
                found_something = True
            else:
                found_something = False
            while found_something:
                found_something = False
                if (len(data) >= 6) and (data[0:6].lower() == "getact"):
                    # sends the actual values back
                    found_something = True
                    data = data[6:]
                    response += self.create_send_format(controller.get_actualvalue())
                elif (len(data) >= 4) and (data[0:4].lower() == "quit"):
                    found_something = True
                    a = "quitting"
                    response += a
                    controller.log.info(a)
                    data = data[4:]
                    controller.running = False
                    self.server.shutdown()
                elif (len(data) >= 4) and (data[0:7].lower() == "version"):
                    found_something = True
                    a = "acceleration_sensor_server.py Version: %s" % __acceleration_sensor_server_version__
                    response += self.create_send_format(a)
                    controller.log.debug(a)
                    data = data[7:]
                if len(data) == 0:
                    break
            if len(response) > 0:
                self.send_data_to_socket(self.request,response)

    def send_data_to_socket(self,s,msg):
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = s.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def finish(self):
        controller.log.debug("stop connection to %s:%s" % (self.client_address[0],self.client_address[1]))
        try:
            self.request.shutdown(socket.SHUT_RDWR)
        except:
            pass

def raw2g(xr,yr,zr,maxg):
    x = maxg * float(xr - 2**13) / 2**13
    y = -maxg * float(yr - 2**13) / 2**13 # y is inverted
    z = maxg * float(zr - 2**13) / 2**13
    return [x,y,z]

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def shutdown(signum,frame):
    global controller
    controller.log.info("got signal %d" % signum)
    controller.log.debug("number of threads: %d" % threading.activeCount())
    controller.log.info("will exit the program")
    controller.__del__()

def main():
    global controller
    # command line parameter
    help = ""
    help += "Over the given port on the given address a socket communication is "
    help += "lisening with the following commands: (This is a prefix-code. Upper or lower letters do not matter.)\n"
    help += "  getact : sends the actual values back as [pickle data]\n"
    help += "  quit : quit the server\n"
    help += "  version : response the version of the server\n"
    parser = argparse.ArgumentParser(
        description='acceleration_sensor_server.py is a socket server to read and log the measurements from the acceleration sensor JoyWarrior24F14. A friendly kill (SIGTERM) should be possible.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__acceleration_sensor_server_version__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
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
    parser.add_argument('-logfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"acceleration.log"),
                        type=str,
                        required=False,
                        dest='logfile',
                        help='Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"acceleration.log"),
                        metavar='f')
    parser.add_argument('-datalogfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"acceleration.data"),
                        type=str,
                        required=False,
                        dest='datalogfile',
                        help='Set the datalogfile to f. Only the measurements will be logged here. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"acceleration.data"),
                        metavar='f')
    parser.add_argument('-datalogformat',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='datalogformat',
                        help='Set the log format for the data: 0 raw format; 1 value in g; 2 both. default: 0',
                        metavar='f')
    parser.add_argument('-maxg',
                        nargs=1,
                        default=2.0,
                        type=float,
                        required=False,
                        dest='maxg',
                        help='Set the measurement range in g. default 2 for +-2g',
                        metavar='x')
    parser.add_argument('-runfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"acceleration_sensor.pids"),
                        type=str,
                        required=False,
                        dest='runfile',
                        help='Set the runfile to f. If an other process is running with a given pid and reading the same SerialNumber, the program will not start. Setting f=\"\" will disable this function. default: %s' % os.path.join(tempfile.gettempdir(),"acceleration_sensor.pids"),
                        metavar='f')
    parser.add_argument('-ip',
                        nargs=1,
                        default="localhost",
                        type=str,
                        required=False,
                        dest='ip',
                        help='Set the IP/host n to listen. If ip == \"\" the default behavior will be used; typically listen on all possible adresses. default: localhost',
                        metavar='n')
    parser.add_argument('-port',
                        nargs=1,
                        default=15123,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15123',
                        metavar='p')
    parser.add_argument('-choosenextport',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='choosenextport',
                        help='By specifying this flag the next available port after the given one will be choosen. Without this flag a socket.error is raised if the port is not available.')
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
    if not isinstance(args.datalogfile,str):
        args.datalogfile = args.datalogfile[0]
    if not isinstance(args.runfile,str):
        args.runfile = args.runfile[0]
    if not isinstance(args.ip,str):
        args.ip = args.ip[0]
    if not isinstance(args.port,int):
        args.port = args.port[0]
    if not isinstance(args.choosenextport,bool):
        args.choosenextport = args.choosenextport[0]
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
    if not isinstance(args.datalogformat,int):
        args.datalogformat = args.datalogformat[0]
    if not isinstance(args.maxg,float):
        args.maxg = args.maxg[0]
    # logging
    log = logging.getLogger('as')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    #fh = logging.handlers.WatchedFileHandler(args.logfile)
    fh = QueuedWatchedFileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(created)f %(levelname)s %(message)s'))
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO) # logging.WARNING = 30
    ch.setFormatter(logging.Formatter('%(asctime)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    datalog = logging.getLogger('asd')
    datalog.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    #fhd = logging.handlers.WatchedFileHandler(args.datalogfile)
    fhd = QueuedWatchedFileHandler(args.datalogfile)
    fhd.setLevel(logging.DEBUG)
    #fhd.setFormatter(logging.Formatter('%(created)f %(message)s'))
    fhd.setFormatter(logging.Formatter('%(message)s'))
    datalog.addHandler(fhd)
    log.info("start logging in acceleration_sensor_server: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.info("logging to \"%s\" and data to \"%s\"" % (args.logfile,args.datalogfile))
    # listsensors
    if args.listsensors:
        dev = usb.core.find(idVendor=int(args.idVendor,16), idProduct=int(args.idProduct,16), find_all=True)
        dev_iSerialNumber = []
        for d in dev:
            dev_iSerialNumber += [str(usb.util.get_string(d,MAX_ISERIAL_LEN,d.iSerialNumber))]
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
    signal.signal(signal.SIGTERM,shutdown)
    # check runfile
    if args.runfile != "":
        ori = [os.getpid(),args.SerialNumber]
        runinfo = [ori]
        if os.path.isfile(args.runfile):
            # file exists, read it
            f = open(args.runfile,'r')
            reader = csv.reader(f)
            r = False # assuming other pid is not running; will be corrected if more information is available
            for row in reader:
                # row[0] should be a pid
                # row[1] should be the SerialNumber
                rr = False
                if os.path.exists(os.path.join("/proc","%d" % os.getpid())): # checking /proc available
                    if os.path.exists(os.path.join("/proc","%d" % int(row[0]))): # check if other pid is running
                        ff = open(os.path.join("/proc","%d" % int(row[0]),"cmdline"),'rt')
                        cmdline = ff.read(1024*1024)
                        ff.close()
                        if re.findall(__file__,cmdline):
                            rr = True
                            log.debug("process %d is running (proc)" % int(row[0]))
                else: # /proc is not available; try kill, which only wirks on posix systems
                    try:
                        os.kill(int(row[0]),0)
                    except OSError as err:
                        if err.errno == errno.ESRCH:
                            # not running
                            pass
                        elif err.errno == errno.EPERM:
                            # no permission to signal this process; assuming it is another kind of process
                            pass
                        else:
                            # unknown error
                            raise
                    else: # other pid is running
                        rr = True # assuming this is the same kind of process
                        log.debug("process %d is running (kill)" % int(row[0]))
                if rr and row[1] != args.SerialNumber: # checking iff same SerialNumber
                    runinfo += [[row[0],row[1]]]
                elif rr:
                    r = True
            f.close()
            if r:
                log.debug("other process is running; exit.")
                sys.exit(1)
        f = open(args.runfile,'w')
        writer = csv.writer(f)
        for i in range(len(runinfo)):
            writer.writerows([runinfo[i]])
        f.close()
    # go in background if useful
    if args.debug == 0:
        # go in background
        log.info("go to background (fork)")
        newpid = os.fork()
        if newpid > 0:
            log.info("background process pid = %d" % newpid)
            sys.exit(0)
        elif args.runfile != "":
            nri = [os.getpid(),args.SerialNumber]
            index = runinfo.index(ori)
            runinfo[index] = nri
            f = open(args.runfile,'w')
            writer = csv.writer(f)
            for i in range(len(runinfo)):
                writer.writerows([runinfo[i]])
                f.close()
        log.removeHandler(ch)
        # threads in the default process are dead
        # in particular this means QueuedWatchedFileHandler is not working anymore
        fh.startloopthreadagain()
        fhd.startloopthreadagain()
        log.info("removed console log handler")
    else:
        log.info("due to debug=1 will _not_ go to background (fork)")
    controller = controller_class(log=log,datalog=datalog,idVendor=args.idVendor,idProduct=args.idProduct,SerialNumber=args.SerialNumber,devid=args.id,datalogformat=args.datalogformat,maxg=args.maxg)
    s = True
    while s:
        s = False
        try:
            server = ThreadedTCPServer((args.ip,args.port), ThreadedTCPRequestHandler)
        except socket.error:
            if not args.choosenextport:
                controller.running = False
            if not args.choosenextport:
                raise
            s = True
            log.error("port %d is in use" % args.port)
            args.port += 1
            log.info("try port %d" % args.port)
    ip, port = server.server_address
    log.info("listen at %s:%d" % (ip,port))
    # start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    while controller.running:
        time.sleep(1) # it takes at least 1 second to exit
    log.debug("exit")
    fhd.flush()
    fhd.close()
    fh.flush()
    fh.close()
    if args.debug != 0:
        ch.flush()
        ch.close()
    sys.exit(0)

if __name__ == "__main__":
    main()
