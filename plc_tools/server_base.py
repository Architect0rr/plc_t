"""draft for our servers

Author: Daniel Mohr
Date: 2013-05-13
"""

import serial
import threading
import time

class controller_class():
    def __init__(self,log=None,datalog=None,device=None,updatedelay=1,*args):
        self.log = log
        self.datalog = datalog
        self.devicename = device
        self.deviceopen = False
        self.boudrate = 9600
        self.databits = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE # serial.STOPBITS_ONE_POINT_FIVE serial.STOPBITS_TWO
        self.readtimeout = 0.1
        self.writetimeout = 0.1
        self.sleeptime = 0.001
        self.minsleeptime = 0.000001
        self.device = serial.Serial(port=None,
                                    baudrate=self.boudrate,
                                    bytesize=self.databits,
                                    parity=self.parity,
                                    stopbits=self.stopbits,
                                    timeout=self.readtimeout,
                                    writeTimeout=self.writetimeout)
        self.device.port = self.devicename
        self.communication_problem = 0
        self.actualvaluelock = threading.Lock()
        self.setpointlock = threading.Lock()
        self.updatelock = threading.Lock()
        self.set_actualvalue_to_the_device_lock = threading.Lock()
        self.send_data_to_socket_lock = threading.Lock()
        self.myinit(*args)
        self.set_actualvalue_to_the_device()
        self.updatedelay = updatedelay # seconds
        self.running = True
        self.lastupdate = time.time()
        self.updatethread = threading.Thread(target=self.updateloop)
        self.updatethread.daemon = True
        self.updatethread.start()

    def myinit(self,*args):
        """for outside use"""
        pass

    def str2boolarray(self,A):
        n = len(A)
        r = n*[False]
        for i in range(n):
            if A[i] == "1":
                r[i] = True
        return r
    def str2bool(self,s):
        if s == "1":
            r = True
        else:
            r = False
        return r
    def str2float(self,s):
        a = s.split(',')
        for i in range(len(a)):
            a[i] = float(a[i])
        return a
    def boolarray2str(self,A):
        n = len(A)
        r = ""
        for i in range(n):
            if A[(n-1)-i]:
                r += "1"
            else:
                r += "0"
        return r
    def boolarray2int(self,A):
        return int(self.boolarray2str(A),2)
    def boolarray2hex(self,A):
        return "%02X" % self.boolarray2int(A)
    def int2boolarray(self,i):
        s = "{0:08b}".format(i)
        A = 8*[False]
        for i in range(8):
            if s[i] == "1":
                A[i] = True
        return A

    def updateloop(self):
        """update

        will update every updatedelay seconds
        
        Author: Daniel Mohr
        Date: 2013-01-25
        """
        global controller
        self.updatelock.acquire() # lock for running
        while self.running:
            self.set_actualvalue_to_the_device()
            nextupdate = self.lastupdate + self.updatedelay
            self.lastupdate = time.time()
            time.sleep(self.minsleeptime)
            while self.running and (time.time() < nextupdate):
                time.sleep(self.sleeptime)
        self.updatelock.release() # release the lock

    def shutdown(self):
        self.log.info("shutdown")
        self.running = False
        time.sleep(2*self.sleeptime)
        if self.device.isOpen():
            self.device.close()
            self.deviceopen = False

    def set_setpoint(self,s=None):
        if s != None:
            self.setpointlock.acquire() # lock to set
            self.setpoint = s.copy()
            self.setpointlock.release() # release the lock

    def get_setpoint(self):
        """get_setpoint
        
        So far as I know, this function is useless.
        It only exist due to completeness.
        
        Author: Daniel Mohr
        Date: 2012-09-30
        """
        self.setpointlock.acquire() # lock to set
        s = self.setpoint
        self.setpointlock.release() # release the lock
        return s

    def get_actualvalue(self):
        self.actualvaluelock.acquire() # lock to get new settings
        a = self.actualvalue.copy()
        self.actualvaluelock.release() # release the lock
        return a
