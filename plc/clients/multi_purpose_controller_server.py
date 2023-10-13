#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-05-14, 2014-07-22

__multi_purpose_controller_server_date__ = "2014-07-22"
__multi_purpose_controller_server_version__ = __multi_purpose_controller_server_date__

import argparse
import csv
import errno
import logging
import os
import random
import re
import signal
import socket
import socketserver
import sys
import tempfile
import threading
import time

import plc_tools.server_base
from plc_tools.conversion import volt2dac,adcstring2volt
from plc_tools.plclogclasses import QueuedWatchedFileHandler
import plc_tools.plc_socket_communication

class controller_class(plc_tools.server_base.controller_class):
    """controller_class

    This class is for communicating to a device. This means
    setvalues are required by the user and will be set in some
    intervals. The actualvalues are the actualvalues which were
    set before.

    Author: Daniel Mohr
    Date: 2012-09-30
    """
    def myinit(self,DO=None,R=None,U05=None,U15=None,U24=None,DAC=None,simulate=False):
        self.simulate = simulate
        self.actualvaluelock.acquire() # lock for running
        self.actualvalue = {'DO': 4*[None],
                            'R': 2*[None],
                            'U05': None,
                            'U15': None,
                            'U24': None,
                            'DAC': 4*[0.0],
                            'DI' : 4*[None],
                            'ADC' : 8*[0]}
        self.actualvaluelock.release() # release the lock
        self.setpointlock.acquire() # lock for running
        self.setpoint = {'DO': 4*[False],
                         'R': 2*[False],
                         'U05': False,
                         'U15': False,
                         'U24': False,
                         'DAC': 4*[0.00015259021896696368]}
        if DO != None:
            self.setpoint['DO'] = self.str2boolarray(DO)
        if R != None:
            self.setpoint['R'] = self.str2boolarray(R)
        if U05 != None:
            self.setpoint['U05'] = self.str2bool(U05)
        if U15 != None:
            self.setpoint['U15'] = self.str2bool(U15)
        if U24 != None:
            self.setpoint['U24'] = self.str2bool(U24)
        if DAC != None:
            self.setpoint['DAC'] = self.str2float(DAC)
            for i in range(4):
                self.setpoint['DAC'][i] = min(max(-10.0,self.setpoint['DAC'][i]),+10.0)
        self.setpointlock.release() # release the lock

    def wrd(self, data):
        data = data.encode() if data is not None else None
        return self.device.write(data)

    def set_actualvalue_to_the_device(self):
        # will set the actualvalue to the device
        self.set_actualvalue_to_the_device_lock.acquire() # lock to write data
        # write actualvalue to the device
        self.actualvaluelock.acquire() # lock to get new settings
        actualvalue = self.actualvalue.copy()
        self.actualvaluelock.release() # release the lock
        self.setpointlock.acquire() # lock to get new settings
        actualvalue['DO'][:] = self.setpoint['DO'][:]
        actualvalue['R'][:] = self.setpoint['R'][:]
        actualvalue['U05'] = self.setpoint['U05']
        actualvalue['U15'] = self.setpoint['U15']
        actualvalue['U24'] = self.setpoint['U24']
        actualvalue['DAC'][0:4] = self.setpoint['DAC'][0:4]
        self.setpointlock.release() # release the lock
        sendreceive = ""
        s = "@"
        if self.device == None or self.devicename == "":
            if self.simulate:
                self.log.warning("no device given; can't write to device; will simulate some delay and some data!")
                time.sleep(random.randint(640,1000)/10000.0)
            else:
                self.log.warning("no device given; can't write to device!")
            sendreceive += s
            sendreceive += "Q"
        else:
            if not self.deviceopen:
                self.device.port = self.devicename
                self.device.open()
                self.deviceopen = True
            self.wrd(s)
            self.device.flush()
            sendreceive += s
            r = self.device.read(1)
            sendreceive += r
            if r != 'Q':
                self.log.warning("communication problem with device %s" % self.devicename)
        s = ""
        st = list('0000')
        if actualvalue['DO'][3]:
            st[2] = '1'
        if actualvalue['DO'][2]:
            st[3] = '1'
        #s += "%X" % int(string.join(st,''),2)
        s += "%X" % int(''.join(st),2)
        st = list('0000')
        if actualvalue['DO'][1]:
            st[0] = '1'
        if actualvalue['DO'][0]:
            st[1] = '1'
        if actualvalue['R'][1]:
            st[2] = '1'
        if actualvalue['R'][0]:
            st[3] = '1'
        #s += "%X" % int(string.join(st,''),2)
        s += "%X" % int(''.join(st),2)
        st = list('0000')
        if actualvalue['U15']:
            st[1] = '1'
        if actualvalue['U05']:
            st[2] = '1'
        if actualvalue['U24']:
            st[3] = '1'
        #s += "%X" % int(string.join(st,''),2)
        s += "%X" % int(''.join(st),2)
        if self.device == None or self.devicename == "":
            sendreceive += s
            sendreceive += "D"
        else:
            if not self.deviceopen:
                self.device.port = self.devicename
                self.device.open()
                self.deviceopen = True
            self.wrd(s)
            self.device.flush()
            sendreceive += s
            r = self.device.read(1)
            sendreceive += r
            if r != 'D':
                self.log.warning("communication problem with device %s" % self.devicename)
        s = ""
        for i in range(4):
            v = volt2dac(actualvalue['DAC'][i])
            s += "%04X" % v
        if self.device == None or self.devicename == "":
            sendreceive += s
            sendreceive += "A"
        else:
            if not self.deviceopen:
                self.device.port = self.devicename
                self.device.open()
                self.deviceopen = True
            self.wrd(s)
            self.device.flush()
            sendreceive += s
            r = self.device.read(1)
            sendreceive += r
            if r != 'A':
                self.log.warning("communication problem with device %s" % self.devicename)
        if self.device == None or self.devicename == "":
            if self.simulate:
                # @Q000D8000800080008000A0A03091E20B920BB0000FFFE20CC20D4IFC
                r = ""
                for i in range(32):
                    r += "%X" % random.randint(0,15)
                for i in range(8):
                    actualvalue['ADC'][i] = adcstring2volt(r[i*4+0:i*4+4])
                sendreceive += "I"
                r = ""
                for i in range(2):
                    r += "%X" % random.randint(0,15)
                sendreceive += r
                s = "{0:04b}".format(int(r[1],16))
                for i in range(4):
                    if s[i] == "1":
                        actualvalue['DI'][3-i] = True
                    else:
                        actualvalue['DI'][3-i] = False
            else:
                sendreceive += "********************************"
                sendreceive += "I"
                sendreceive += "**"
        else:
            r = self.device.read(32) # ADC
            sendreceive += r
            for i in range(8):
                actualvalue['ADC'][i] = adcstring2volt(r[i*4+0:i*4+4])
            r = self.device.read(1)
            sendreceive += r
            if r != 'I':
                self.log.warning("communication problem with device %s" % self.devicename)
            r = self.device.read(2) # DI
            sendreceive += r
            s = "{0:04b}".format(int(r[1],16))
            for i in range(4):
                if s[i] == "1":
                    actualvalue['DI'][3-i] = True
                else:
                    actualvalue['DI'][3-i] = False
        t = time.time()
        self.actualvaluelock.acquire() # lock to get new settings
        self.actualvalue = actualvalue
        self.actualvaluelock.release() # release the lock
        if self.device == None or self.devicename == "":
            self.log.debug("SENDRECEIVE: %s" % (sendreceive))
        else:
            self.datalog.debug("%f SENDRECEIVE: %s" % (t,sendreceive))
        self.set_actualvalue_to_the_device_lock.release() # release the lock

    def set_setpoint(self,s=None):
        if s != None:
            for i in range(4):
                s['DAC'][i] = min(max(-10.0,s['DAC'][i]),+10.0)
            self.setpointlock.acquire() # lock to set
            self.setpoint = s.copy()
            self.setpointlock.release() # release the lock

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler,plc_tools.plc_socket_communication.tools_for_socket_communication):

    def handle(self):
        global controller
        self.send_data_to_socket_lock = threading.Lock()
        bufsize = 4096 # read/receive Bytes at once
        controller.log.debug("start connection to %s:%s" % (self.client_address[0],self.client_address[1]))
        data = ""
        while controller.running:
            self.request.settimeout(1)
            # get some data
            d = ""
            try:
                d = self.request.recv(bufsize)
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
                if (len(data) >= 2) and (data[0].lower() == "p"):
                    # packed data; all settings at once
                    found_something = True
                    [data,v] = self.receive_data_from_socket2(self.request,bufsize=bufsize,data=data[2:])
                    controller.set_setpoint(s=v)
                elif (len(data) >= 4) and (data[0:4].lower() == "!w2d"):
                    # trigger writing setvalues to the external device
                    found_something = True
                    controller.set_actualvalue_to_the_device()
                    data = data[4:]
                elif (len(data) >= 6) and (data[0:6].lower() == "getact"):
                    # sends the actual values back
                    found_something = True
                    data = data[6:]
                    response += self.create_send_format(controller.get_actualvalue())
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
                    a = "multi_purpose_controller_server Version: %s" % __multi_purpose_controller_server_version__
                    response += a
                    controller.log.debug(a)
                    data = data[7:]
                if len(data) == 0:
                    break
            time.sleep(random.randint(1,100)/1000.0)
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
    help += "lisening with the following commands: (This is a prefix-code. Upper or lower letters do not matter.)\n"
    help += "  p[pickle data] : Set all setpoints at once. You have all setpoints in one\n"
    help += "                   object:\n"
    help += "                   a = {'DO':4*[False],'R':2*[False],'U05':False,'U15':False,'U24':False,'DAC':4*[0.0]}\n"
    help += "                   Now you can generate the [pickle data]==v by:\n"
    help += "                   s = pickle.dumps(a,-1); v='%d %s' % (len(s),s)\n"
    help += "  !w2d : trigger writing setvalues to the external device\n"
    help += "  getact : sends the actual values back as [pickle data]\n"
    help += "  timedelay000 : set the time between 2 actions to 000 milliseconds.\n"
    help += "  quit : quit the server\n"
    help += "  version : response the version of the server\n"
    parser = argparse.ArgumentParser(
        description='multi_purpose_controller_server is a socket server to control the multi purpose controller on an serial interface. On start every settings are assumed to 0 or the given values and set to the device. A friendly kill (SIGTERM) should be possible.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__multi_purpose_controller_server_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
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
                        default=os.path.join(tempfile.gettempdir(),"multi_purpose_controller.log"),
                        type=str,
                        required=False,
                        dest='logfile',
                        help='Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"multi_purpose_controller.log"),
                        metavar='f')
    parser.add_argument('-datalogfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"multi_purpose_controller.data"),
                        type=str,
                        required=False,
                        dest='datalogfile',
                        help='Set the datalogfile to f. Only the measurements will be logged here. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"multi_purpose_controller.data"),
                        metavar='f')
    parser.add_argument('-runfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"multi_purpose_controller.pids"),
                        type=str,
                        required=False,
                        dest='runfile',
                        help='Set the runfile to f. If an other process is running with a given pid and writing to the same device, the program will not start. Setting f=\"\" will disable this function. default: %s' % os.path.join(tempfile.gettempdir(),"multi_purpose_controller.pids"),
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
                        default=15113,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15113',
                        metavar='p')
    parser.add_argument('-timedelay',
                        nargs=1,
                        default=0.062, # 62 characters with 9600 boud
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
    parser.add_argument('-DO',
                        nargs=1,
                        default="0000",
                        type=str,
                        required=False,
                        dest='DO',
                        help='Set the default values for the multi purpose controller port DO; \"0\" for channel off and \"1\" for channel on; \"0001\" means only channel 1 to ON. default: d = \"0000\"',
                        metavar='d')
    parser.add_argument('-R',
                        nargs=1,
                        default="00",
                        type=str,
                        required=False,
                        dest='R',
                        help='Set the default values for the multi purpose controller port R; \"0\" for channel off and \"1\" for channel on; \"01\" means only channel 1 to ON. default: d = \"00\"',
                        metavar='d')
    parser.add_argument('-U05',
                        nargs=1,
                        default="0",
                        type=str,
                        required=False,
                        dest='U05',
                        help='Set the default values for the multi purpose controller port U05; \"0\" for channel off and \"1\" for channel on. default: d = \"0\"',
                        metavar='d')
    parser.add_argument('-U15',
                        nargs=1,
                        default="0",
                        type=str,
                        required=False,
                        dest='U15',
                        help='Set the default values for the multi purpose controller port U15; \"0\" for channel off and \"1\" for channel on. default: d = \"0\"',
                        metavar='d')
    parser.add_argument('-U24',
                        nargs=1,
                        default="0",
                        type=str,
                        required=False,
                        dest='U24',
                        help='Set the default values for the multi purpose controller port U24; \"0\" for channel off and \"1\" for channel on. default: d = \"0\"',
                        metavar='d')
    #default="-10,-10,-10,-10",
    parser.add_argument('-DAC',
                        nargs=1,
                        default="0.00016,0.00016,0.00016,0.00016",
                        type=str,
                        required=False,
                        dest='DAC',
                        help='Set the default values for the multi purpose controller port DAC. default: d = \"0.00016,0.00016,0.00016,0.00016\"',
                        metavar='d')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    parser.add_argument('-simulate',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='simulate',
                        help='By specifying this flag simulated values (ADC-values) will be send to a client and a random sleep simulates the communication to the device.')
    args = parser.parse_args()
    if not isinstance(args.device,str):
        args.device = args.device[0]
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
    if not isinstance(args.timedelay,float):
        args.timedelay = args.timedelay[0]
    if not isinstance(args.choosenextport,bool):
        args.choosenextport = args.choosenextport[0]
    if not isinstance(args.DO,str):
        args.DO = args.DO[0]
    if not isinstance(args.R,str):
        args.R = args.R[0]
    if not isinstance(args.U05,str):
        args.U05 = args.U05[0]
    if not isinstance(args.U15,str):
        args.U15 = args.U15[0]
    if not isinstance(args.U24,str):
        args.U24 = args.U24[0]
    if not isinstance(args.DAC,str):
        args.DAC = args.DAC[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.simulate,bool):
        args.simulate = args.simulate[0]
    # logging
    log = logging.getLogger('mpcs')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
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
    datalog = logging.getLogger('mpcsd')
    datalog.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    fhd = QueuedWatchedFileHandler(args.datalogfile)
    fhd.setLevel(logging.DEBUG)
    fhd.setFormatter(logging.Formatter('%(message)s'))
    # add the handlers to log
    datalog.addHandler(fhd)
    log.info("start logging in multi_purpose_controller_server: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.info("logging to \"%s\" and data to \"%s\"" % (args.logfile,args.datalogfile))
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
                log.error("other process is running; exit.")
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
            if args.runfile != "":
                nri = [newpid,args.device]
                index = runinfo.index(ori)
                runinfo[index] = nri
                f = open(args.runfile,'w')
                writer = csv.writer(f)
                for i in range(len(runinfo)):
                    writer.writerows([runinfo[i]])
                    f.close()
            time.sleep(0.062) # time for first communication with device
            sys.exit(0)
        log.removeHandler(ch)
        # threads in the default process are dead
        # in particular this means QueuedWatchedFileHandler is not working anymore
        fh.startloopthreadagain()
        fhd.startloopthreadagain()
        log.info("removed console log handler")
    else:
        log.info("due to debug=1 will _not_ go to background (fork)")
    controller = controller_class(log,datalog,args.device,args.timedelay,args.DO,args.R,args.U05,args.U15,args.U24,args.DAC,args.simulate)
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
    time.sleep(0.001)
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
