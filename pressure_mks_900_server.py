#!/usr/bin/python -O
# Author: Richard Schlitz, Daniel Mohr
# Date: 2013-01-26, 2014-07-22

__pressure900_server_date__ = "2014-07-22"
__pressure900_server_version__ = __pressure900_server_date__

import argparse
import pickle
import csv
import errno
import logging
import logging.handlers
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

from plc_tools.plclogclasses import QueuedWatchedFileHandler

class controller_class():
    """controller_class

    This class is for communicating to a device. This means
    setvalues are required by the user and will be set in some
    intervals. The actualvalues are the actualvalues which were
    set before.
    """
    def __init__(self,log=None,device=None,updatedelay=1,PR=None,UNIT=None,GT=None):
        global controller
        self.log = log
        self.devicename = device
        self.deviceopen = False
        self.boudrate = 9600
        self.databits = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE # serial.STOPBITS_ONE_POINT_FIVE serial.STOPBITS_TWO
        self.readtimeout = 2
        self.writetimeout = 2
        self.device = serial.Serial(port=None,
                                    baudrate=self.boudrate,
                                    bytesize=self.databits,
                                    parity=self.parity,
                                    stopbits=self.stopbits,
                                    timeout=self.readtimeout,
                                    writeTimeout=self.writetimeout)
        self.device.port = self.devicename
        self.communication_problem = 0
        self.lock = threading.Lock()
        self.updatelock = threading.Lock()
        self.write_to_device_lock = threading.Lock()
        self.set_actualvalue_to_the_device_lock = threading.Lock()
        self.get_actualvalue_from_the_device_lock = threading.Lock()
        self.actualvalue = {'PR': "",'U':"",'GC':"",'GT':""}
        # contains the actualvalues in acualvalue[key]
        # PR contains active filament
        # U contains active unit
        # GC contains active gas correction
        # GT contains active gas type
        self.pressure = ""
        # contains pressure
        self.get_actualvalue_from_the_device()
        if (PR != None and PR != ""):
            self.actualvalue['PR'] = PR
        else:
            self.actualvalue['PR'] = "PR3"
        self.setpoint = self.actualvalue.copy()
        if (UNIT != None and UNIT != ""):
            self.setpoint['U'] = UNIT
        if (GT != None and GT != ""):
            self.setpoint['GT'] = GT
        #print self.setpoint
        self.set_actualvalue_to_the_device()
        self.updatedelay = updatedelay # seconds
        self.running = True
        self.lastupdate = None
        self.updatetimer = threading.Timer(self.updatedelay,self.update)
        self.updatetimer.start()



    def update(self):
        """update

        will update every updatedelay seconds
        """
        global controller
        #print "updating now"
        self.updatetimer.cancel()
        self.updatelock.acquire() # lock for running
        if self.running:
            if self.lastupdate == None:
                t = self.updatedelay
            else:
                t = max(0.000001,self.updatedelay + self.updatedelay - (time.time()-self.lastupdate))
            self.lastupdate = time.time()
            self.updatetimer = threading.Timer(t,self.update)
            self.updatetimer.start()
        else:
            return
        self.set_actualvalue_to_the_device()
        self.updatelock.release() # release the lock

    def shutdown(self):
        self.log.info("shutdown")
        self.running = False
        try:
            self.updatetimer.cancel()
        except:
            pass
        if self.device.isOpen():
            self.device.close()
            self.deviceopen = False

    def get_actualvalue_from_the_device(self):
        self.get_actualvalue_from_the_device_lock.acquire() #lock to read data
        s=""
        #print self.write_to_device("@253GC?;FF")
        for i in self.actualvalue:
            if ('PR' != i):
                s="@001%s?;FF" % i
                self.actualvalue[i] = self.write_to_device(s)
        #print self.actualvalue['GC']
        if (type(self.actualvalue['GC'])==type("") or type(self.actualvalue['GC'])==type(1)):
            self.actualvalue['GC'] = float(self.actualvalue['GC'])
        self.get_actualvalue_from_the_device_lock.release() # release the lock



    def set_actualvalue_to_the_device(self):
        # will set the actualvalue to the device
        self.set_actualvalue_to_the_device_lock.acquire() # lock to write data
        # write actualvalue to the device
        s = ''
        for i in self.actualvalue:
            if ('PR' != i and self.actualvalue[i] != self.setpoint[i]):
                s = '@001%s!%s;FF' % (i,self.setpoint[i])
                self.actualvalue[i] = self.write_to_device(s)
            elif ('PR' == i and self.actualvalue[i] != self.setpoint[i]):
                self.actualvalue[i] = self.setpoint[i]
        if (type(self.actualvalue['GC'])==type("") or type(self.actualvalue['GC'])==type(1)):
            self.actualvalue['GC'] = float(self.actualvalue['GC'])
        self.pressure = self.write_to_device('@001%s?;FF' % self.actualvalue['PR'])
        # write to device
        #print "act",self.actualvalue,"press" ,self.pressure
        if self.communication_problem == -1:
            self.communication_problem = 0
            self.log.warning("write everything to device")
            # try it again
            s = ''
            for i in self.actualvalue:
                if ('PR' != i):
                    s = '@001%s!;FF' % i
                    self.write_to_device(s)
        self.set_actualvalue_to_the_device_lock.release() # release the lock

    def wrd(self, data):
        data = data.encode() if data is not None else None
        return self.device.write(data)

    def write_to_device(self,s):
        global controller
        if len(s)==0:
            return
        if self.device == None or self.devicename == "":
            self.log.warning("no device given; can't write to device!")
            self.log.debug("out: %s" % s)
            return
        self.write_to_device_lock.aquire()
        if not self.deviceopen:
            self.device.open()
            if self.device.isOpen():
                self.device.close()
                self.device.open()
            self.deviceopen = True
            self.log.debug("device.isOpen() - %s" % self.device.isOpen())
            self.log.debug("Adress: Bytes written - %s, Receive - %s" % (self.wrd("@254AD?;FF"), self.device.read(13)))
        self.wrd(s)
        self.device.flush()
        #self.log.debug("SEND: %s" % s)
        r = self.device.read(7)
        #self.log.debug("RECEIVE: %s" % r)
        if r != '@001ACK' and r != '@253ACK': #check whether command was recognised
            self.log.warning("communication problem with device %s" % self.devicename)
            self.communication_problem += 1
            if self.communication_problem >= 3:
                self.log.warning("%d communication problems; will restart the device" % self.communication_problem)
                self.device.flushInput()
                self.device.flushOutput()
                self.device.close()
                self.device.open()
                self.communication_problem = -1
                r = None
        else: #if command is recognised read up to ";" + 2 bytes
            dummy = self.device.read()
            r = ''
            while(';' != dummy):
                r+=dummy
                dummy = self.device.read()
            dummy = self.device.read(2)
            self.log.debug("SENDRECEIVE: %s%s" % (s,r))
        self.write_to_device_lock.release()
        return r


    def set_setpoint(self,s=None):
        if s != None:
            self.setpoint = s


    def get_actualvalue(self):
        self.lock.acquire()
        a = self.actualvalue
        self.lock.release()
        return a

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        global controller
        # actual thread information:
        # cur_thread = threading.current_thread()
        # cur_thread.name
        #
        controller.log.debug("start connection to %s:%s" % (self.client_address[0],self.client_address[1]))
        data = ""
        while controller.running:
            self.request.settimeout(1)
            # get some data
            d = ""
            try:
                d = self.request.recv(1024*1024)
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
                if (len(data) >= 6) and (data[0:6].lower() == "setact"):
                    # packed data; all settings at once
                    found_something = True
                    tmpdata = data[6:]
                    #print tmpdata
                    r = re.findall("^([0-9]+) ",tmpdata)
                    totalbytes = 0
                    #print r
                    if r:
                        totalbytes = 6 + len(r[0]) + 1 + int(r[0])
                        while len(data) < totalbytes:
                            data += self.socket.recv(1024*1024)
                        length = int(r[0])
                        data = data[7+len(r[0]):]
                        v = pickle.loads(data[0:length])
                        data = data[length:]
                        controller.set_setpoint(s=v)
                elif (len(data) >= 6) and (data[0:6].lower() == "getact"):
                    # sends the actual values back
                    found_something = True
                    s = pickle.dumps(controller.get_actualvalue(),-1)
                    response += '%d %s' % (len(s),s)
                    data = data[6:]
                elif (len(data) >= 12) and (data[0:9].lower() == "timedelay"):
                    found_something = True
                    v = int(data[9:12])
                    controller.log.debug("set timedelay/updatedelay to %d milliseconds" % v)
                    controller.updatedelay = v/1000.0
                    data = data[12:]
                elif (len(data) >= 4) and (data[0:4].lower() == "quit"):
                    found_something = True
                    a = "quitting"
                    response += a
                    controller.log.info(a)
                    data = data[4:]
                    controller.running = False
                    self.server.shutdown()
                elif (len(data) >= 7) and (data[0:7].lower() == "version"):
                    found_something = True
                    a = "pressure900_server Version: %s" % __pressure900_server_version__
                    response += a
                    controller.log.debug(a)
                    data = data[7:]
                elif (len(data) >= 1) and (data[0].lower() == "p"): # pressure
                    #print data
                    found_something = True
                    s = pickle.dumps(controller.pressure)
                    response+='%d %s' % (len(s),s)
                    data=data[1:]
                if len(data) == 0:
                    break
            if len(response) > 0:
                #self.request.sendall(response)
                self.send_data_to_socket(self.request,response)
                #controller.log.debug("send to socket \"%s\"" % response)

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

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def shutdown(signum,frame):
    global controller
    controller.log.info("got signal %d" % signum)
    controller.log.debug("number of threads: %d" % threading.activeCount())
    controller.log.info("will exit the program")
    controller.shutdown()

