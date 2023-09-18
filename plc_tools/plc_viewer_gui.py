"""gui for plc_viewer

Author: Daniel Mohr
Date: 2013-04-09, 2017-05-30
"""

import tkinter
import PIL.ImageTk
import re
import zipfile
import io
import PIL.Image
import PIL.ImageDraw
import PIL.ImageMath
import time
import math
import pickle

from plc_tools.plc_viewer_movietime import movietime
from plc_tools.plc_viewer_play_gui import play_gui
from plc_tools.plc_viewer_movietime import movietime
from plc_tools.plc_viewer_play_log_gui import play_log_gui
from plc_tools.plc_viewer_play_rflog_gui import play_rflog_gui

class gui():
    def __init__(self,log=None,mpclogdata=None,logdata=None,rflogdata=None,brightness=None,diffs=None,indexfile=None,brightnessfile=None,diffsfile=None,configs=None,timestamps=[],camcolumn=2,timeratefactor=1.0,scale=1.0,absolutscale=None,timestamp_min=0,timestamp_max=0,minupdateinterval1=6,maxupdateinterval1=42,minupdateinterval2=1,maxupdateinterval2=23,create_info_graphics=None,gamma=1.0):
        self.log = log
        self.mpclogdata = mpclogdata
        self.logdata = logdata
        self.rflogdata = rflogdata
        self.brightness =brightness
        self.diffs = diffs
        self.indexfile = indexfile
        self.brightnessfile = brightnessfile
        self.diffsfile = diffsfile
        self.configs = configs
        self.timestamps = timestamps
        self.timeratefactor = timeratefactor
        self.scale = scale
        self.absolutscale = absolutscale
        self.timestamp_min = timestamp_min
        self.timestamp_max = timestamp_max
        self.minupdateinterval1 = minupdateinterval1
        self.maxupdateinterval1 = maxupdateinterval1
        self.minupdateinterval2 = minupdateinterval2
        self.maxupdateinterval2 = maxupdateinterval2
        self.create_info_graphics = create_info_graphics
        self.gamma = gamma
        self.mt = movietime(self.timestamp_min,self.timestamp_max,self.timeratefactor)
        self.mt.setstatus("stop")
        self.padx = 3
        self.pady = 3
        self.repeatdelay = 500
        self.repeatinterval = 10
        self.updateinterval = 10
        self.updateid = None
        self.infoframeready = False
        self.infoframeupdateid = None
        self.infoframecreateupdateid = None
        self.infoframelastupdatetime = 0
        # create gui
        self.main_window = tkinter.Tk()
        self.main_window.title("plc_viewer")
        # controlframe
        self.controlframe = tkinter.Frame(self.main_window)
        self.controlframe.pack(expand=True,fill=tkinter.X)
        self.minus100sbutton = tkinter.Button(self.controlframe,text="-100s",command=self.gominus100s,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.minus100sbutton.pack(side=tkinter.LEFT)
        self.minus10sbutton = tkinter.Button(self.controlframe,text="-1s",command=self.gominus10s,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.minus10sbutton.pack(side=tkinter.LEFT)
        self.minus1sbutton = tkinter.Button(self.controlframe,text="-0.01s",command=self.gominus1s,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.minus1sbutton.pack(side=tkinter.LEFT)
        self.minus1button = tkinter.Button(self.controlframe,text="-1",command=self.gominus1,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.minus1button.pack(side=tkinter.LEFT)
        self.yalpbutton = tkinter.Button(self.controlframe,text="yalp",command=self.yalp,padx=self.padx,pady=self.pady)
        self.yalpbutton.pack(side=tkinter.LEFT)
        self.stopbutton = tkinter.Button(self.controlframe,text="stop",command=self.stop,padx=self.padx,pady=self.pady)
        self.stopbutton.pack(side=tkinter.LEFT)
        self.playbutton = tkinter.Button(self.controlframe,text="play",command=self.play,padx=self.padx,pady=self.pady)
        self.playbutton.pack(side=tkinter.LEFT)
        self.plus1button = tkinter.Button(self.controlframe,text="+1",command=self.goplus1,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.plus1button.pack(side=tkinter.LEFT)
        self.plus1sbutton = tkinter.Button(self.controlframe,text="+0.01s",command=self.goplus1s,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.plus1sbutton.pack(side=tkinter.LEFT)
        self.plus10sbutton = tkinter.Button(self.controlframe,text="+1s",command=self.goplus10s,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.plus10sbutton.pack(side=tkinter.LEFT)
        self.plus100sbutton = tkinter.Button(self.controlframe,text="+100s",command=self.goplus100s,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.plus100sbutton.pack(side=tkinter.LEFT)
        # timerate
        self.timerate_var = tkinter.StringVar()
        self.timerate_label = tkinter.Label(self.controlframe,textvariable=self.timerate_var, width=16,height=1)
        self.timerate_label.pack(side=tkinter.LEFT)
        self.timerate_var.set("timerate * %1.2f" % self.timeratefactor)
        self.timeratehalfbutton = tkinter.Button(self.controlframe,text="*0.5",command=self.timeratehalf,padx=self.padx,pady=self.pady)
        self.timeratehalfbutton.pack(side=tkinter.LEFT)
        self.timeratedoublebutton = tkinter.Button(self.controlframe,text="*2",command=self.timeratedouble,padx=self.padx,pady=self.pady)
        self.timeratedoublebutton.pack(side=tkinter.LEFT)
        # frame time
        self.time_val = tkinter.StringVar()
        self.time_label = tkinter.Label(self.controlframe,textvariable=self.time_val,height=1,width=26)
        self.time_label.pack(side=tkinter.RIGHT)
        # info
        if self.create_info_graphics == 1:
            self.infoframe = tkinter.Frame(self.main_window)
            self.infoframe.pack(expand=True,fill=tkinter.X)
            self.infoframestatus = 0
            self.infoframecreatepicture()
        # output frames
        self.outframe = tkinter.Frame(self.main_window)
        self.outframe.pack(expand=True,fill=tkinter.X)
        self.outframes = dict()
        gx = 0 # column
        gxm = camcolumn - 1 # max column
        gy = 0 # row
        for i in range(len(self.timestamps)):
            r = re.findall("([^.]+)[0-9]{3}.zip",self.timestamps[i][0][1])
            if r:
                title = r[0]
            else:
                title = ""
            self.outframes[i] = dict()
            self.outframes[i]['frame'] = tkinter.LabelFrame(self.outframe,text=title)
            self.outframes[i]['frame'].grid(column=gx,row=gy)
            gx = gx+1
            if gx > gxm:
                gx = 0
                gy = gy + 1
            self.outframes[i]['playgui'] = play_gui(log=self.log,parent=self.outframes[i]['frame'],db=self.timestamps[i],timeratefactor=self.timeratefactor,scale=self.scale,absolutscale=self.absolutscale,mt=self.mt,minupdateinterval1=self.minupdateinterval1,maxupdateinterval1=self.maxupdateinterval1,minupdateinterval2=self.minupdateinterval2,maxupdateinterval2=self.maxupdateinterval2,gamma=self.gamma)
        i = len(self.timestamps)
        if self.mpclogdata != None:
            # log output
            self.outframes[i] = dict()
            self.outframes[i]['frame'] = tkinter.LabelFrame(self.outframe,text="logs")
            self.outframes[i]['frame'].grid(column=gx,row=gy)
            gx = gx+1
            if gx > gxm:
                gx = 0
                gy = gy + 1
            self.outframes[i]['playgui'] = play_log_gui(log=self.log,parent=self.outframes[i]['frame'],mpclogdata=self.mpclogdata,logdata=self.logdata,configs=self.configs,timeratefactor=self.timeratefactor,mt=self.mt)
        i = i + 1
        if self.rflogdata != None:
            # rf-log output
            self.outframes[i] = dict()
            self.outframes[i]['frame'] = tkinter.LabelFrame(self.outframe,text="rf-logs")
            self.outframes[i]['frame'].grid(column=gx,row=gy)
            gx = gx+1
            if gx > gxm:
                gx = 0
                gy = gy + 1
            self.outframes[i]['playgui'] = play_rflog_gui(log=self.log,parent=self.outframes[i]['frame'],rflogdata=self.rflogdata,configs=self.configs,timeratefactor=self.timeratefactor,mt=self.mt)

    def create_image_from_array(self,w,h,d,ii,createtime=False,m=None):
        if createtime:
            pic = m
            draw = PIL.ImageDraw.Draw(pic)
            t = self.mt.gettime()
            x = w * (t-self.timestamp_min)/(self.timestamp_max-self.timestamp_min)
            draw.line((x,0, x,h),fill=128)
            self.log.debug("line")
            self.infoframelastupdatetime = t
            del draw
        else:
            pic = PIL.Image.new("L",(w,h),color=0)
            if len(d[ii]) > 0:
                draw = PIL.ImageDraw.Draw(pic)
                a = d[ii][0][1]
                b = a
                for i in range(len(d[ii])):
                    if d[ii][i][1] < a:
                        a = d[ii][i][1]
                    if d[ii][i][1] > b:
                        b = d[ii][i][1]
                for i in range(len(d[ii])):
                    x = w * (d[ii][i][0]-self.timestamp_min)/(self.timestamp_max-self.timestamp_min)
                    if b-a != 0:
                        y = h - h * (d[ii][i][1]-a) / (b-a)
                    else:
                        y = h
                    x = int(round(x))
                    y = int(round(y))
                    draw.line((x,0, x,y),fill=0)
                    draw.line((x,y, x,h),fill=255)
                del draw
        return pic

    def ifromtime(self,t,db,ii):
        i = 0
        imin = 0
        imax = len(db[ii]) - 1
        #i = int((imax + imin + 1) / 2)
        while imax-imin > 1:
            if t <= db[ii][i][0]:
                imax = i
            if t >= db[ii][i][0]:
                imin = i
            i = int((imax + imin + 1) / 2)
        if (i < imax) and (abs(db[ii][i+1][0]-t) < abs(db[ii][i][0]-t)):
            i = i + 1
        return i

    def create_image_from_arrays(self,w,h,brightness,diffs,createtime=False,m=None):
        w = len(self.timestamps) * w
        if createtime:
            pic = m
            draw = PIL.ImageDraw.Draw(pic)
            t = self.mt.gettime()
            x = w * (t-self.timestamp_min)/(self.timestamp_max-self.timestamp_min)
            draw.line((x,0, x,h),fill=(255,255,255))
            del draw
        else:
            pic = PIL.Image.new("RGB",(w,h),color=(0,0,0))
            draw = PIL.ImageDraw.Draw(pic)
            min_brightness = brightness[0][0][1]
            max_brightness = min_brightness
            min_diffs = diffs[0][0][1]
            max_diffs = min_diffs
            for ii in range(len(self.timestamps)): # for every movie
                for i in range(len(brightness[ii])):
                    if brightness[ii][i][1] < min_brightness:
                        min_brightness = brightness[ii][i][1]
                    if brightness[ii][i][1] > max_brightness:
                        max_brightness = brightness[ii][i][1]
                for i in range(len(diffs[ii])):
                    if diffs[ii][i][1] < min_diffs:
                        min_diffs = diffs[ii][i][1]
                    if diffs[ii][i][1] > max_diffs:
                        max_diffs = diffs[ii][i][1]
            t = self.timestamp_min
            while t < self.timestamp_max:
                x = w * (t-self.timestamp_min)/(self.timestamp_max-self.timestamp_min)
                y = 0
                for ii in range(len(self.timestamps)): # for every movie
                    i = self.ifromtime(t,diffs,ii)
                    y += h * (diffs[ii][i][1]-min_diffs)/float(max_diffs-min_diffs)
                y = max(0,min(int(y),h))
                c = []
                for ii in range(len(self.timestamps)): # for every movie
                    i = self.ifromtime(t,brightness,ii)
                    if abs(t - brightness[ii][i][0]) <= self.infoframe_i_step:
                        c += [int(255 * (brightness[ii][i][1]-min_brightness)/(max_brightness-min_brightness))]
                    else:
                        c += [0]
                while len(c) < 3:
                    c += [0]
                draw.line((x,int(h/2.0-y/2.0), x,int(h/2.0+y/2.0)),fill=(c[0],c[1],c[2]))
                t += self.infoframe_i_step/3.0
            del draw
        return pic

    def create_infoframe_pictures(self,createtime=False):
        if createtime:
            # create only time
            for i in range(len(self.timestamps)):
                self.brightnesspic[i] = self.create_image_from_array(self.graphic1_width,self.graphic1_height,self.brightness,i,createtime=createtime,m=self.master_brightnesspic[i].copy())
                self.brightnessgraphic[i].paste(self.brightnesspic[i])
                self.diffpic[i] = self.create_image_from_array(self.graphic1_width,self.graphic1_height,self.diffs,i,createtime=createtime,m=self.master_diffpic[i].copy())
                self.diffgraphic[i].paste(self.diffpic[i])
            if self.infoframestatus == 6:
                self.infoframe_all_pic = self.create_image_from_arrays(self.graphic1_width,self.graphic1_height,self.brightness,self.diffs,createtime=createtime,m=self.master_infoframe_all_pic.copy())
                self.infoframe_all_graphic.paste(self.infoframe_all_pic)
        else:
            for i in range(len(self.timestamps)):
                self.master_brightnesspic[i] = self.create_image_from_array(self.graphic1_width,self.graphic1_height,self.brightness,i,createtime=createtime)
                self.brightnesspic[i] = self.master_brightnesspic[i]
                self.brightnessgraphic[i].paste(self.brightnesspic[i])
                self.master_diffpic[i] = self.create_image_from_array(self.graphic1_width,self.graphic1_height,self.diffs,i,createtime=createtime)
                self.diffpic[i] = self.master_diffpic[i]
                self.diffgraphic[i].paste(self.diffpic[i])
            if self.infoframestatus == 6:
                self.master_infoframe_all_pic = self.create_image_from_arrays(self.graphic1_width,self.graphic1_height,self.brightness,self.diffs,createtime=createtime)
                self.infoframe_all_pic = self.master_infoframe_all_pic
                self.infoframe_all_graphic.paste(self.infoframe_all_pic)

    def infoframecreatepicture(self):
        self.log.debug("infoframestatus = %d" % self.infoframestatus)
        if self.infoframestatus == 0:
            self.log.info("create infoframe...")
            self.infoframestatus = 1
            self.infoframe_i = self.timestamp_min
            self.infoframe_i_alt = self.timestamp_min
            self.infoframecreateupdateid = self.infoframe.after(1000,func=self.infoframecreatepicture)
        elif self.infoframestatus == 1:
            self.infoframeoutputstatus_var = tkinter.StringVar()
            self.infoframeoutputstatus = tkinter.Label(self.infoframe,textvariable=self.infoframeoutputstatus_var, height=1)
            self.infoframeoutputstatus.grid(column=0,row=0)
            if self.absolutscale != None:
                self.graphic_width = self.absolutscale
            else:
                self.graphic_width = 500
            self.graphic_height = 20
            self.graphic1_width = self.graphic_width
            self.graphic1_height = self.graphic_height
            if self.brightness == None:
                self.create_brightness_diffs = True
                self.brightness = []
                self.diffs = []
                for i in range(len(self.timestamps)):
                    self.brightness += [[]]
                    self.diffs += [[]]
            else:
                self.create_brightness_diffs = False
            self.infoframestatus = 2
            self.infoframecreateupdateid = self.infoframe.after("idle",func=self.infoframecreatepicture)
            #self.infoframecreateupdateid = self.infoframe.after(1,func=self.infoframecreatepicture)
        elif self.infoframestatus == 2:
            #self.infoframe_i_step = (self.timestamp_max-self.timestamp_min)/(3.0*self.graphic1_width)
            self.infoframe_i_step = (self.timestamp_max-self.timestamp_min)/(float(len(self.timestamps))*self.graphic1_width)
            if self.create_brightness_diffs:
                self.log.debug("infoframe_i_step = %f" % self.infoframe_i_step)
            self.brightnesspic = []
            self.master_brightnesspic = []
            self.brightnessgraphic = []
            self.infoframe_brightnessgraphic = []
            self.diffpic = []
            self.master_diffpic = []
            self.diffgraphic = []
            self.infoframe_diffgraphic = []
            for i in range(len(self.timestamps)):
                self.brightnesspic += [PIL.Image.new("L",(self.graphic1_width,self.graphic1_height),color=0)]
                self.master_brightnesspic += [PIL.Image.new("L",(self.graphic1_width,self.graphic1_height),color=0)]
                self.brightnessgraphic += [PIL.ImageTk.PhotoImage("L",(self.graphic1_width,self.graphic1_height))]
                self.brightnessgraphic[i].paste(self.brightnesspic[i])
                self.infoframe_brightnessgraphic += [tkinter.Label(self.infoframe,image=self.brightnessgraphic[i])]
                self.infoframe_brightnessgraphic[i].grid(column=i,row=1)
                self.diffpic += [PIL.Image.new("L",(self.graphic1_width,self.graphic1_height),color=0)]
                self.master_diffpic += [PIL.Image.new("L",(self.graphic1_width,self.graphic1_height),color=0)]
                self.diffgraphic += [PIL.ImageTk.PhotoImage("L",(self.graphic1_width,self.graphic1_height))]
                self.diffgraphic[i].paste(self.diffpic[i])
                self.infoframe_diffgraphic += [tkinter.Label(self.infoframe,image=self.diffgraphic[i])]
                self.infoframe_diffgraphic[i].grid(column=i,row=2)
            if self.create_brightness_diffs:
                self.infoframestatus = 3
            else:
                self.infoframestatus = 5
            self.infoframecreateupdateid = self.infoframe.after("idle",func=self.infoframecreatepicture)
            #self.infoframecreateupdateid = self.infoframe.after(1,func=self.infoframecreatepicture)
        elif self.infoframestatus == 3:
            self.infoframeoutputstatus_var.set("%f / %f" % (self.infoframe_i,self.timestamp_max))
            if self.infoframe_i < self.timestamp_max:
                for i in range(len(self.timestamps)):
                #for i in range(1):
                    [ok,ii,t] = self.outframes[i]['playgui'].ifromtime(i=0,t=self.infoframe_i)
                    if ok:
                        zips = zipfile.ZipFile(self.timestamps[i][ii][1],"r")
                        zipdata = io.StringIO(zips.read(self.timestamps[i][ii][2]))
                        pic1 = PIL.Image.open(zipdata)
                        pic1a = pic1.load()
                        zipdata.close()
                        if (ii+1 < self.outframes[i]['playgui'].n) and (self.timestamps[i][ii][1] == self.timestamps[i][ii+1][1]):
                            zipdata = io.StringIO(zips.read(self.timestamps[i][ii+1][2]))
                            pic2 = PIL.Image.open(zipdata)
                            pic2a = pic2.load()
                            zipdata.close()
                        else:
                            pic2 = None
                        # do something with this pic(s) #######################
                        [width,height] = pic1.size
                        hist = pic1.histogram()
                        b = 0
                        for j in range(len(hist)):
                            b = b + j*hist[j]
                        b = float(b) / (width*height)
                        self.brightness[i] += [[self.infoframe_i,b]]
                        if pic2 != None:
                            d = 0
                            out = PIL.ImageMath.eval("abs(a-b)", a=pic1, b=pic2)
                            h = out.histogram()
                            for j in range(len(h)):
                                d = d + j*h[j]
                            d = float(d) / (width*height)
                            self.diffs[i] += [[self.infoframe_i,d]]
                            self.log.debug("i=%d t=%f b=%f d=%f" % (i,self.infoframe_i,b,d))
                        else:
                            self.log.debug("i=%d t=%f b=%f" % (i,self.infoframe_i,b))
                if self.infoframe_i > self.infoframe_i_alt + 1*self.infoframe_i_step:
                    self.infoframe_i_alt = self.infoframe_i
                    # create picture
                    self.log.debug("create pictures")
                    for i in range(len(self.timestamps)):
                        self.brightnesspic[i] = self.create_image_from_array(self.graphic1_width,self.graphic1_height,self.brightness,i)
                        self.brightnessgraphic[i].paste(self.brightnesspic[i])
                        self.diffpic[i] = self.create_image_from_array(self.graphic1_width,self.graphic1_height,self.diffs,i)
                        self.diffgraphic[i].paste(self.diffpic[i])
                self.infoframe_i += self.infoframe_i_step
            else:
                self.infoframestatus = 4
            self.infoframecreateupdateid = self.infoframe.after("idle",func=self.infoframecreatepicture)
            #self.infoframecreateupdateid = self.infoframe.after(1,func=self.infoframecreatepicture)
        elif self.infoframestatus == 4:
            # save data
            if self.indexfile != None:
                self.log.debug("save data to \"%s\"" % self.indexfile)
                zip = zipfile.ZipFile(self.indexfile,"a",zipfile.ZIP_DEFLATED)
                # write brightness
                z = zipfile.ZipInfo()
                z.external_attr = 0o600 << 16
                z.compress_type = zipfile.ZIP_DEFLATED
                z.filename = self.brightnessfile
                z.date_time = time.localtime(time.time())[0:6]
                zip.writestr(z,pickle.dumps(self.brightness))
                # write diffs
                z = zipfile.ZipInfo()
                z.external_attr = 0o600 << 16
                z.compress_type = zipfile.ZIP_DEFLATED
                z.filename = self.diffsfile
                z.date_time = time.localtime(time.time())[0:6]
                zip.writestr(z,pickle.dumps(self.diffs))
                zip.close()
            self.infoframestatus = 5
            self.infoframecreateupdateid = self.infoframe.after("idle",func=self.infoframecreatepicture)
            #self.infoframecreateupdateid = self.infoframe.after(1,func=self.infoframecreatepicture)
        elif self.infoframestatus == 5:
            # create picture
            self.log.debug("create pictures")
            self.create_infoframe_pictures()
            self.infoframeoutputstatus.destroy()
            self.infoframe_all_pic = PIL.Image.new("RGB",(len(self.timestamps)*self.graphic1_width,self.graphic1_height),color=(0,0,0))
            self.infoframe_all_graphic = PIL.ImageTk.PhotoImage(self.infoframe_all_pic)
            self.infoframe_all_graphic_label = tkinter.Label(self.infoframe,image=self.infoframe_all_graphic)
            self.infoframe_all_graphic_label.grid(column=0,row=0,columnspan=3)
            self.infoframestatus = 6
            self.create_infoframe_pictures()
            self.infoframecreateupdateid = self.infoframe.after("idle",func=self.infoframecreatepicture)
            #self.infoframecreateupdateid = self.infoframe.after(1,func=self.infoframecreatepicture)
        else:
            self.log.info("infoframe created")
            self.infoframeready = True

    def gominus100s(self):
        self.gos(-100)
    def gominus10s(self):
        self.gos(-1)
    def gominus1s(self):
        self.gos(-0.01)
    def goplus100s(self):
        self.gos(100)
    def goplus10s(self):
        self.gos(1)
    def goplus1s(self):
        self.gos(0.01)
    def gos(self,step):
        self.mt.tunnel(step)
        for i in range(len(self.outframes)):
            self.outframes[i]['playgui'].gos()
        t = self.mt.gettime()
        self.time_val.set("(%s.%03d)" % (time.strftime("%Y-%m-%d, %H:%M:%S",time.localtime(t)),int(math.floor((t-math.floor(t))*1000))))
        if (self.create_info_graphics == 1) and (abs(t-self.infoframelastupdatetime) >= self.infoframe_i_step):
            self.infoframeupdateid = self.controlframe.after("idle",func=self.infoframeupdate)

    def gominus100(self):
        self.go(-100)
    def gominus10(self):
        self.go(-10)
    def gominus1(self):
        self.go(-1)
    def goplus1(self):
        self.go(+1)
    def goplus10(self):
        self.go(+10)
    def goplus100(self):
        self.go(+100)
    def go(self,step):
        for i in range(len(self.outframes)):
            self.outframes[i]['playgui'].go(step)

    def timeratehalf(self):
        self.timeratefactor = self.timeratefactor / 2.0
        self.settimeratefactor()
        self.timerate_var.set("timerate * %1.2f" % self.timeratefactor)
    def timeratedouble(self):
        self.timeratefactor = self.timeratefactor * 2.0
        self.settimeratefactor()
        self.timerate_var.set("timerate * %1.2f" % self.timeratefactor)
    def settimeratefactor(self):
        s = self.mt.getstatus()
        self.stop()
        self.mt.timeratefactor = self.timeratefactor
        for i in range(len(self.outframes)):
            self.outframes[i]['playgui'].timeratefactor = self.timeratefactor
        if s == "play":
            self.play()
        elif s == "yalp":
            self.yalp()

    def yalp(self):
        self.mt.setstatus("yalp")
        for i in range(len(self.outframes)):
            self.outframes[i]['frame'].after(1,func=self.outframes[i]['playgui'].play())
        self.updateid = self.controlframe.after(1,func=self.update)
    def play(self):
        self.mt.setstatus("play")
        for i in range(len(self.outframes)):
            self.outframes[i]['frame'].after(1,func=self.outframes[i]['playgui'].play())
        self.updateid = self.controlframe.after(1,func=self.update)

    def stop(self):
        self.mt.setstatus("stop")
        if self.updateid != None:
            self.controlframe.after_cancel(self.updateid)
            self.updateid = None
        for i in range(len(self.outframes)):
            self.outframes[i]['frame'].after(1,func=self.outframes[i]['playgui'].stop())

    def update(self):
        t = self.mt.gettime()
        self.time_val.set("(%s.%03d)" % (time.strftime("%Y-%m-%d, %H:%M:%S",time.localtime(t)),int(math.floor((t-math.floor(t))*1000))))
        if (t <= self.timestamp_min) or (self.timestamp_max <= t):
            self.stop()
        else:
            if (self.create_info_graphics == 1) and (abs(self.mt.gettime()-self.infoframelastupdatetime) >= self.infoframe_i_step):
                self.infoframeupdateid = self.controlframe.after("idle",func=self.infoframeupdate)
            self.updateid = self.controlframe.after(self.updateinterval,func=self.update)

    def infoframeupdate(self):
        if self.infoframeupdateid != None:
            self.controlframe.after_cancel(self.infoframeupdateid)
        if self.infoframeready:
            self.log.debug("time line in info frame")
            self.create_infoframe_pictures(createtime=True)

    def destroy(self):
        self.log.debug("destroy class gui")
        try: self.controlframe.after_cancel(self.updateid)
        except: pass
        try: self.controlframe.after_cancel(self.infoframeupdateid)
        except: pass
        for i in range(len(self.outframes)):
            self.outframes[i]['playgui'].destroy()

    def __del__(self):
        self.log.debug("del class gui")
        self.destroy()
