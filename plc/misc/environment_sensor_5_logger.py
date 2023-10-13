#!/usr/bin/python
# Author: Daniel Mohr
# Date: 2013-03-13, 2013-12-12, 2013-12-13, 2013-12-16. 2014-01-27, 2014-03-19, 2014-03-29, 2014-07-23, 2015-02-09
# License: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.
# Copyright (C) 2013, 2014, 2015 Daniel Mohr and PlasmaLab (FKZ 50WP0700)

__environment_sensor_5_logger_date__ = "2015-02-09"
__environment_sensor_5_logger_version__ = __environment_sensor_5_logger_date__

import argparse
import csv
import logging
import os
import re
import serial
import signal
import sys
import tempfile
import threading
import time

import http.server
import socketserver
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
import datetime

from plc_tools.plclogclasses import QueuedWatchedFileHandler

# udev-rule for Environment Sensor 5:
# ACTION=="add", KERNEL=="ttyUSB*", ATTRS{product}=="TTL232R-3V3", ATTRS{manufacturer}=="FTDI", ATTRS{serial}=="FTGAB745", SYMLINK+="ES%s{serial}", GROUP="dialout"

class environment_sensor_5():
    def __init__(self,log=None,datalog=None,devicename="/dev/ESFTGAB745",extrasleep=-1.0,sleep=3.0,baudrate=9600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=2.0,writeTimeout=2.0,webserver=False,webserverpath=None,webserver_history_length=1000,webserver_plot_interval=-1):
        self.log = log
        self.datalog = datalog
        self.devicename = devicename
        self.extrasleep = extrasleep
        self.sleep = sleep
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.writeTimeout = writeTimeout
        self.webserver = webserver
        self.webserverpath = webserverpath
        self.webserver_history_length = webserver_history_length
        self.webserver_plot_interval = webserver_plot_interval
        #
        self.running = True
        self.device_init = False
        self.device = None
        self.actualvaluelock = threading.Lock()
        self.actualvaluelock.acquire() # lock for running
        self.actualvalue = {'time': None,
                            'temperature': None,
                            'humidity': None,
                            'dewpoint': None}
        self.actualvaluelock.release() # release the lock
        self.nodevice = True
        #
        self.webserver_header = ""
        self.webserver_footer = ""
        #self.webserver_history_length = 1000 # 1000
        # history goes back n*numpy.log(n)/numpy.log(2) steps
        # biggest distance in history is n seconds
        # for 10 and every second: 25 seconds back and 10 seconds biggest distance
        # for 50 and every second: 272 seconds back and 50 seconds biggest distance
        # for 100 and every second: 600 seconds back and 100 seconds biggest distance
        # for 1000 and every second: 9965 seconds back and 1000 seconds biggest distance
        self.webserver_history_del_position = self.webserver_history_length
        self.webserver_data = []
        if self.webserver_plot_interval > 0:
            self.webserver_create_plot = True
        else:
            self.webserver_create_plot = False
        self.webserver_plot_data0 = []
        self.webserver_plot_data1 = []
        self.webserver_plot_data2 = []
        self.webserver_plot_data3 = []
        self.webserver_plot_it = 0
        if self.webserver:
            self.webserver_header += "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n"
            self.webserver_header += "<html>\n"
            self.webserver_header += "<head>\n"
            self.webserver_header += "<title>environment sensor</title>\n"
            if self.webserver_plot_interval > 0:
                self.webserver_header += "<meta http-equiv=\"refresh\" content=\"%d; URL=environment_sensor_5.html\">\n" % (self.webserver_plot_interval*max(1,self.extrasleep))
            else:
                self.webserver_header += "<meta http-equiv=\"refresh\" content=\"%d; URL=environment_sensor_5.html\">\n" % max(1,self.extrasleep)
            self.webserver_header += "</head>\n"
            self.webserver_header += "<body>\n"
            if self.webserver_create_plot:
                self.webserver_header += "<p><img src=\"environment_sensor_5.svg\"></p>\n"
            self.webserver_footer += "</body>\n"
            self.webserver_footer += "</html>\n"

    def start_logging(self):
        self.logging_thread_id = threading.Thread(target=self.logging_thread)
        self.logging_thread_id.daemon = True # exit thread when the main thread terminates
        self.logging_thread_id.start()

    def stop_logging(self,signum=None,frame=None):
        self.running = False
        self.log.debug("stopping, sleep a while")
        time.sleep(max(self.sleep,self.timeout,self.writeTimeout)+0.1)

    def stop_logging_if_nodevice(self,signum=None,frame=None):
        if self.nodevice:
            self.log.debug("no device, stopping")
            self.stop_logging()

    def logging_thread(self):
        while self.running:
            if not self.device_init:
                self.device_init = True
                self.device = serial.Serial(port=None,
                               baudrate=self.baudrate,
                               bytesize=self.bytesize,
                               parity=self.parity,
                               stopbits=self.stopbits,
                               timeout=self.timeout,
                               writeTimeout=self.writeTimeout)
                self.device.port = self.devicename
            if not self.device.isOpen():
                try:
                    self.device.open()
                except:
                    self.device_init = False
            if self.device_init:
                try:
                    line = self.device.readline()
                    t = time.time()
                    self.nodevice = False
                except:
                    line = None
                    self.device_init = False
                    self.log.debug("cannot read from device, sleep a while")
                    self.nodevice = True
                    time.sleep(self.sleep)
                if line:
                    (line,numberofchanges) = re.subn(chr(0),"",line)
                    if numberofchanges > 0:
                        self.log.debug("WARNING: replaced %d times chr(0) by nothing" % numberofchanges)
                    r = re.findall("temperature=([0-9\.\-]+)"+chr(186)+"C humidity=([0-9\.]+)% dewpoint=([0-9\.\-]+)"+chr(186)+"C",line)
                    if r:
                        self.actualvaluelock.acquire() # lock for running
                        self.actualvalue['time'] = t
                        self.actualvalue['temperature'] = r[0][0]
                        self.actualvalue['humidity'] = r[0][1]
                        self.actualvalue['dewpoint'] = r[0][2]
                        self.datalog.info("%f %s %s %s" % (self.actualvalue['time'],self.actualvalue['temperature'],self.actualvalue['humidity'],self.actualvalue['dewpoint']))
                        self.actualvaluelock.release() # release the lock
                        if self.webserver:
                            self.writedataforwebserver()
                        if self.extrasleep > 0:
                            self.log.debug("extrasleep")
                            time.sleep(self.extrasleep)
                    else:
                        self.log.debug("ERROR: \""+line+"\"")
                        output = "ERROR: \""
                        for i in range(len(line)):
                            output += "%d," % ord(line[i])
                        output += "\""
                        self.log.debug(output)
            else:
                self.log.debug("no device, sleep a while")
                self.nodevice = True
                time.sleep(self.sleep)
        try:
            if self.device.isOpen():
                self.device.close()
        except: pass
    def writedataforwebserver(self):
        self.actualvaluelock.acquire() # lock for running
        output = ""
        output += "<table border=\"1\">\n"
        output += "<tr><th>time</th><th>temperature</th><th>humidity</th><th>dewpoint</th></tr>\n"
        data = ""
        data += "<tr align=\"center\">"
        data += "<td>%s</td>" % time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.actualvalue['time']))
        data += "<td>%s &deg;</td>" % self.actualvalue['temperature']
        data += "<td>%s %%</td>" % self.actualvalue['humidity']
        data += "<td>%s &deg;</td>" % self.actualvalue['dewpoint']
        data += "</tr>\n"
        self.webserver_data.insert(0,data)
        if self.webserver_create_plot:
            self.webserver_plot_data0.append(datetime.datetime.fromtimestamp(self.actualvalue['time']))
            self.webserver_plot_data1.append(float(self.actualvalue['temperature']))
            self.webserver_plot_data2.append(float(self.actualvalue['humidity']))
            self.webserver_plot_data3.append(float(self.actualvalue['dewpoint']))
        self.actualvaluelock.release() # release the lock
        if len(self.webserver_data) > self.webserver_history_length:
            del self.webserver_data[self.webserver_history_del_position]
            if self.webserver_create_plot:
                del self.webserver_plot_data0[self.webserver_history_length-self.webserver_history_del_position]
                del self.webserver_plot_data1[self.webserver_history_length-self.webserver_history_del_position]
                del self.webserver_plot_data2[self.webserver_history_length-self.webserver_history_del_position]
                del self.webserver_plot_data3[self.webserver_history_length-self.webserver_history_del_position]
            self.webserver_history_del_position -= 1
            if self.webserver_history_del_position < 1:
                self.webserver_history_del_position = self.webserver_history_length
        output += "".join(self.webserver_data)
        output += "</table>\n"
        if self.webserver_create_plot:
            if self.webserver_plot_it%self.webserver_plot_interval == 0:
                self.webserver_plot_it = 1
                matplotlib.pyplot.subplot(3,1,1)
                matplotlib.pyplot.plot(self.webserver_plot_data0,self.webserver_plot_data1,'r.-')
                #matplotlib.pyplot.title('')
                matplotlib.pyplot.ylabel('temperature')
                matplotlib.pyplot.subplot(3,1,2)
                matplotlib.pyplot.plot(self.webserver_plot_data0,self.webserver_plot_data2,'g.-')
                matplotlib.pyplot.ylabel('humidity')
                matplotlib.pyplot.subplot(3,1,3)
                matplotlib.pyplot.plot(self.webserver_plot_data0,self.webserver_plot_data3,'b.-')
                matplotlib.pyplot.xlabel('time')
                matplotlib.pyplot.ylabel('dewpoint')
                matplotlib.pyplot.gcf().autofmt_xdate()
                matplotlib.pyplot.savefig('environment_sensor_5.svg')
                matplotlib.pyplot.close()
            else:
                self.webserver_plot_it += 1
        f = open(os.path.join(self.webserverpath,"environment_sensor_5.html"),'w')
        f.write(self.webserver_header)
        f.write(output)
        f.write(self.webserver_footer)
        f.close()

