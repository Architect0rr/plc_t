"""play_rflog_gui for plc_viewer

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

class play_rflog_gui():
    def __init__(self,log=None,parent=None,rflogdata=None,configs=None,timeratefactor=1.0,mt=None):
        self.log = log
        self.parent = parent
        self.rflogdata = rflogdata
        self.configs = configs
        self.timeratefactor = timeratefactor
        self.i = 0
        self.n = len(self.rflogdata)
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
        self.elements = [None,None,None]
        self.header1 = tkinter.Label(self.frame,text="current")
        self.header1.grid(column=2,row=0)
        self.header2 = tkinter.Label(self.frame,text="phase")
        self.header2.grid(column=3,row=0)
        channel = 1
        for g in range(3):
            if (len(self.rflogdata)>0) and self.rflogdata[0][1][g]['exists']:
                self.elements[g] = dict()
                self.elements[g]['rf_onoff'] = tkinter.Checkbutton(self.frame,text="RF",state=tkinter.DISABLED)
                self.elements[g]['rf_onoff'].grid(column=0,row=channel)
                if self.rflogdata[0][1][g]['rf_onoff']:
                    self.elements[g]['rf_onoff'].select()
                else:
                    self.elements[g]['rf_onoff'].deselect()
                self.elements[g]['current'] = [None,None,None,None]
                self.elements[g]['phase'] = [None,None,None,None]
                self.elements[g]['channel_onoff'] = [None,None,None,None]
                for i in range(4):
                    #
                    self.elements[g]['channel_onoff'][i] = tkinter.Checkbutton(self.frame,text="Pwr Channel %d" % (channel),state=tkinter.DISABLED)
                    self.elements[g]['channel_onoff'][i].grid(column=1,row=channel)
                    if self.rflogdata[0][1][g]['channel'][i]['onoff']:
                        self.elements[g]['channel_onoff'][i].select()
                    else:
                        self.elements[g]['channel_onoff'][i].deselect()
                    #
                    self.elements[g]['current'][i] = dict()
                    self.elements[g]['current'][i]['val'] = tkinter.StringVar()
                    self.elements[g]['current'][i]['label'] = tkinter.Label(self.frame,textvariable=self.elements[g]['current'][i]['val'],height=1,width=6)
                    self.elements[g]['current'][i]['label'].grid(column=2,row=channel)
                    self.elements[g]['current'][i]['val'].set("%d" % self.rflogdata[0][1][g]['channel'][i]['current'])
                    #
                    self.elements[g]['phase'][i] = dict()
                    self.elements[g]['phase'][i]['val'] = tkinter.StringVar()
                    self.elements[g]['phase'][i]['label'] = tkinter.Label(self.frame,textvariable=self.elements[g]['phase'][i]['val'],height=1,width=6)
                    self.elements[g]['phase'][i]['label'].grid(column=3,row=channel)
                    self.elements[g]['phase'][i]['val'].set("%d" % self.rflogdata[0][1][g]['channel'][i]['phase'])
                    #
                    channel += 1
    def destroy(self):
        pass

    def go(self,step):
        self.i = max(0,min(self.i+step,self.n-1))
        self.displaylogs()
    def gos(self):
        [ok,i,t] = self.ifromtime(self.rflogdata,self.n,self.i)
        if ok:
            self.i = i
            self.displaylogs()
        else:
            # display nothing
            pass

    def onlydisplaylogs(self):
        for g in range(3):
            if (len(self.rflogdata)>0) and self.rflogdata[self.i][1][g]['exists']:
                if self.rflogdata[self.i][1][g]['rf_onoff']:
                    self.elements[g]['rf_onoff'].select()
                else:
                    self.elements[g]['rf_onoff'].deselect()
                for i in range(4):
                    self.elements[g]['current'][i]['val'].set("%d" % self.rflogdata[self.i][1][g]['channel'][i]['current'])
                    self.elements[g]['phase'][i]['val'].set("%d" % self.rflogdata[0][1][g]['channel'][i]['phase'])
                    if self.rflogdata[self.i][1][g]['channel'][i]['onoff']:
                        self.elements[g]['channel_onoff'][i].select()
                    else:
                        self.elements[g]['channel_onoff'][i].deselect()
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
            if (db[i][0] > t):
                i = max(0,i-1)
            ok = True
        else:
            self.log.debug("no data to search i")
            ok = False
        return [ok,i,t]

    def play(self):
        if self.updateid != None:
            self.frame.after_cancel(self.updateid)
            self.updateid = None
        [ok,i,t] = self.ifromtime(self.rflogdata,self.n,self.i)
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
                    self.updateinterval = max(self.minupdateinterval1,min(self.maxupdateinterval1,int(round(1000*abs(self.rflogdata[min(self.i+1,self.n-1)][0]-t)/3.0/self.timeratefactor))))
                elif a == 2:
                    self.updateinterval = max(self.minupdateinterval2,min(self.maxupdateinterval2,int(round(1000*abs(self.rflogdata[self.i][0]-self.mt.gettime())/self.timeratefactor))))
                self.updateid = self.frame.after(self.updateinterval,func=self.play)
            else:
                self.i = self.n-1
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
