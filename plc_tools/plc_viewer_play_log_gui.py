"""play_log_gui for plc_viewer

Author: Daniel Mohr
Date: 2013-02-04, 2017-05-30
"""

import PIL.Image
import PIL.ImageTk
import math
import os
import sys
import time
import tkinter
import zipfile

from plc_tools.conversion import *

class play_log_gui():
    def __init__(self,log=None,parent=None,mpclogdata=None,logdata=None,configs=None,timeratefactor=1.0,mt=None):
        self.log = log
        self.parent = parent
        self.mpclogdata = mpclogdata
        self.logdata = logdata
        self.configs = configs
        # turbo pumps
        self.turbo_pump_1_rpm_controller = self.configs.values.get('gas system','turbo_pump_1_rpm_controller')
        self.turbo_pump_1_rpm_port = self.configs.values.get('gas system','turbo_pump_1_rpm_port')
        self.turbo_pump_1_rpm_channel = int(self.configs.values.get('gas system','turbo_pump_1_rpm_channel'))
        self.turbo_pump_2_rpm_controller = self.configs.values.get('gas system','turbo_pump_2_rpm_controller')
        self.turbo_pump_2_rpm_port = self.configs.values.get('gas system','turbo_pump_2_rpm_port')
        self.turbo_pump_2_rpm_channel = int(self.configs.values.get('gas system','turbo_pump_2_rpm_channel'))
        # mass flow
        self.mass_flow_controller = self.configs.values.get('gas system','mass_flow_controller_measure_rate_controller')
        self.mass_flow_port = self.configs.values.get('gas system','mass_flow_controller_measure_rate_port')
        self.mass_flow_channel = int(self.configs.values.get('gas system','mass_flow_controller_measure_rate_channel'))
        self.timeratefactor = timeratefactor
        self.i = 0
        self.n = len(self.mpclogdata)
        self.logdata_i = 0
        self.logdata_n = len(self.logdata)
        self.mt = mt
        self.updateinterval = 1
        self.updateid = None
        self.time = dict()
        self.time['last displayed timestamp'] = None
        self.time['last displayed real'] = 0
        self.time['buffer timestamp'] = None
        self.padx = 3
        self.pady = 3
        self.parent.after(1,func=self._init_())
    def _init_(self):
        # frame number
        self.frame = tkinter.Frame(self.parent)
        self.frame.pack(expand=True,fill=tkinter.X)
        self.frame1 = tkinter.Frame(self.frame)
        self.frame1.pack(expand=True,fill=tkinter.X)
        self.frame2 = tkinter.Frame(self.frame)
        self.frame2.pack(expand=True,fill=tkinter.X)
        self.frame3 = tkinter.Frame(self.frame)
        self.frame3.pack(expand=True,fill=tkinter.X)
        self.frame4 = tkinter.Frame(self.frame)
        self.frame4.pack(expand=True,fill=tkinter.X)
        # turbo pumps
        self.turbo_pumps_label = tkinter.Label(self.frame1,text="Turbo Pumps:")
        self.turbo_pumps_label.pack(side=tkinter.LEFT)
        self.turbo_pump_1_rpm_val = tkinter.StringVar()
        self.turbo_pump_1_rpm_label = tkinter.Label(self.frame1,textvariable=self.turbo_pump_1_rpm_val,height=1,width=6)
        self.turbo_pump_1_rpm_label.pack(side=tkinter.LEFT)
        self.turbo_pump_2_rpm_val = tkinter.StringVar()
        self.turbo_pump_2_rpm_label = tkinter.Label(self.frame1,textvariable=self.turbo_pump_2_rpm_val,height=1,width=6)
        self.turbo_pump_2_rpm_label.pack(side=tkinter.LEFT)
        # mass flow
        self.mass_flow_description = tkinter.Label(self.frame2,text="Mass Flow:")
        self.mass_flow_description.pack(side=tkinter.LEFT)
        self.mass_flow_val = tkinter.StringVar()
        self.mass_flow_label = tkinter.Label(self.frame2,textvariable=self.mass_flow_val,height=1,width=14)
        self.mass_flow_label.pack(side=tkinter.LEFT)
        # RF
        # logdata
        self.logdata_description = tkinter.Label(self.frame4,text="Log:")
        self.logdata_description.pack(side=tkinter.LEFT)
        self.logdata_val = tkinter.StringVar()
        self.logdata_label = tkinter.Label(self.frame4,textvariable=self.logdata_val,height=5,width=42)
        self.logdata_label.pack(side=tkinter.LEFT)
    def destroy(self):
        pass

    def go(self,step):
        self.i = max(0,min(self.i+step,self.n-1))
        self.logdata_i = max(0,min(self.logdata_i+step,self.logdata_n-1))
        self.displaylogs()
    def gos(self):
        [ok,i,t] = self.ifromtime(self.logdata,self.logdata_n,self.logdata_i)
        if ok:
            self.logdata_i = max(0,min(i,self.logdata_n-1))
        else:
            # display nothing
            pass
        [ok,i,t] = self.ifromtime(self.mpclogdata,self.n,self.i)
        if ok:
            self.i = i
            self.displaylogs()
        else:
            # display nothing
            pass

    def onlydisplaylogs(self):
        # turbo pumps
        v = self.mpclogdata[self.i][1][self.turbo_pump_1_rpm_controller][self.turbo_pump_1_rpm_port][self.turbo_pump_1_rpm_channel]
        v = round(100*v/32767.0)
        self.turbo_pump_1_rpm_val.set("%d %%" % v)
        v = self.mpclogdata[self.i][1][self.turbo_pump_2_rpm_controller][self.turbo_pump_2_rpm_port][self.turbo_pump_2_rpm_channel]
        v = round(100*v/32767.0)
        self.turbo_pump_2_rpm_val.set("%d %%" % v)
        # mass flow
        v = self.mpclogdata[self.i][1][self.mass_flow_controller][self.mass_flow_port][self.mass_flow_channel]
        self.mass_flow_val.set("%.2f msccm" % adc2msccm(v))
        # logdata
        s = ""
        n = 10
        tt = self.mt.gettime()
        if len(self.logdata) > 0:
            for i in range(n):
                t = self.logdata[max(0,self.logdata_i-i)][0]
                if (0 < tt-t) and (tt-t < 10*self.timeratefactor):
                    t = "(%s.%03d)" % (time.strftime("%H:%M:%S",time.localtime(t)),int(math.floor((t-math.floor(t))*1000)))
                    a = self.logdata[max(0,self.logdata_i-((n-1)+i))][1]
                    s = "%s %s\n%s" % (t,a,s)
            self.logdata_val.set(s)
    def displaylogs(self):
        self.onlydisplaylogs()
        self.time['last displayed real'] = time.time()
        self.time['last displayed timestamp'] = self.time['buffer timestamp']

    def timestamps_available(self):
        r = False
        if (self.time['buffer timestamp'] != None) and (self.time['last displayed real'] != None) and (self.time['last displayed timestamp'] != None):
            r = True
        return r

    def delta_time_last_displayed(self):
        return (time.time()-self.time['last displayed real'])*self.timeratefactor
    def delta_timestamp_last_displayed(self):
        return abs(self.time['buffer timestamp'] - self.time['last displayed timestamp'])

    def ifromtime(self,db,n,i=None,t=None):
        if n > 0:
            self.log.debug("search i")
            if i == None:
                i = self.i
            if t == None:
                t = self.mt.gettime()
            imin = 0
            imax = n - 1
            #i = int((imax + imin + 1) / 2)
            while imax-imin > 1:
                if t <= db[i][0]:
                    imax = i
                if t >= db[i][0]:
                    imin = i
                i = int((imax + imin + 1) / 2)
            if (i < imax) and (abs(db[i+1][0]-t) < abs(db[i][0]-t)):
                i = i + 1
            if abs(t - db[i][0]) <= 1*self.timeratefactor:
                self.log.debug("found i = %d" % i)
                ok = True
            else:
                self.log.debug("no i found")
                ok = False
        else:
            self.log.debug("no data to search i")
            ok = False
        return [ok,i,t]

    def play(self):
        if self.updateid != None:
            self.frame.after_cancel(self.updateid)
            self.updateid = None
        [ok,i,t] = self.ifromtime(self.logdata,self.logdata_n,self.logdata_i)
        if ok:
            self.logdata_i = i
        [ok,i,t] = self.ifromtime(self.mpclogdata,self.n,self.i)
        if ok:
            self.i = i
            if (0 <= self.i) and (self.i < self.n):
                self.log.debug("play")
                a = 0
                d = True
                if self.timestamps_available():
                    d = False
                    self.log.debug("%f >= %f ??" % (self.delta_time_last_displayed(),self.delta_timestamp_last_displayed()))
                    if self.delta_time_last_displayed() >= self.delta_timestamp_last_displayed():
                        a = 1
                        d = True
                    else:
                        a = 2
                    self.log.debug("update: %d" % self.updateinterval)
                if d:
                    self.displaylogs()
                if a == 1:
                    self.updateinterval = max(self.minupdateinterval1,min(self.maxupdateinterval1,int(round(1000*abs(self.mpclogdata[min(self.i+1,self.n-1)][0]-t)/3.0/self.timeratefactor))))
                elif a == 2:
                    self.updateinterval = max(self.minupdateinterval2,min(self.maxupdateinterval2,int(round(1000*abs(self.mpclogdata[self.i][0]-self.mt.gettime())/self.timeratefactor))))
                self.updateid = self.frame.after(self.updateinterval,func=self.play)
            else:
                self.i = self.n-1
                self.logdata_i = self.logdata_n-1
                self.displaylogs()
                self.stop()
        else:
            # display nothing
            self.time['last displayed timestamp'] = None
            self.updateinterval = 50
            self.updateid = self.frame.after(self.updateinterval,func=self.play)
    def stop(self):
        self.log.debug("stop")
        if self.updateid != None:
            self.frame.after_cancel(self.updateid)
        self.time['last displayed timestamp'] = None
