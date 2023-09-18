"""client server communication classes for plc

Author: Daniel Mohr
Date: 2013-05-22
"""

import socket
import subprocess
import threading
import time
import tkinter

import plc_tools.plc_socket_communication

class socket_communication_class(plc_tools.plc_socket_communication.tools_for_socket_communication):
    """base class for continued socket communication

    Author: Daniel Mohr
    Date: 2013-05-22
    """
    def __init__(self,config=None,confsect=None,pw=None,bufsize=4096):
        self.myservername = "server"
        self.dev = "-1"
        self.serialnumber = "-1"
        self.st = "-1"
        self.actualvalue = None
        self.setpoint = None
        self.bufsize = bufsize # read/receive Bytes at once
        self.lock = threading.Lock()
        self.updatelock = threading.Lock()
        self.socketlock = threading.Lock()
        self.get_actualvalues_lock = threading.Lock()
        self.send_data_to_socket_lock = threading.Lock()
        self.updatethread_lock = threading.Lock()
        self.lock.acquire() # lock
        self.config = config
        self.confsect = confsect
        self.pw = pw
        self.socket = None
        self.lastupdate = time.time()
        self.isconnect = False
        self.trigger_out = False
        # values for the gui
        self.isgui = False
        self.start_button = None
        self.stop_button = None
        self.updatethreadsleeptime = 0.001
        self.myinit()
        self.lock.release() # release the lock

    def myinit(self):
        """for outside use"""
        pass

    def updatethread(self):
        """if necessary write values self.setpoint to device
        and read them from device to self.actualvalue

        Author: Daniel Mohr
        Date: 2013-01-10
        """
        self.updatethread_lock.acquire() # lock
        while self.updatethreadrunning:
            self.isconnect = True
            self.socket_communication_with_server()
            nextupdate = self.lastupdate + self.update_intervall
            self.lastupdate = time.time()
            time.sleep(self.updatethreadsleeptime)
            while self.updatethreadrunning and (time.time() < nextupdate):
                time.sleep(self.updatethreadsleeptime)
        self.isconnect = False
        self.updatethread_lock.release() # release the lock

    def update(self):
        self.updatelock.acquire() # lock
        self.socket_communication_with_server()
        self.updatelock.release() # release the lock

    def get_actualvalues(self):
        self.get_actualvalues_lock.acquire() # lock
        if self.socket != None:
            try:
                self.send_data_to_socket(self.socket,"getact")
                self.actualvalue = self.receive_data_from_socket(self.socket,self.bufsize)
            except:
                self.log.error("could not get actualvalues from server!")
        self.get_actualvalues_lock.release() # release the lock

    def socket_communication_with_server(self):
        self.socketlock.acquire() # lock
        if self.socket != None:
            if self.setpoint != None:
                # set self.setpoint
                if self.trigger_out:
                    self.send_data_to_socket(self.socket,"p %s!w2d" % self.create_send_format(self.setpoint))
                else:
                    self.send_data_to_socket(self.socket,"p %s" % self.create_send_format(self.setpoint))
                self.myextra_socket_communication_with_server()
            # read self.actualvalue
            self.get_actualvalues()
            self.reading_last = time.time()
        self.socketlock.release() # release the lock

    def myextra_socket_communication_with_server(self):
        """for outside use"""
        pass

    def gui(self):
        self.isgui = True
        self.start_button = tkinter.Button(self.pw,text="start",command=self.start_request,padx=self.padx,pady=self.pady)
        self.start_button.grid(column=0,row=0)
        self.stop_button = tkinter.Button(self.pw,text="stop",command=self.stop_request,state=tkinter.DISABLED,padx=self.padx,pady=self.pady)
        self.stop_button.grid(column=1,row=0)
        self.set_default_values()

    def start_request(self):
        self.lock.acquire() # lock
        if self.isgui:
            self.start_button.after(1, self.start)
        else:
            starttimer = threading.Thread(target=self.start)
            starttimer.daemon = True
            starttimer.start()
        self.lock.release() # release the lock

    def start(self):
        self.lock.acquire() # lock
        self.socketlock.acquire() # lock
        if self.socket == None:
            self.log.debug("first try to connect to %s:%s" % (self.ip,self.sport))
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ip,self.sport))
                self.log.debug("connected")
            except:
                self.socket = None
                self.log.warning("cannot connect")
            if (self.socket == None) and (self.start_server):
                c = [self.cmd]
                if self.dev != "-1":
                    c += ["-device",self.dev]
                if self.serialnumber != "-1":
                    # acceleration sensor
                    c += ["-SerialNumber",self.serialnumber]
                    c += ["-datalogformat","%d" % self.datalogformat]
                    c += ["-maxg","%f" % self.maxg]
                c += ["-logfile",self.logfile,
                      "-datalogfile",self.datalogfile,
                      "-runfile",self.rf,
                      "-ip",self.ip,
                      "-port","%s" % self.sport]
                if self.st != "-1":
                      c += ["-timedelay","%s" % self.st]
                self.log.debug("start %s '%s'" % (self.myservername," ".join(c)))
                prc_srv = subprocess.Popen(c)
                t0 = time.time()
                prc_srv.poll()
                while ((prc_srv.returncode == None) and
                       (time.time()-t0<self.server_max_start_time)):
                    time.sleep(0.01)
                    prc_srv.poll()
                prc_srv.poll()
                if prc_srv.returncode == None:
                    self.log.debug("%s does not fork until now!" % self.myservername)
                else:
                    if prc_srv.returncode == 0:
                        self.log.debug("%s seems to fork" % self.myservername)
                    else:
                        self.log.warning("%s terminate with status: %s" % (self.myservername,prc_srv.returncode))
                time.sleep(0.05)
        if self.socket == None:
            self.log.debug("try to connect to %s:%s" % (self.ip,self.sport))
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ip,self.sport))
                self.log.debug("connected")
            except:
                self.socket = None
                self.log.warning("cannot connect to %s:%s" % (self.ip,self.sport))
        if self.socket != None:
            if self.isgui:
                self.start_button.configure(state=tkinter.DISABLED)
                self.stop_button.configure(state=tkinter.NORMAL)
            self.get_actualvalues()
            self.actualvalue2setpoint()
        self.correct_state_intern()
        self.socketlock.release() # release the lock
        self.lock.release() # release the lock
        if (self.socket != None):
            self.updatethreadrunning = True
            starttimer = threading.Thread(target=self.updatethread)
            starttimer.daemon = True
            starttimer.start()

    def actualvalue2setpoint(self):
        """also for outside use"""
        if self.actualvalue != None and not isinstance(self.actualvalue,list):
            self.setpoint = self.actualvalue.copy()

    def stop_request(self):
        self.updatethreadrunning = False
        if self.isgui:
            self.stop_button.after(1, self.stop)
        else:
            starttimer = threading.Thread(target=self.stop)
            starttimer.daemon = True
            starttimer.start()

    def stop(self):
        self.updatethreadrunning = False
        time.sleep(0.001)
        self.lock.acquire() # lock
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.log.debug("disconnect to %s:%d %s" % (self.ip,self.sport,self.myservername))
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except:
                pass
        self.socket = None
        self.socketlock.release() # release the lock
        self.correct_state_intern()
        self.lock.release() # release the lock

    def correct_state_intern(self):
        if self.isgui:
            if (self.socket != None):
                self.start_button.configure(state=tkinter.DISABLED)
                self.stop_button.configure(state=tkinter.NORMAL)
            else:
                self.start_button.configure(state=tkinter.NORMAL)
                self.stop_button.configure(state=tkinter.DISABLED)