def main():
    # command line parameter
    help = ""
    help += "This is a simple command line program to get the data from the environment sensor 5 http://www.messpc.de/sensor_alphanumerisch.php . You can plot the logfile with gnuplot.\n\n"
    help += "\nYou need access to the device of the sensor.\n"
    help += "For example you can use the following udev rule:\n"
    help += "  ACTION==\"add\", KERNEL==\"ttyUSB*\", ATTRS{product}==\"TTL232R-3V3\", ATTRS{manufacturer}==\"FTDI\", ATTRS{serial}==\"FTGAB745\", SYMLINK+=\"ES%s{serial}\", GROUP=\"users\"\n"
    help += "A temperature between 21 C and 23 C is a good range. Good humidity levels are\n"
    help += "between 45 % and 50 %. These are good intervals for humans and maschines.\n"
    help += "Electrostatic discharge can occur if the relative humidity is below 35 %.\n"
    help += "It becomes critical when relative humidity is below 30 %. High humidity over\n"
    help += "55 % can cause hardware corrosion. In the middle of these intervals is the\n"
    help += "biggest buffer in all direction available. A typical design point is 22 C\n"
    help += "and 45 % (e. g. IBM uses this point as environmental criteria).\n"
    help += "\nExamples:\n"
    help += " environment_sensor_5_logger.py -logfile /tmp/environment_sensor/environment_sensor_5.log -datalogfile /tmp/environment_sensor/environment_sensor_5.data -devicename /dev/ESFTGA2TC2 -runfile /tmp/environment_sensor/environment_sensor_5.pids -webserver -webserver_path /tmp/environment_sensor -webserver_history_length 100 -extrasleep 1 -webserver_plot_interval 60\n"
    parser = argparse.ArgumentParser(
        description='environment_sensor_5_logger.py logs measurements from the  environment sensor 5 to a logfile. You need access to the device.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.\n\n%s" % (__environment_sensor_5_logger_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-logfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"environment_sensor_5.log"),
                        type=str,
                        required=False,
                        dest='logfile',
                        help='Set the logfile to f. Setting f to an empty string disables logging to file. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"environment_sensor_5.log"),
                        metavar='f')
    parser.add_argument('-datalogfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"environment_sensor_5.data"),
                        type=str,
                        required=False,
                        dest='datalogfile',
                        help='Set the datalogfile to f. Only the measurements will be logged here. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"environment_sensor_5.data"),
                        metavar='f')
    parser.add_argument('-devicename',
                        nargs=1,
                        default="/dev/ESFTGAB745",
                        type=str,
                        required=False,
                        dest='devicename',
                        help='Set the devicename to dev. default: /dev/ESFTGAB745',
                        metavar='dev')
    parser.add_argument('-extrasleep',
                        nargs=1,
                        default=-1.0,
                        type=float,
                        required=False,
                        dest='extrasleep',
                        help='Sleep s seconds after every measurement. default: -1.0 (no sleep)',
                        metavar='s')
    parser.add_argument('-sleep',
                        nargs=1,
                        default=3.0,
                        type=float,
                        required=False,
                        dest='sleep',
                        help='If communication to device is not possible, sleep s seconds before retrying. default: 3.0',
                        metavar='s')
    parser.add_argument('-baudrate',
                        nargs=1,
                        default=9600,
                        type=int,
                        required=False,
                        dest='baudrate',
                        help='Set the baudrate to n. default: 9600',
                        metavar='n')
    parser.add_argument('-runfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"environment_sensor_5.pids"),
                        type=str,
                        required=False,
                        dest='runfile',
                        help='Set the runfile to f. If an other process is running with a given pid and reading the same device, the program will not start. Setting f=\"\" will disable this function. default: %s' % os.path.join(tempfile.gettempdir(),"environment_sensor_5.pids"),
                        metavar='f')
    parser.add_argument('-debug',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info; 1 debug to STDOUT (default).',
                        metavar='debug_level')
    parser.add_argument('-webserver',
                        action='store_true',
                        default=False,
                        dest='webserver',
                        help='Start a webserver. With the default values this server can be connected by: http://localhost:8080/')
    parser.add_argument('-webserverhost',
                        nargs=1,
                        default="localhost",
                        type=str,
                        required=False,
                        dest='webserverhost',
                        help='Set the host of the webserver. default: localhost',
                        metavar='host')
    parser.add_argument('-webserverport',
                        nargs=1,
                        default=8080,
                        type=int,
                        required=False,
                        dest='webserverport',
                        help='Set the port of the webserver. default: 8080',
                        metavar='port')
    parser.add_argument('-webserver_history_length',
                        nargs=1,
                        default=1000,
                        type=int,
                        required=False,
                        dest='webserver_history_length',
                        help='Set the length of the history of the presented data of the webserver. default: 1000',
                        metavar='n')
    parser.add_argument('-webserver_path',
                        nargs=1,
                        default=None,
                        type=str,
                        required=False,
                        dest='webserver_path',
                        help='Set the path for the webserver. default: None (A temporary directory will be created, used and in the end deleted.)',
                        metavar='f')
    parser.add_argument('-webserver_plot_interval',
                        nargs=1,
                        default=-1,
                        type=int,
                        required=False,
                        dest='webserver_plot_interval',
                        help='Creates plot for the webserver every n measurements. default: -1 (do not create plots)',
                        metavar='n')
    args = parser.parse_args()
    if not isinstance(args.logfile,str):
        args.logfile = args.logfile[0]
    if not isinstance(args.datalogfile,str):
        args.datalogfile = args.datalogfile[0]
    if not isinstance(args.devicename,str):
        args.devicename = args.devicename[0]
    if not isinstance(args.extrasleep,float):
        args.extrasleep = args.extrasleep[0]
    if not isinstance(args.sleep,float):
        args.sleep = args.sleep[0]
    if not isinstance(args.baudrate,int):
        args.baudrate = args.baudrate[0]
    if not isinstance(args.runfile,str):
        args.runfile = args.runfile[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.webserverhost,str):
        args.webserverhost = args.webserverhost[0]
    if not isinstance(args.webserverport,int):
        args.webserverport = args.webserverport[0]
    if not isinstance(args.webserver_history_length,int):
        args.webserver_history_length = args.webserver_history_length[0]
    if (not args.webserver_path == None) and (not isinstance(args.webserver_path,str)):
        args.webserver_path = args.webserver_path[0]
    if not isinstance(args.webserver_plot_interval,int):
        args.webserver_plot_interval = args.webserver_plot_interval[0]
    # logging
    log = logging.getLogger('log')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    if args.logfile != "":
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
    # datalog
    datalog = logging.getLogger('datalog')
    datalog.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    fhd = QueuedWatchedFileHandler(args.datalogfile)
    fhd.setLevel(logging.DEBUG)
    fhd.setFormatter(logging.Formatter('%(message)s'))
    datalog.addHandler(fhd)
    if args.debug == 1:
        # create console handler
        chd = logging.StreamHandler()
        chd.setLevel(logging.DEBUG) # logging.DEBUG = 10
        chd.setFormatter(logging.Formatter('%(asctime)s %(message)s',datefmt='%H:%M:%S'))
        # add the handlers to log
        datalog.addHandler(chd)
    log.info("logging to \"%s\" and data to \"%s\"" % (args.logfile,args.datalogfile))
    # check runfile
    if args.runfile != "":
        ori = [os.getpid(),args.devicename]
        runinfo = [ori]
        if os.path.isfile(args.runfile):
            # file exists, read it
            f = open(args.runfile,'r')
            reader = csv.reader(f)
            r = False # assuming other pid is not running; will be corrected if more information is available
            for row in reader:
                # row[0] should be a pid
                # row[1] should be the devicename
                rr = False
                if os.path.exists(os.path.join("/proc","%d" % os.getpid())): # checking /proc available
                    if os.path.exists(os.path.join("/proc","%d" % int(row[0]))): # check if other pid is running
                        ff = open(os.path.join("/proc","%d" % int(row[0]),"cmdline"),'rt')
                        cmdline = ff.read(1024*1024)
                        ff.close()
                        if re.findall(__file__,cmdline):
                            rr = True
                            log.info("process %d is running (proc)" % int(row[0]))
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
                        log.info("process %d is running (kill)" % int(row[0]))
                if rr and row[1] != args.devicename: # checking iff same devicename
                    runinfo += [[row[0],row[1]]]
                elif rr:
                    r = True
            f.close()
            if r:
                log.error("other process is running; exit.")
                time.sleep(0.1)
                sys.exit(1)
        f = open(args.runfile,'w')
        writer = csv.writer(f)
        for i in range(len(runinfo)):
            writer.writerows([runinfo[i]])
        f.close()
    # go to background if useful
    if args.debug == 0:
        # go in background
        log.info("go to background (fork)")
        newpid = os.fork()
        if newpid > 0:
            log.info("background process pid = %d" % newpid)
            time.sleep(0.1)
            sys.exit(0)
        elif args.runfile != "":
            nri = [os.getpid(),args.devicename]
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
    if args.webserver:
        log.info("start webserver")
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer((args.webserverhost, args.webserverport), Handler)
    webserver_path = None
    if args.webserver:
        if not args.webserver_path == None:
            webserver_path = args.webserver_path
            log.info("use directory: %s" % webserver_path)
        else:
            webserver_path = tempfile.mkdtemp(prefix='environment_sensor_')
            log.info("use temporary directory: %s" % webserver_path)
        os.chdir(webserver_path) # change current working directory
    sensor = environment_sensor_5(log=log,datalog=datalog,devicename=args.devicename,extrasleep=args.extrasleep,sleep=args.sleep,baudrate=args.baudrate,webserver=args.webserver,webserverpath=webserver_path,webserver_history_length=args.webserver_history_length,webserver_plot_interval=args.webserver_plot_interval)
    signal.signal(signal.SIGTERM,sensor.stop_logging)
    signal.signal(signal.SIGCONT,sensor.stop_logging_if_nodevice)
    sensor.start_logging()
    if args.webserver:
        webserver_thread = threading.Thread(target=httpd.serve_forever)
        webserver_thread.daemon = True # exit thread when the main thread terminates
        webserver_thread.start()
    while sensor.running:
        time.sleep(1) # it takes at least 1 second to exit
    if args.webserver and (args.webserver_path == None):
        for d in os.listdir(webserver_path):
            os.unlink('%s/%s' % (webserver_path,d))
        os.rmdir(webserver_path)
        log.info("temporary directory '%s' deleted" % webserver_path)
    log.debug("exit")
    time.sleep(0.1)

if __name__ == "__main__":
    main()