def main():
    global controller
    # command line parameter
    help = ""
    help += "Over the given port on the given address a socket communication is "
    help += "listening with the following commands: (This is a prefix-code. Upper or lower letters do not matter.)\n"
    help += "  p : returns the pressure to the client\n"
    help += "  setact : sets the setpoint to a given setpoint received as [pickle data]\n"
    help += "  getact : sends the actual values back as [pickle data]\n"
    help += "  timedelay000 : set the time between 2 actions to 000 milliseconds.\n"
    help += "  quit : quit the server\n"
    help += "  version : response the version of the server\n"
    #done ---- (below) (( i hope so :) ))
    parser = argparse.ArgumentParser(
        description='pressure900_server is a socket server to control the MKS-PDR900-1 controller on a serial interface. On start all settings are fetched from the controller and then reset with the initialization values. A friendly kill (SIGTERM) should be possible.',
        epilog="Author: Richard Schlitz\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__pressure900_server_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # device /dev/MKS_P900_1
    # IP to listen
    # port to listen
    # logfile /data/logs/MKS_P900_1.log
    # delay time between 2 actions
    parser.add_argument('-device',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='device',
                        help='Set the external device dev to communicate with the box.',
                        metavar='dev')
    parser.add_argument('-logfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"pressure_controller.log"),
                        type=str,
                        required=False,
                        dest='logfile',
                        help='Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"pressure_controller.log"),
                        metavar='f')
    parser.add_argument('-runfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"pressure_controller.pids"),
                        type=str,
                        required=False,
                        dest='runfile',
                        help='Set the runfile to f. If an other process is running with a given pid and writing to the same device, the program will not start. Setting f=\"\" will disable this function. default: %s' % os.path.join(tempfile.gettempdir(),"pressure_controller.pids"),
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
                        default=15121,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15121',
                        metavar='p')
    parser.add_argument('-timedelay',
                        nargs=1,
                        default=0.05,
                        type=float,
                        required=False,
                        dest='timedelay',
                        help='Set the time between 2 actions to t seconds. default: t = 0.05',
                        metavar='t')
    parser.add_argument('-choosenextport',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='choosenextport',
                        help='By specifying this flag the next available port after the given one will be choosen. Without this flag a socket.error is raised if the port is not available.')
    parser.add_argument('-PR',
                        nargs=1,
                        default="PR3",
                        type=str,
                        required=False,
                        dest='PR',
                        help='Set the default values for the filament to use for measuring the pressure (PR1,PR2,PR3); default: d = \"PR3\"',
                        metavar='d')
    parser.add_argument('-U',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='U',
                        help='Set the default unit for the pressure controller to use (MBAR,TORR,PASCAL); default: d = PRESET',
                        metavar='d')
    parser.add_argument('-GT',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='GT',
                        help='Set the default gas type for the pressure controller to use (ARGON,NITROGEN,AIR,HYDROGEN,HELIUM); default: d = PRESET',
                        metavar='d')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    args = parser.parse_args()

    if not isinstance(args.device,str):
        args.device = args.device[0]
    if not isinstance(args.logfile,str):
        args.logfile = args.logfile[0]
    if not isinstance(args.runfile,str):
        args.runfile = args.runfile[0]
    if not isinstance(args.ip,str):
        args.ip = args.ip[0]
    if not isinstance(args.port,int):
        args.port = args.port[0]
    if not isinstance(args.timedelay,float):
        args.timedelay = args.timedelay[0]
    if not isinstance(args.choosenextport,bool):
        args.choosenextport = args.choosenextport[0]
    if not isinstance(args.PR,str):
        args.PR = args.PR[0]
    if not isinstance(args.U,str):
        args.U = args.U[0]
    if not isinstance(args.GT,str):
        args.GT = args.GT[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    # logging
    log = logging.getLogger('dcs')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    #fh = logging.handlers.WatchedFileHandler(args.logfile)
    fh = QueuedWatchedFileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    #fh.setFormatter(logging.Formatter('%(created)f %(name)s %(levelname)s %(message)s'))
    fh.setFormatter(logging.Formatter('%(created)f %(levelname)s %(message)s'))
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO) # logging.WARNING = 30
    #ch.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s',datefmt='%H:%M:%S'))
    ch.setFormatter(logging.Formatter('%(asctime)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    log.info("start logging in pressure900_server: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.info("logging to \"%s\"" % args.logfile)
    signal.signal(signal.SIGTERM,shutdown)
    # check runfile
    if args.runfile != "":
        ori = [os.getpid(),args.device]
        runinfo = [ori]
        #runinfo = os.getpid(),args.device
        if os.path.isfile(args.runfile):
            # file exists, read it
            f = open(args.runfile,'r')
            reader = csv.reader(f)
            r = False # assuming other pid is not running; will be corrected if more information is available
            for row in reader:
                # row[0] should be a pid
                # row[1] should be the device
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
                if rr and row[1] != args.device: # checking iff same device
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
            nri = [os.getpid(),args.device]
            index = runinfo.index(ori)
            runinfo[index] = nri
            f = open(args.runfile,'w')
            writer = csv.writer(f)
            for i in range(len(runinfo)):
                writer.writerows([runinfo[i]])
                f.close()
        log.removeHandler(ch)
    else:
        log.info("due to debug=1 will _not_ go to background (fork)")
    controller = controller_class(log=log,device=args.device,updatedelay=args.timedelay,PR=args.PR,UNIT=args.U,GT=args.GT)
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
    sys.exit(0)

if __name__ == "__main__":
    main()

