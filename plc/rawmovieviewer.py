#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2012-09-11, 2012-09-17, 2012-09-19, 2012-09-20, 2013-01-26, 2013-02-04, 2013-04-09, 2013-04-18, 2014-07-22, 2017-05-30

__rawmoviewviewer_date__ = "2017-05-30"
__rawmoviewviewer_version__ = __rawmoviewviewer_date__


import argparse
import PIL.Image
import PIL.ImageTk
import logging
import logging.handlers
import math
import os
import re
#import string
import tkinter
import time

class play_gui():
    def __init__(self,log,f,pics,n,timeratefactor=1.0,scale = 1.0,istep=+1,pausebetweenrecordings=1):
        self.f = f
        self.pics = pics
        self.width = pics[0]["width"]
        self.height = pics[0]["height"]
        self.swidth = int(scale*self.width)
        self.sheight = int(scale*self.height)
        self.depth = pics[0]["depth"]
        self.maxval = pics[0]["maxval"]
        self.picturesize = self.width*self.height*self.depth
        self.n = n
        self.timeratefactor = timeratefactor
        self.scale = scale
        self.pausebetweenrecordings = bool(pausebetweenrecordings)
        self.i = 0
        self.log = log
        self.log.debug("start play_gui")
        self.main_window = tkinter.Tk()
        self.main_window.title("rawmoviewviewer: %s (%dx%d -> %dx%d)" % (self.f,self.width,self.height,self.swidth,self.sheight))
        self.padx = 3
        self.pady = 3
        self.repeatdelay = 500
        self.repeatinterval = 10
        # buttons
        self.frame1 = tkinter.Frame(self.main_window)
        self.frame1.pack(expand=True,fill=tkinter.X)
        self.minus100button = tkinter.Button(self.frame1,text="-100",command=self.gominus100,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.minus100button.pack(side=tkinter.LEFT)
        self.minus10button = tkinter.Button(self.frame1,text="-10",command=self.gominus10,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.minus10button.pack(side=tkinter.LEFT)
        self.minus1button = tkinter.Button(self.frame1,text="-1",command=self.gominus1,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.minus1button.pack(side=tkinter.LEFT)
        self.yalpbutton = tkinter.Button(self.frame1,text="yalp",command=self.yalp,padx=self.padx,pady=self.pady)
        self.yalpbutton.pack(side=tkinter.LEFT)
        self.stopbutton = tkinter.Button(self.frame1,text="stop",command=self.stop,padx=self.padx,pady=self.pady)
        self.stopbutton.pack(side=tkinter.LEFT)
        self.playbutton = tkinter.Button(self.frame1,text="play",command=self.play,padx=self.padx,pady=self.pady)
        self.playbutton.pack(side=tkinter.LEFT)
        self.plus1button = tkinter.Button(self.frame1,text="+1",command=self.goplus1,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.plus1button.pack(side=tkinter.LEFT)
        self.plus10button = tkinter.Button(self.frame1,text="+10",command=self.goplus10,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.plus10button.pack(side=tkinter.LEFT)
        self.plus100button = tkinter.Button(self.frame1,text="+100",command=self.goplus100,padx=self.padx,pady=self.pady,repeatdelay=self.repeatdelay, repeatinterval=self.repeatinterval)
        self.plus100button.pack(side=tkinter.LEFT)
        # space
        #self.label1 = Tkinter.Label(self.frame1,height=1,width=10)
        #self.label1.pack(side=Tkinter.LEFT)
        # scale
        self.label2_var = tkinter.StringVar()
        self.label2 = tkinter.Label(self.frame1,textvariable=self.label2_var, width=11,height=1)
        self.label2.pack(side=tkinter.LEFT)
        self.label2_var.set("scale %2.2f" % self.scale)
        self.scalehalfbutton = tkinter.Button(self.frame1,text="*0.5",command=self.scalehalf,padx=self.padx,pady=self.pady)
        self.scalehalfbutton.pack(side=tkinter.LEFT)
        self.scaledoublebutton = tkinter.Button(self.frame1,text="*2",command=self.scaledouble,padx=self.padx,pady=self.pady)
        self.scaledoublebutton.pack(side=tkinter.LEFT)
        self.scaleminusbutton = tkinter.Button(self.frame1,text="-0.1",command=self.scaleminus,padx=self.padx,pady=self.pady)
        self.scaleminusbutton.pack(side=tkinter.LEFT)
        self.scaleplusbutton = tkinter.Button(self.frame1,text="+0.1",command=self.scaleplus,padx=self.padx,pady=self.pady)
        self.scaleplusbutton.pack(side=tkinter.LEFT)
        # timerate
        self.timerate_var = tkinter.StringVar()
        self.timerate_label = tkinter.Label(self.frame1,textvariable=self.timerate_var, width=16,height=1)
        self.timerate_label.pack(side=tkinter.LEFT)
        self.timerate_var.set("timerate * %1.2f" % self.timeratefactor)
        self.timeratehalfbutton = tkinter.Button(self.frame1,text="*0.5",command=self.timeratehalf,padx=self.padx,pady=self.pady)
        self.timeratehalfbutton.pack(side=tkinter.LEFT)
        self.timeratedoublebutton = tkinter.Button(self.frame1,text="*2",command=self.timeratedouble,padx=self.padx,pady=self.pady)
        self.timeratedoublebutton.pack(side=tkinter.LEFT)
        # every frame
        self.istep = istep
        self.everyframe_var = tkinter.StringVar()
        self.everyframe_label = tkinter.Label(self.frame1,textvariable=self.everyframe_var, width=16,height=1)
        self.everyframe_label.pack(side=tkinter.LEFT)
        self.everyframe_var.set("every %d frame" % self.istep)
        self.everyframehalfbutton = tkinter.Button(self.frame1,text="*0.5",command=self.everyframehalf,padx=self.padx,pady=self.pady)
        self.everyframehalfbutton.pack(side=tkinter.LEFT)
        self.everyframedoublebutton = tkinter.Button(self.frame1,text="*2",command=self.everyframedouble,padx=self.padx,pady=self.pady)
        self.everyframedoublebutton.pack(side=tkinter.LEFT)
        # frame number
        self.status_val = tkinter.StringVar()
        self.status_label = tkinter.Label(self.frame1,textvariable=self.status_val,height=1,width=10)
        self.status_label.pack(side=tkinter.RIGHT)
        self.time_val = tkinter.StringVar()
        self.time_label = tkinter.Label(self.frame1,textvariable=self.time_val,height=1,width=26)
        self.time_label.pack(side=tkinter.RIGHT)
        # movie frame
        self.picture = None
        self.img = PIL.ImageTk.PhotoImage("L",(self.swidth,self.sheight))
        self.pic = PIL.Image.new("L",(self.swidth,self.sheight))
        self.img.paste(self.pic)
        self.frame2 = tkinter.Frame(self.main_window)
        self.frame2.pack()
        self.movie_label = tkinter.Label(self.frame2, image=self.img)
        self.movie_label.pack()
        # other variables
        self.updateinterval = 1
        self.updateid = None
        self.time = dict()
        self.time['last displayed timestamp'] = None
        self.time['last displayed real'] = 0
        self.time['buffer timestamp'] = None
        self.picture_in_buffer = False

    def open(self):
        self.fd = open(self.f,'rb')

    def close(self):
        self.fd.close()

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
        self.i = max(0,min(self.i+step,self.n-1))
        self.readimage()
        self.displayimage()
    def scalehalf(self):
        self.scale = self.scale / 2.0
        self.changescale()
    def scaledouble(self):
        self.scale = self.scale * 2.0
        self.changescale()
    def scaleminus(self):
        self.scale = self.scale - 0.1
        self.changescale()
    def scaleplus(self):
        self.scale = self.scale + 0.1
        self.changescale()
    def changescale(self):
        self.label2_var.set("scale %2.2f" % self.scale)
        self.swidth = int(self.scale*self.width)
        self.sheight = int(self.scale*self.height)
        self.main_window.title("rawmoviewviewer: %s (%dx%d -> %dx%d)" % (self.f,self.width,self.height,self.swidth,self.sheight))
        self.movie_label.destroy()
        self.img = PIL.ImageTk.PhotoImage("L",(self.swidth,self.sheight))
        self.movie_label = tkinter.Label(self.frame2, image=self.img)
        self.movie_label.pack()
        if self.picture != None:
            self.onlydisplayimage()

    def timeratehalf(self):
        self.timeratefactor = self.timeratefactor / 2.0
        self.timerate_var.set("timerate * %1.2f" % self.timeratefactor)
    def timeratedouble(self):
        self.timeratefactor = self.timeratefactor * 2.0
        self.timerate_var.set("timerate * %1.2f" % self.timeratefactor)

    def everyframehalf(self):
        self.istep = int(max(1,self.istep / 2))
        self.everyframe_var.set("every %d frame" % self.istep)
    def everyframedouble(self):
        self.istep = int(max(1,self.istep * 2))
        self.everyframe_var.set("every %d frame" % self.istep)

    def readimage(self):
        self.fd.seek(self.pics[self.i]["fileposition"])
        self.time['buffer timestamp'] = self.pics[self.i]["timestamp"]
        self.picture = self.fd.read(self.pics[self.i]["picturesize"])

    def onlydisplayimage(self):
        self.pic = PIL.Image.frombuffer("L",(self.width,self.height),self.picture,'raw',"L",0,1)
        if self.height != self.sheight:
            self.pic = self.pic.resize((self.swidth,self.sheight))
        self.img.paste(self.pic)

    def displayimage(self):
        self.onlydisplayimage()
        self.status_val.set("%d of %d" % (self.i+1,self.n))
        self.time_val.set("(%s.%03d)" % (time.strftime("%Y-%m-%d, %H:%M:%S",time.localtime(self.time['buffer timestamp'])),int(math.floor((self.time['buffer timestamp']-math.floor(self.time['buffer timestamp']))*1000))))
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
        return self.time['buffer timestamp'] - self.time['last displayed timestamp']

    def play(self):
        if (0 <= self.i) and (self.i < self.n):
            self.log.debug("play")
            if self.updateid != None:
                self.playbutton.after_cancel(self.updateid)
            if not self.picture_in_buffer:
                self.readimage()
                self.picture_in_buffer = True
            d = True
            if self.timestamps_available():
                d = False
                self.log.debug("%f >= %f ??" % (self.delta_time_last_displayed(),self.delta_timestamp_last_displayed()))
                if self.delta_time_last_displayed() >= self.delta_timestamp_last_displayed():
                    d = True
                    self.updateinterval = max(1,min(10,int(round(1000*self.delta_timestamp_last_displayed()/2.0/self.timeratefactor))))
                else:
                    self.updateinterval = max(1,min(10,int(round(1000*(self.delta_timestamp_last_displayed() - self.delta_time_last_displayed())/self.timeratefactor))))
                self.log.debug("update: %d" % self.updateinterval)
                if (self.pausebetweenrecordings and
                    (abs(self.delta_timestamp_last_displayed()) > 1*max(1,self.timeratefactor))):
                    self.log.debug("next record set start in 3 seconds")
                    self.updateinterval = 3000
                    self.pic = PIL.Image.new("L",(self.swidth,self.sheight),color=255)
                    self.img.paste(self.pic)
                    self.time['last displayed real'] = time.time()
                    self.time['last displayed timestamp'] = self.time['buffer timestamp']
                elif ((not self.pausebetweenrecordings) and
                    (abs(self.delta_timestamp_last_displayed()) > 1*max(1,self.timeratefactor))):
                    d = True
                    self.updateinterval = max(1,min(10,int(round(1000*self.delta_timestamp_last_displayed()/2.0/self.timeratefactor))))
            if d:
                self.i = self.i+self.istep
                self.displayimage()
                self.picture_in_buffer = False
            self.updateid = self.playbutton.after(self.updateinterval,func=self.play)
        else:
            self.i = self.n-1
            self.displayimage()
            self.stop()

    def yalp(self):
        if (0 <= self.i) and (self.i < self.n):
            self.log.debug("yalp")
            if self.updateid != None:
                self.playbutton.after_cancel(self.updateid)
            if not self.picture_in_buffer:
                self.readimage()
                self.picture_in_buffer = True
            d = True
            if self.timestamps_available():
                d = False
                self.log.debug("%f >= %f ??" % (self.delta_time_last_displayed(),abs(self.delta_timestamp_last_displayed())))
                if self.delta_time_last_displayed() >= abs(self.delta_timestamp_last_displayed()):
                    d = True
                    self.updateinterval = max(1,min(10,int(round(1000*abs(self.delta_timestamp_last_displayed())/2.0/self.timeratefactor))))
                else:
                    self.updateinterval = max(1,min(10,int(round(1000*(abs(self.delta_timestamp_last_displayed()) - self.delta_time_last_displayed())/self.timeratefactor))))
                self.log.debug("update: %d" % self.updateinterval)
                if (self.pausebetweenrecordings and
                    (abs(self.delta_timestamp_last_displayed()) > 1*max(1,self.timeratefactor))):
                    self.log.debug("next record set start in 3 seconds")
                    self.updateinterval = 3000
                    self.pic = PIL.Image.new("L",(self.swidth,self.sheight),color=255)
                    self.img.paste(self.pic)
                    self.time['last displayed real'] = time.time()
                    self.time['last displayed timestamp'] = self.time['buffer timestamp']
                elif ((not self.pausebetweenrecordings) and
                    (abs(self.delta_timestamp_last_displayed()) > 1*max(1,self.timeratefactor))):
                    d = True
                    self.updateinterval = max(1,min(10,int(round(1000*abs(self.delta_timestamp_last_displayed())/2.0/self.timeratefactor))))
            if d:
                self.i = self.i-self.istep
                self.displayimage()
                self.picture_in_buffer = False
            self.updateid = self.playbutton.after(self.updateinterval,func=self.yalp)
        else:
            self.i = 0
            self.displayimage()
            self.stop()

    def stop(self):
        self.log.debug("stop")
        if self.updateid != None:
            self.playbutton.after_cancel(self.updateid)

def readimage(log,fd,readimagebytes=True):
    pic = {"headerlength": 0,
           "timestamp": None,
           "width": None,
           "height": None,
           "depth": None,
           "maxval": None,
           "cam": None,
           "mode": None,
           "features": None,
           "picture": None,
           "picturesize": None}
    magic = fd.read(2)
    pic["headerlength"] += 2
    if magic == "P7":
        log.debug("OK, right format")
        t = fd.readline().strip() # first line with magic
        pic["headerlength"] += len(t)+1
        while (t != "ENDHDR"):
            t = fd.readline().strip()
            pic["headerlength"] += len(t)+1
            #log.debug("L: %s" % t)
            nothing = True
            if nothing:
                r = re.findall("DEPTH ([0-9]+)",t)
                if r:
                    pic["depth"] = int(r[0])
                    log.debug("depth: %d" % pic["depth"])
                    nothing = False
            if nothing:
                r = re.findall("MAXVAL ([0-9]+)",t)
                if r:
                    pic["maxval"] = int(r[0])
                    log.debug("maxval: %d" % pic["maxval"])
                    nothing = False
            if nothing:
                r = re.findall("CAM: (.+)",t)
                if r:
                    pic["cam"] = r[0]
                    log.debug("cam: %s" % pic["cam"])
                    nothing = False
            if nothing:
                r = re.findall("MODE: (.+)",t)
                if r:
                    pic["mode"] = r[0]
                    log.debug("mode: %s" % pic["mode"])
                    nothing = False
            if nothing:
                r = re.findall("FEATURES: (\{.+\})",t)
                if r:
                    pic["features"] = r[0]
                    log.debug("features: %s" % pic["features"])
                    nothing = False
            if nothing:
                r = re.findall("HEIGHT ([0-9]+)",t)
                if r:
                    pic["height"] = int(r[0])
                    log.debug("height: %d" % pic["height"])
                    nothing = False
            if nothing:
                r = re.findall("WIDTH ([0-9]+)",t)
                if r:
                    pic["width"] = int(r[0])
                    log.debug("width: %d" % pic["width"])
                    nothing = False
            if nothing:
                r = re.findall("#TIME: ([0-9\.]+)",t)
                if r:
                    pic["timestamp"] = float(r[0])
                    log.debug("timestamp: %f" % pic["timestamp"])
                    nothing = False
        if ((pic["width"] != None) and (pic["height"] != None) and
            (pic["depth"] != None) and (pic["maxval"] != None)):
            pic["picturesize"] = pic["width"]*pic["height"]*pic["depth"]
            pic["fileposition"] = fd.tell()
            if readimagebytes:
                pic["picture"] = fd.read(pic["picturesize"])
            else:
                pic["picture"] = ""
                fd.seek(pic["fileposition"]+pic["picturesize"])
            log.debug("read picture of %d bytes" % (pic["picturesize"]))
            p = True
    return pic

def readimages(f,log):
    pics = []
    fd = open(f,'rb')
    readimagebytes = False
    pic = readimage(log,fd,readimagebytes)
    if pic["picture"] != None:
        p = True
        pics += [pic]
    while pic["picture"] != None:
        pic = readimage(log,fd,readimagebytes)
        if pic["picture"] != None:
            p = True
            pics += [pic]
    fd.close()
    return [p,pics]

def main():
    # command line parameter
    parser = argparse.ArgumentParser(
        description='RawmoviewViewer',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\nExamples:\n  rawmovieviewer.py -f movie1.img movie2.img movie3.img\n  rawmovieviewer.py -f movie.img -d 1 -t 0.01 -s 2\n  rawmovieviewer.py -f movie.img -i 10 -t 10" % __rawmoviewviewer_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-f',
                        nargs="+",
                        type=str,
                        required=True,
                        dest='file',
                        help='will play this file(s)',
                        metavar='file')
    parser.add_argument('-scale',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='scale',
                        help='Set the scale factor x. default: x = 1.0',
                        metavar='x')
    parser.add_argument('-timeratefactor',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='timeratefactor',
                        help='Set the time rate factor x. default: x = 1.0',
                        metavar='x')
    parser.add_argument('-istep',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='istep',
                        help='Only every ith frame will be shown. default: i = 1',
                        metavar='i')
    parser.add_argument('-pausebetweenrecordings',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='pausebetweenrecordings',
                        help='If set to 1 a pause between 2 recording sets is added. default: b = 1',
                        metavar='b')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    args = parser.parse_args()
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.timeratefactor,float):
        args.timeratefactor = args.timeratefactor[0]
    if not isinstance(args.scale,float):
        args.scale = args.scale[0]
    if not isinstance(args.istep,int):
        args.istep = args.istep[0]
    if not isinstance(args.pausebetweenrecordings,int):
        args.pausebetweenrecordings = args.pausebetweenrecordings[0]
    # logging
    log = logging.getLogger('rawmovieviewer')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.WARNING) # logging.WARNING = 30
    ch.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(ch)
    log.info("start logging in rawmovieviewer: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.debug("scale to %f" % args.scale)
    # gui
    for f in args.file:
        log.debug("file: %s" % f)
        if os.path.isfile(f):
            [p,pics] = readimages(f,log)
            n = len(pics)
            log.debug("found %d pictures in %s" % (n,f))
            if p:
                g = play_gui(log,f,pics,n,timeratefactor=args.timeratefactor,scale=args.scale,istep=args.istep,pausebetweenrecordings=args.pausebetweenrecordings)
                log.debug("start mainloop")
                g.open()
                g.main_window.mainloop()
                g.close()


if __name__ == "__main__":
    main()
