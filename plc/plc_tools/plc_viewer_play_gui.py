"""play_gui for plc_viewer

Author: Daniel Mohr
Date: 2012-09-28, 2013-02-04, 2013-04-09, 2013-10-20, 2017-05-30
"""

import os
import zipfile
import io
import PIL.Image
import tkinter
import PIL.ImageTk
import time
import sys
import threading

class play_gui():
    def __init__(self,log=None,parent=None,db=None,timeratefactor=1.0,scale=1.0,absolutscale=None,mt=None,minupdateinterval1=6,maxupdateinterval1=42,minupdateinterval2=1,maxupdateinterval2=23,gamma=1.0):
        self.playchangedisplayparaemterlock = threading.Lock()
        self.log = log
        self.parent = parent
        self.db = db
        self.dt = abs(self.db[1][0]-self.db[0][0])
        self.timeratefactor = timeratefactor
        self.scale = scale
        self.oldscale = scale
        self.absolutscale = absolutscale
        self.i = 0
        self.mt = mt
        self.minupdateinterval1 = minupdateinterval1
        self.maxupdateinterval1 = maxupdateinterval1
        self.minupdateinterval2 = minupdateinterval2
        self.maxupdateinterval2 = maxupdateinterval2
        self.gamma = gamma
        self.palette = 256
        self.updateinterval = 1
        self.updateid = None
        self.zips = dict()
        self.zipsopen = dict()
        self.time = dict()
        self.time['last displayed timestamp'] = None
        self.time['last displayed real'] = 0
        self.time['buffer timestamp'] = None
        self.picture_in_buffer = False
        self.picture_in_buffer_i = -1
        self.padx = 3
        self.pady = 3
        self.parent.after(1,func=self._init_())
    def _init_(self):
        self.readimage()
        self.log.debug("size: %sx%s" % self.pic.size)
        [self.width,self.height] = self.pic.size
        if (self.absolutscale != None) and (self.absolutscale > 0):
            self.scale = float(self.absolutscale) / self.width
            self.log.debug("set scale to %f (width = %d)" % (self.scale,self.absolutscale))
        self.swidth = int(self.scale*self.width)
        self.sheight = int(self.scale*self.height)
        self.log.debug("set scale width*height to %dx%d" % (self.swidth,self.sheight))
        if self.height != self.sheight:
            self.pic = self.pic.resize((self.swidth,self.sheight))
        self.n = len(self.db)
        # frame number
        self.frame = tkinter.Frame(self.parent)
        self.frame.pack(expand=True,fill=tkinter.X)
        self.status_val = tkinter.StringVar()
        self.status_label = tkinter.Label(self.frame,textvariable=self.status_val,height=1,width=16)
        self.status_label.pack(side=tkinter.RIGHT)
        # gamma
        self.gammalabel = tkinter.Label(self.frame,text="gamma: ")
        self.gammalabel.pack(side=tkinter.LEFT)
        self.gammavar = tkinter.DoubleVar()
        self.gammavar.set(self.gamma)
        self.gammaentry = tkinter.Entry(self.frame,textvariable=self.gammavar,width=5)
        self.gammaentry.pack(side=tkinter.LEFT)
        # palette (number of colors)
        self.palettelabel = tkinter.Label(self.frame,text="palette: ")
        self.palettelabel.pack(side=tkinter.LEFT)
        self.palettevar = tkinter.DoubleVar()
        self.palettevar.set(self.palette)
        self.paletteentry = tkinter.Entry(self.frame,textvariable=self.palettevar,width=5)
        self.paletteentry.pack(side=tkinter.LEFT)        
        # change display paraemter
        self.change_display_parameter_button = tkinter.Button(self.frame,text="set",command=self.changedisplayparaemter,padx=self.padx,pady=self.pady)
        self.change_display_parameter_button.pack(side=tkinter.LEFT)
        # scale
        self.label2_var = tkinter.StringVar()
        self.label2 = tkinter.Label(self.frame,textvariable=self.label2_var, width=11,height=1)
        self.label2.pack(side=tkinter.LEFT)
        self.label2_var.set("scale %2.2f" % self.scale)
        self.scalehalfbutton = tkinter.Button(self.frame,text="*0.5",command=self.scalehalf,padx=self.padx,pady=self.pady)
        self.scalehalfbutton.pack(side=tkinter.LEFT)
        self.scaledoublebutton = tkinter.Button(self.frame,text="*2",command=self.scaledouble,padx=self.padx,pady=self.pady)
        self.scaledoublebutton.pack(side=tkinter.LEFT)
        self.display_on_off = True
        self.display_on_off_var = tkinter.IntVar()
        self.display_on_off_checkbutton = tkinter.Checkbutton(self.frame,text="On/Off",variable=self.display_on_off_var,command=self.switch_display_on_off)
        self.display_on_off_checkbutton.pack(side=tkinter.LEFT)
        self.display_on_off_checkbutton.select()
        # movie frame
        self.picture = None
        self.img = PIL.ImageTk.PhotoImage("L",(self.swidth,self.sheight),gamma=self.gamma,palette=self.palette)
        #self.pic = PIL.Image.new("L",(self.swidth,self.sheight))
        self.img.paste(self.pic)
        self.movie_label_after_running = False
        self.movie_label = tkinter.Label(self.parent, image=self.img)
        self.movie_label.pack()
        # name of the file for this frame
        self.frame2 = tkinter.Frame(self.parent)
        self.frame2.pack()
        self.file_name_output_var = tkinter.StringVar()
        self.file_name_output_label = tkinter.Label(self.frame2,textvariable=self.file_name_output_var,height=1)
        self.file_name_output_label.pack(side=tkinter.LEFT)
        self.onlydisplayimage()

    def switch_display_on_off(self):
        if self.display_on_off_var.get() == 1:
            if not self.display_on_off:
                # switch to on
                self.display_on_off = True
        else:
            if self.display_on_off:
                # switch to off
                self.display_on_off = False

    def scalehalf(self):
        self.scale = self.scale / 2.0
        self.changedisplayparaemter()
    def scaledouble(self):
        self.scale = self.scale * 2.0
        self.changedisplayparaemter()
    def changedisplayparaemter(self):
        self.playchangedisplayparaemterlock.acquire() # lock
        try:
            gamma = float(self.gammavar.get())
            if 0.0 <= gamma and gamma <= 1000.0:
                self.gamma = gamma
        except: pass
        try:
            palette = float(self.palettevar.get())
            if 1 <= palette and palette <= 256:
                self.palette = int(palette)
        except: pass
        self.label2_var.set("scale %2.2f" % self.scale)
        self.swidth = int(self.scale*self.width)
        self.sheight = int(self.scale*self.height)
        self.movie_label.destroy()
        self.file_name_output_label.destroy()
        self.frame2.destroy()
        self.img = PIL.ImageTk.PhotoImage("L",(self.swidth,self.sheight),gamma=self.gamma,palette=self.palette)
        self.movie_label = tkinter.Label(self.parent, image=self.img)
        self.movie_label.pack()
        self.frame2 = tkinter.Frame(self.parent)
        self.frame2.pack()
        self.file_name_output_label = tkinter.Label(self.frame2,textvariable=self.file_name_output_var,height=1)
        self.file_name_output_label.pack(side=tkinter.LEFT)
        if self.pic != None:
            if self.scale != self.oldscale:
                self.pic = self.pic.resize((self.swidth,self.sheight))
            self.onlydisplayimage()
        self.oldscale = self.scale
        if self.movie_label_after_running:
            self.updateid = self.movie_label.after(self.updateinterval,func=self.play)
        self.playchangedisplayparaemterlock.release() # release the lock

    def readimage(self):
        self.log.debug("read image %d " % self.i)
        if not os.path.isfile(self.db[self.i][1]):
            log.error("File \"%s\" does not exists!" % self.db[self.i][1])
            sys.exit(1)
        if ((not self.db[self.i][1] in self.zips) or
            (not self.zipsopen[self.db[self.i][1]])):
            self.log.debug("open \"%s\"" % self.db[self.i][1])
            self.zips[self.db[self.i][1]] = zipfile.ZipFile(self.db[self.i][1],"r")
            self.zipsopen[self.db[self.i][1]] = True
        zipdata = io.StringIO(self.zips[self.db[self.i][1]].read(self.db[self.i][2]))
        self.pic = PIL.Image.open(zipdata)
        self.pic.load()
        zipdata.close()
        #a = self.pic.histogram()
        #print a
        self.time['buffer timestamp'] = self.db[self.i][0]
    def destroy(self):
        for zip in list(self.zips.keys()):
            if self.zipsopen[self.db[self.i][1]]:
                self.log.debug("close \"%s\"" % zip)
                self.zips[zip].close()
    def go(self,step):
        self.i = max(0,min(self.i+step,self.n-1))
        if self.display_on_off:
            self.readimage()
            if self.height != self.sheight:
                self.pic = self.pic.resize((self.swidth,self.sheight))
            self.playchangedisplayparaemterlock.acquire() # lock
            self.displayimage()
            self.playchangedisplayparaemterlock.release() # release the lock
    def gos(self):
        if self.display_on_off:
            [ok,i,t] = self.ifromtime(self.i)
            if ok:
                self.i = i
                self.readimage()
                if self.height != self.sheight:
                    self.pic = self.pic.resize((self.swidth,self.sheight))
                self.playchangedisplayparaemterlock.acquire() # lock
                self.displayimage()
                self.playchangedisplayparaemterlock.release() # release the lock
            else:
                self.pic = PIL.Image.new("L",(self.swidth,self.sheight),color=0)
                self.img.paste(self.pic)

    def onlydisplayimage(self):
        self.img.paste(self.pic)
        self.status_val.set("%d of %d" % (self.i+1,self.n))
        self.file_name_output_var.set("%s" % (self.db[self.i][2]))
    def displayimage(self):
        self.onlydisplayimage()
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

    def ifromtime(self,i=None,t=None):
        self.log.debug("search i")
        if i == None:
            i = self.i
        if t == None:
            t = self.mt.gettime()
        imin = 0
        imax = self.n - 1
        #i = int((imax + imin + 1) / 2)
        while imax-imin > 1:
            if t <= self.db[i][0]:
                imax = i
            if t >= self.db[i][0]:
                imin = i
            i = int((imax + imin + 1) / 2)
        if (i < imax) and (abs(self.db[i+1][0]-t) < abs(self.db[i][0]-t)):
            i = i + 1
        if abs(t - self.db[i][0]) <= 1*self.timeratefactor:
            self.log.debug("found i = %d" % i)
            ok = True
        else:
            self.log.debug("no i found")
            ok = False
        return [ok,i,t]

    def play(self):
        self.playchangedisplayparaemterlock.acquire() # lock
        self.movie_label_after_running = False
        if self.updateid != None:
            self.movie_label.after_cancel(self.updateid)
            self.updateid = None
        ok = False
        if self.display_on_off:
            [ok,i,t] = self.ifromtime(self.i)
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
                    if not self.picture_in_buffer:
                        if self.picture_in_buffer_i != self.i:
                            self.readimage()
                            if self.height != self.sheight:
                                self.pic = self.pic.resize((self.swidth,self.sheight))
                            self.picture_in_buffer_i = self.i
                        self.picture_in_buffer = True
                    self.displayimage()
                    self.picture_in_buffer = False
                if a == 1:
                    #self.updateinterval = max(self.minupdateinterval1,min(self.maxupdateinterval1,int(round(1000*self.delta_timestamp_last_displayed()/2.0/self.timeratefactor))))
                    self.updateinterval = max(self.minupdateinterval1,min(self.maxupdateinterval1,int(round(1000*abs(self.db[min(self.i+1,self.n-1)][0]-t)/3.0/self.timeratefactor))))
                elif a == 2:
                    #self.updateinterval = max(self.minupdateinterval2,min(self.maxupdateinterval2,int(round(1000*(self.delta_timestamp_last_displayed() - self.delta_time_last_displayed())/self.timeratefactor))))
                    self.updateinterval = max(self.minupdateinterval2,min(self.maxupdateinterval2,int(round(1000*abs(self.db[self.i][0]-self.mt.gettime())/self.timeratefactor))))
                self.movie_label_after_running = True
                self.updateid = self.movie_label.after(self.updateinterval,func=self.play)
            else:
                self.i = self.n-1
                self.displayimage()
                self.stop()
        else:
            pic = PIL.Image.new("L",(self.swidth,self.sheight),color=0)
            self.img.paste(pic)
            self.time['last displayed timestamp'] = None
            self.updateinterval = 50
            if not self.display_on_off:
                self.updateinterval = 500
            self.movie_label_after_running = True
            self.updateid = self.movie_label.after(self.updateinterval,func=self.play)
        self.playchangedisplayparaemterlock.release() # release the lock
    def stop(self):
        self.playchangedisplayparaemterlock.acquire() # lock
        self.log.debug("stop")
        if self.updateid != None:
            self.movie_label.after_cancel(self.updateid)
        self.time['last displayed timestamp'] = None
        self.playchangedisplayparaemterlock.release() # release the lock
