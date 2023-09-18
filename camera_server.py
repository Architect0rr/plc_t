#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-10-29, 2014-07-22, 2017-05-30

__camera_server_date__ = "2017-05-30"
__camera_server_version__ = __camera_server_date__

import argparse
import csv
import errno
import PIL.Image
import logging
import logging.handlers
import os
import queue
import re
import signal
import socket
import socketserver
import sys
import tempfile
import threading
import time
import types

import pydc1394

from plc_tools.plclogclasses import QueuedWatchedFileHandler
import plc_tools.plc_socket_communication

#import ctypes
#import ctypes.util
#
#ctypes.util.find_library("dc1394")
#libdc1394=ctypes.CDLL('libdc1394.so.22')
#
#libdc1394=ctypes.CDLL(ctypes.util.find_library("dc1394"))
#d=libdc1394.dc1394_new()
#
# https://launchpad.net/pydc1394
# http://www.rzuser.uni-heidelberg.de/~ge6/Programing/dc1394python.html
# http://bazaar.launchpad.net/~sirver/pydc1394/trunk/view/head:/pydc1394/_dc1394core.py
# http://bazaar.launchpad.net/~sirver/pydc1394/trunk/files/head:/pydc1394/

class controller_class():
    """controller_class
    
    This class is for communicating to a device. This means
    setvalues are required by the user and will be set in some
    intervals. The actualvalues are the actualvalues which were
    set before.
    
    Author: Daniel Mohr
    Date: 2012-09-30
    """
    def __init__(self,log=None,guid=None,mode=None,color_coding=None,framerate=None,ringbuf=16,recvbuf=4096):
        if guid == "":
            guid = None
        if mode == "":
            mode = None
        if color_coding == "":
            color_coding = None
        if framerate == "":
            framerate = None
        self.libdc1394 = pydc1394.DC1394Library()
        self.log = log
        self.running = True
        self.cam = None
        self.caminit = False
        #self.bufsize = 4
        #self.bufsize = 16
        self.bufsize = ringbuf
        self.bufheader = self.bufsize * [None]
        self.recvbuf = recvbuf
        self.cd = None
        self.camname = None
        self.values = {'guid': None, 'isospeed': None, 'mode': None, 'image_size': None, 'image_position': None, 'color_coding': None, 'packet_size': None, 'framerate': None, 'feature_settings': None, 'bufsize': self.bufsize}
        self.patheslock = threading.Lock()
        self.pathes = None
        self.pathes_index = 0
        self.fdlock = threading.Lock()
        self.fd = None
        self.filename_i = 0
        self.filename = None
        self.maxfilesize = 1e9
        self.filesuffixformat = "%05d.img"
        if guid != None:
            self.values['guid'] = guid
        if mode != None:
            self.values['mode'] = mode
        if color_coding != None:
            self.values['color_coding'] = color_coding
        if framerate != None:
            self.values['framerate'] = framerate
        self.valueslock = threading.Lock()
        self.camlock = threading.Lock()
        self.grabbing_running = False
        self.recording_thread_function_running = False
        self.grabbinglock = threading.Lock()
        self.recording_thread_function_lock = threading.Lock()
        self.recording = False
        self.recording1frame = False
        # init camera
        self.initcam() # try to init cam

    def initcam(self,dovalueslock=True):
        wasrunning = False
        if dovalueslock:
            self.valueslock.acquire() # lock for running
        if ((self.values['guid'] != None) and
            (self.values['mode'] != None) and
            (self.values['framerate'] != None)):
            self.camlock.acquire() # lock for running
            if self.caminit:
                wasrunning = self.cam.running
                try:
                    self.cam.stop()
                    time.sleep(0.003) # wait 3 millisecond
                except:
                    self.log.warning("cannot stop camera")
            else:
                # init camera
                self.log.debug("init cam with guid %x" % self.values['guid'])
                self.cam =  pydc1394.Camera(self.libdc1394,self.values['guid'])
                self.caminit = True
            if int(self.cam.guid,16) != int(self.values['guid']):
                self.log.debug("change cam")
                self.log.debug("init cam with guid %x" % self.values['guid'])
                self.cam =  pydc1394.Camera(self.libdc1394,self.values['guid'])
                self.caminit = True
                self.values['isospeed'] = None
            if self.values['isospeed'] == None:
                v = 800
            else:
                v = self.values['isospeed']
            self.values['isospeed'] = self.cam.isospeed
            self.camname = "%s %s" % (self.cam.vendor,self.cam.model)
            try:
                self.cam.isospeed = v
                if self.values['isospeed'] != self.cam.isospeed:
                    self.log.debug("switch isospeed to %d" % self.cam.isospeed)
            except:
                self.log.warning("cannot set isospeed to camera")
            self.values['isospeed'] = self.cam.isospeed
            try:
                if self.values['extern_trigger']:
                    #print "self.cam.__getattribute__('trigger').pos_polarities",self.cam.__getattribute__('trigger').pos_polarities()
                    #print "self.cam.__getattribute__('trigger').polarity",self.cam.__getattribute__('trigger').polarity
                    self.cam.__getattribute__('trigger').polarity = 'TRIGGER_ACTIVE_HIGH' # ['TRIGGER_ACTIVE_LOW', 'TRIGGER_ACTIVE_HIGH']
                    self.log.debug("set extern trigger polarity to TRIGGER_ACTIVE_HIGH")
                    # it was necessary to change the source code of pydc1394 in _dc1394core.py
                    # comment out lines 413-416 and comment lines 417-420
                    self.cam.__getattribute__('trigger').on = True
                    self.log.debug("set extern trigger to on")
                else:
                    self.cam.__getattribute__('trigger').on = False
                    self.log.debug("set extern trigger to off")
            except:
                pass
            m, = [m for m in self.cam.modes if m.name == self.values['mode']]
            self.cam.mode = m
            self.cd = 1
            if self.cam.mode.name[len(self.cam.mode.name)-2:len(self.cam.mode.name)] == 'Y8':
                self.cd = 1
            elif self.cam.mode.name[len(self.cam.mode.name)-2:len(self.cam.mode.name)] == 'Y16':
                self.cd = 2
            if self.cam.mode.name[0:6] == "FORMAT":
                self.log.debug("set FORMAT")
                if self.values['image_size'] == None:
                    self.values['image_size'] = self.cam.mode.max_image_size
                if self.values['image_position'] == None:
                    self.values['image_position'] = self.cam.mode.image_position
                if self.values['color_coding'] == None:
                    self.values['color_coding'] = self.cam.mode.color_coding
                #if self.values['packet_size'] == None:
                self.cd = 1
                if self.values['color_coding'] == 'Y8':
                    self.cd = 1
                elif self.values['color_coding'] == 'Y16':
                    self.cd = 2
                # The packet size must always be evenly divisible by four.
                # http://www.alliedvisiontec.com/de/support/knowledge-base.html?tx_nawavtknowledgebase_piList[uid]=58&tx_nawavtknowledgebase_piList[mode]=single
                minpacketsize = 68
                maxpacketsize = 4092 # normally 4095; but 4095%4=3
                if self.cam.isospeed == 800:
                    maxpacketsize = 8188 # normally 8191; but 8191%4=3
                #self.values['image_position'] = (500,500)
                #self.values['image_size'] = (1032-500,778-500)
                #print "self.values['image_size'][0]",self.values['image_size'][0]
                #print "image_position",self.values['image_position']
                #print "image_size",self.values['image_size']
                x = self.values['image_size'][0]
                y = self.values['image_size'][1]
                self.values['packet_size'] = max(minpacketsize,
                                                 min(
                                                     int(self.values['framerate'] * x * y * self.cd / 8000),
                                                     maxpacketsize)
                                                 )
                if self.values['packet_size']%4 != 0:
                    self.values['packet_size'] = max(minpacketsize,
                                                     min(self.values['packet_size'] + 4 - self.values['packet_size']%4,
                                                         maxpacketsize)
                                                     )
                self.log.debug('set packet_size = %d' % self.values['packet_size'])
                self.values['framerate'] = round(8000.0 * self.values['packet_size'] /
                                                 (x * y * self.cd),2)
                self.cam.mode.setup(image_size=self.values['image_size'],
                                    image_position=self.values['image_position'],
                                    color_coding=self.values['color_coding'],
                                    packet_size=self.values['packet_size'])
            if self.values['feature_settings'] == None:
                # feature_settings
                self.values['feature_settings'] = dict()
                self.values['feature_settings']['val'] = dict()
                self.values['feature_settings']['mode'] = dict()
                self.values['feature_settings']['modes'] = dict()
                for f in self.cam.features:
                    self.values['feature_settings']['val'][f] = self.cam.__getattribute__(f).val
                    self.values['feature_settings']['mode'][f] = self.cam.__getattribute__(f).mode
                    self.values['feature_settings']['modes'] = self.cam.__getattribute__(f).pos_modes
            else:
                # set features
                possible_features = self.cam.features
                for f in self.values['feature_settings']['val']:
                    if f in possible_features:
                        self.cam.__getattribute__(f).val = self.values['feature_settings']['val'][f]
                        self.cam.__getattribute__(f).mode = self.values['feature_settings']['mode'][f]
                    else:
                        del self.values['feature_settings']['val'][f]
            if wasrunning:
                self.startcam_direct()
            self.camlock.release() # release the lock
        if dovalueslock:
            self.valueslock.release() # release the lock

    def setvalues(self,v):
        self.valueslock.acquire() # lock for running
        #time.sleep(1e-3) # wait for 10 milliseconds
        for f in v:
            self.values[f] = v[f]
        # set features
        self.initcam(dovalueslock=False)
        self.valueslock.release() # release the lock

    def getvalues(self):
        self.valueslock.acquire() # lock for running
        self.camlock.acquire() # lock for running
        if self.caminit:
            possible_features = self.cam.features
            for f in self.values['feature_settings']['val']:
                if f in possible_features:
                    self.values['feature_settings']['val'][f] = self.cam.__getattribute__(f).val
        else:
            self.log.debug("camera not initialized; cannot get values from camera")
        self.camlock.release() # release the lock
        s = self.values
        self.valueslock.release() # release the lock
        return s

    def setpathes(self,v):
        self.patheslock.acquire() # lock for running
        self.log.debug("set pathes to %s" % v)
        self.fdlock.acquire() # lock
        self.pathes = v
        if self.fd != None:
            self.fd.flush()
            self.fd.close()
            self.fd = None
        self.fdlock.release() # release the lock
        self.patheslock.release() # release the lock

    def startcam(self):
        if self.caminit:
            if self.cam.running:
                #self.log.debug("cam is already running")
                pass
            else:
                self.camlock.acquire() # lock for running
                self.grabbing_thread = threading.Thread(target=self.grabbing)
                self.grabbing_thread.daemon = True # exit thread when the main thread terminates
                self.grabbing_thread.name = "grabbing"
                self.recording_thread = threading.Thread(target=self.recording_thread_function)
                self.recording_thread.daemon = True # exit thread when the main thread terminates
                self.recording_thread.name = "recording"
                self.recording_maxqueue = 1000
                self.recording_queue = queue.Queue(maxsize=2*self.recording_maxqueue)
                self.startcam_direct(startthreads=False)
                self.log.debug("cam started")
                self.grabbing_thread.start()
                self.recording_thread.start()
                self.camlock.release() # release the lock
        else:
            self.log.debug("camera not initialized; cannot start camera")

    def startcam_direct(self,startthreads=True):
        if 'bufsize' in self.values:
            self.bufsize = self.values['bufsize']
        self.cam.start(bufsize=self.bufsize,interactive=False)
        if startthreads:
            if not self.grabbing_running:
                self.grabbing_thread = threading.Thread(target=self.grabbing)
                self.grabbing_thread.daemon = True # exit thread when the main thread terminates
                self.grabbing_thread.name = "grabbing"
                self.grabbing_thread.start()
            if not self.recording_thread_function_running:
                self.recording_thread = threading.Thread(target=self.recording_thread_function)
                self.recording_thread.daemon = True # exit thread when the main thread terminates
                self.recording_thread.name = "recording"
                self.recording_maxqueue = 1000
                self.recording_queue = queue.Queue(maxsize=2*self.recording_maxqueue)
                self.recording_thread.start()

    def rec1frame(self):
        if self.caminit and (not self.recording):
            self.log.debug("start recording for 1 frame")
            self.recording1frame = True
            if not self.cam.running:
                self.startcam()
        else:
            self.log.debug("camera not initialized; cannot start recording for 1 frame")

    def startrec(self):
        if self.caminit and (not self.recording):
            self.log.debug("start recording")
            self.recording = True
            if not self.cam.running:
                self.startcam()
        else:
            self.log.debug("camera not initialized; cannot start recording")

    def grabbing(self):
        if self.caminit == None:
            return
        self.grabbinglock.acquire() # lock for running
        it = 0
        itint1 = 3
        itint2 = 10
        itint3 = itint1*itint2
        t0 = time.time()
        isospeed = 0
        features = []
        self.valueslock.acquire() # lock for running
        if 'isospeed' in self.values:
            isospeed = self.values['isospeed']
        if 'feature_settings' in self.values:
            features = self.values['feature_settings']
        self.valueslock.release() # release the lock
        self.grabbing_running = True
        while self.cam.running and self.running:
            #self.log.debug("grabbing")
            self.valueslock.acquire() # lock for running
            self.camlock.acquire() # lock for running
            if it%itint1 == 0:
                possible_features = self.cam.features
                if 'isospeed' in self.values:
                    isospeed = self.values['isospeed']
                if 'feature_settings' in self.values:
                    features = self.values['feature_settings']
                isospeed = self.cam.isospeed
                for f in features['val']:
                    if f in possible_features:
                        features['val'][f] = self.cam.__getattribute__(f).val
                        features['mode'][f] = self.cam.__getattribute__(f).mode
            else:
                for f in features['val']:
                    if ((features['mode'][f] == 'auto') and
                        (f in possible_features)):
                        features['val'][f] = self.cam.__getattribute__(f).val
            header = "P7\n"
            header += "DEPTH %d\n" % self.cd
            header += "MAXVAL %d\n" % (2**(8*self.cd)-1)
            header += "TUPLTYPE DATA\n"
            header += "#GUID: %x\n" % int(self.cam.guid,16)
            header += "#CAM: %s\n" % self.camname
            header += "#MODE: %s\n" % self.cam.mode.name
            header += "#FRAMERATE: %f\n" % self.values['framerate']
            header += "#ISOSPEED: %d\n" % isospeed
            header += "#FEATURES: %s\n" % features
            header += "#IMAGE_SIZE: %d %d\n" % (self.values['image_size'][0],self.values['image_size'][1])
            header += "#IMAGE_POSITION: %d %d\n" % (self.values['image_position'][0],self.values['image_position'][1])
            header += "#PACKET_SIZE: %d\n" % self.values['packet_size']
            got_frame = False
            if self.cam.running:
                frame = self.cam.shot() # waiting for the next frame
                if frame != None:
                    got_frame = True
            self.camlock.release() # release the lock
            self.valueslock.release() # release the lock
            if got_frame:
                header += "HEIGHT %d\nWIDTH %d\n" % frame.shape
                header += "#TIME: %f\n" % (frame.timestamp/1e6)
                header += "ENDHDR\n"
                #self.log.debug("grabbing %d" % frame.id)
                self.bufheader[frame.id] = header
                if (self.recording or self.recording1frame) and self.pathes != None:
                    # write to file
                    try:
                        self.recording_queue.put_nowait([header,frame])
                    except:
                        self.log.warning("recording queue runs over; will stop recording")
                        self.stoprec()
                    if self.recording1frame:
                        self.recording1frame = False
                it += 1
                if it == itint3:
                    it = 0
                if it%itint2 == 0:
                    t1 = time.time()
                    s = ""
                    if self.recording and self.pathes != None:
                        s = " rec"
                    self.log.debug("get %d frames in %f sec (framerate: %f)%s" % (itint2,(t1-t0),itint2/(t1-t0),s))
                    t0 = time.time()
            else:
                self.log.debug("cannot get frame; possibly will try it again later")
                time.sleep(0.001) # wait 1 millisecond
        self.grabbing_running = False
        self.grabbinglock.release() # release the lock

    def recording_thread_function(self):
        self.valueslock.acquire() # lock for running
        default_sleep = 0.9*min(1.0/self.values['framerate'],1.0)
        self.valueslock.release() # release the lock
        self.recording_thread_function_lock.acquire() # lock for running
        self.recording_thread_function_running = True
        while self.cam.running and self.running:
            do = True
            did = False
            while do:
                do = False
                try:
                    [header,frame] = self.recording_queue.get_nowait()
                    do = True
                except: pass
                if do:
                    did = True
                    self.recording_function(header,frame)
                    self.recording_queue.task_done()
                    while self.recording_queue.qsize() > self.recording_maxqueue:
                        self.log.warning("recording queue runs over; try to reduce it by deleting data in memory")
                        try:
                            item = self.recording_queue.get_nowait()
                            self.recording_queue.task_done()
                        except: pass
            if did:
                time.sleep(0.001) # wait 1 millisecond
            elif self.recording:
                time.sleep(default_sleep)
            else:
                time.sleep(0.1) # wait 100 millisecond
        self.recording_thread_function_running = False
        self.fdlock.acquire() # lock
        if self.fd != None:
            self.fd.flush()
            self.fd.close()
            self.fd = None
        self.fdlock.release() # release the lock
        not_empty = True
        while not_empty:
            try:
                item = self.recording_queue.get_nowait()
                self.recording_queue.task_done()
                not_empty = True
            except:
                not_empty = False
        self.recording_thread_function_lock.release() # release the lock

    def recording_function(self,header,frame):
        needspace = 300+frame.nbytes
        self.fdlock.acquire() # lock
        freespace = self.recording_choose_path(needspace)
        if freespace >= needspace:
            self.recording_close_file_if_too_large(needspace)
            self.recording_create_filename(needspace)
            #self.log.debug("id: %d" % frame.id)
            self.fd.write("%s" % header)
            frame.tofile(self.fd)
            #i = PIL.Image.fromarray(frame)
            #i.save(self.fd,"ppm")
            self.fd.flush()
        else:
            self.log.warning("no space to save frames!")
            self.recording = False
        self.fdlock.release() # release the lock

    def recording_create_filename(self,needspace):
        if self.fd == None:
            # create filename
            self.patheslock.acquire() # lock
            #self.filename = os.path.join(self.pathes[self.pathes_index],self.filesuffixformat % self.filename_i)
            self.filename = "%s%s" % (self.pathes[self.pathes_index],(self.filesuffixformat % self.filename_i))
            self.patheslock.release() # release the lock
            while (os.path.exists(self.filename) and
                   (os.path.getsize(self.filename) > self.maxfilesize-needspace)):
                self.filename_i += 1
                self.filename = "%s%s" % (self.pathes[self.pathes_index],(self.filesuffixformat % self.filename_i))
            self.log.info("write to \"%s\"" % self.filename)
            self.fd = open(self.filename,"a")

    def recording_close_file_if_too_large(self,needspace):
        if self.fd != None:
            filesize = 0
            try:
                filesize = os.path.getsize(self.filename)
            except:
                self.fd == None
            if ((self.fd != None) and
                (filesize > self.maxfilesize-needspace)):
                self.fd.close()
                self.log.debug("stopped writing to \"%s\"" % self.filename)
                self.fd = None

    def recording_choose_path(self,needspace):
        self.patheslock.acquire() # lock
        freespace = self.recording_path_freespace(self.pathes[self.pathes_index])
        if freespace < needspace:
            # we need another place to write the images
            if self.fd != None:
                self.fd.close()
                self.fd = None
            while ((self.pathes_index < len(self.pathes)-1) and
                   (freespace < needspace)):
                self.pathes_index += 1
                freespace = self.recording_path_freespace(self.pathes[self.pathes_index])
            if needspace <= freespace:
                self.filename_i += 1
        self.patheslock.release() # release the lock
        return freespace

    def recording_path_freespace(self,path): # Bytes free on this path
        [p,f] = os.path.split(self.pathes[self.pathes_index])
        a = os.statvfs(p)
        return a.f_bavail*a.f_frsize # Bytes free on this path

    def getsingleframe(self):
        r = None
        if self.caminit and self.cam.running and self.running:
            i = self.cam.current_image
            if i != None:
                r = dict()
                r['frame'] = i
                r['id'] = i.id
                r['shape'] = i.shape
                r['header'] = self.bufheader[i.id]
            # else is the problem of another thread
        return r

    def stoprec(self):
        if self.recording:
            self.log.debug("stop recording")
            self.recording = False

    def stopcam(self):
        self.log.debug("try to stop cam (waiting for lock)")
        self.camlock.acquire() # lock for running
        self.log.debug("try to stop cam")
        try:
            self.cam.stop()
            self.log.debug("cam stoped")
        except:
            self.log.warning("cannot stop camera")
        self.camlock.release() # release the lock

    def get_current_image(self):
        i = None
        if self.caminit:
            i = self.cam.current_image
        return i

    def listcams(self):
        if self.caminit:
            # camera is running, therefor it must be stopped:
            self.stoprec()
            self.stopcam()
        self.valueslock.acquire() # lock for running
        self.camlock.acquire() # lock for running
        self.caminit = False
        cams = self.libdc1394.enumerate_cameras()
        camsdata = []
        # self.values = {'guid': None, 'isospeed': None, 'mode': None, 'image_size': None, 'image_position': None, 'color_coding': None, 'packet_size': None, 'framerate': None, 'feature_settings': None}
        for c in cams:
            cc = pydc1394.Camera(self.libdc1394,c['guid'])
            try:
                cc.isospeed = 800
            except: pass
            ff = dict()
            for f in cc.features:
                ff[f] = dict()
                ff[f]['val'] = cc.__getattribute__(f).val
                ff[f]['mode'] = cc.__getattribute__(f).mode
                ff[f]['modes'] = cc.__getattribute__(f).pos_modes
            mm = dict()
            for m in cc.modes:
                mm[m.name] = dict()
                if m.name[0:6] == "FORMAT":
                    mm[m.name]['max_image_size'] = m.max_image_size
                    mm[m.name]['color_codings'] = m.color_codings
                    mm[m.name]['unit_position'] = m.unit_position
                else:
                    mm[m.name]['framerates'] = m.framerates
            c['features'] = ff
            c['isospeed'] = cc.isospeed
            c['modes'] = mm
            camsdata += [c]
        self.camlock.release() # release the lock
        self.valueslock.release() # release the lock
        return camsdata

    def __del__(self):
        self.del_thread_running = False
        t = threading.Thread(target=self.del_thread)
        t.daemon = True # exit thread when the main thread terminates
        t.name = "del_thread"
        t.start()
        self.log.debug("del controller")
        st = time.time()
        time.sleep(0.01)
        while self.del_thread_running and (time.time()-st < 1.0):
            time.sleep(0.01)
        try:
            self.running = False
            self.cam.stop()
            time.sleep(0.001)
            self.cam.close()
            time.sleep(0.003)
        except:
            pass

    def del_thread(self):
        self.del_thread_running = True
        self.running = False
        self.recording = False
        self.caminit = False
        self.stopcam()
        time.sleep(0.001)
        self.camlock.acquire() # lock for running
        try:
            self.cam.close()
            time.sleep(0.01)
        except: pass
        self.camlock.release() # release the lock
        self.del_thread_running = False

    def quit(self):
        self.log.info("quitting")
        self.running = False
        time.sleep(0.003)
        self.__del__()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler,plc_tools.plc_socket_communication.tools_for_socket_communication):

    def handle(self):
        global controller
        threading.currentThread().name = "ThreadedTCPRequestHandler"
        self.send_data_to_socket_lock = threading.Lock()
        controller.log.debug("start connection to %s:%s" % (self.client_address[0],self.client_address[1]))
        data = ""
        #recv_bufsize = 4096 # read/receive Bytes at once
        recv_bufsize = controller.recvbuf # read/receive Bytes at once
        while controller.running:
            self.request.settimeout(1)
            # get some data
            d = ""
            try:
                d = self.request.recv(recv_bufsize)
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
                if (len(data) >= 9) and (data[0:9].lower() == "get1frame"):
                    # get single frame
                    #controller.log.debug("get1frame")
                    found_something = True
                    data = data[9:]
                    controller.startcam()
                    response += self.create_send_format(controller.getsingleframe())
                elif (len(data) >= 8) and (data[0:8].lower() == "startcam"):
                    # start camera
                    found_something = True
                    controller.log.debug("startcam")
                    data = data[8:]
                    controller.startcam()
                elif (len(data) >= 7) and (data[0:7].lower() == "stopcam"):
                    # start camera
                    found_something = True
                    controller.log.debug("stopcam")
                    data = data[7:]
                    controller.stopcam()
                elif (len(data) >= 9) and (data[0:9].lower() == "rec1frame"):
                    # start camera
                    found_something = True
                    controller.log.debug("rec1frame")
                    data = data[9:]
                    controller.rec1frame()
                elif (len(data) >= 8) and (data[0:8].lower() == "startrec"):
                    # start camera
                    found_something = True
                    controller.log.debug("startrec")
                    data = data[8:]
                    controller.startrec()
                elif (len(data) >= 7) and (data[0:7].lower() == "stoprec"):
                    # start camera
                    found_something = True
                    controller.log.debug("stoprec")
                    data = data[7:]
                    controller.stoprec()
                elif (len(data) >= 8) and (data[0:8].lower() == "listcams"):
                    # listcams
                    found_something = True
                    controller.log.debug("listcams")
                    data = data[8:]
                    response += self.create_send_format(controller.listcams())
                elif (len(data) >= 9) and (data[0:9].lower() == "getvalues"):
                    # send values/settings
                    found_something = True
                    controller.log.debug("getvalues")
                    data = data[9:]
                    response += self.create_send_format(controller.getvalues())
                elif (len(data) >= 10) and (data[0:9].lower() == "setvalues"):
                    # packed data; all settings at once
                    found_something = True
                    controller.log.debug("setvalues")
                    [data,v] = self.receive_data_from_socket2(self.request,bufsize=recv_bufsize,data=data[10:])
                    controller.setvalues(v)
                elif (len(data) >= 10) and (data[0:9].lower() == "setpathes"):
                    found_something = True
                    controller.log.debug("setpathes")
                    [data,v] = self.receive_data_from_socket2(self.request,bufsize=recv_bufsize,data=data[10:])
                    controller.setpathes(v)
                elif (len(data) >= 4) and (data[0:4].lower() == "quit"):
                    found_something = True
                    data = data[4:]
                    controller.quit()
                    self.server.shutdown()
                elif (len(data) >= 4) and (data[0:7].lower() == "version"):
                    controller.log.debug("version")
                    found_something = True
                    a = "camera_server Version: %s" % __camera_server_version__
                    response += self.create_send_format(a)
                    controller.log.debug(a)
                    data = data[7:]
                if len(data) == 0:
                    break
            if len(response) > 0:
                try:
                    self.send_data_to_socket(self.request,response)
                except:
                    pass

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
    threadinfos(controller.log)
    controller.log.info("will exit the program")
    controller.running = False

def main():
    global controller
    # command line parameter
    help = ""
    help += "Over the given port on the given address a socket communication is "
    help += "lisening with the following commands: (This is a prefix-code. Upper or lower letters do not matter.)\n"
    help += "  listcams : This will list all available cams and send back this information\n"
    help += "             as [pickle data]. The data start with a decimal number describing\n"
    help += "             the number of bytes for the pickled data block; then comes a space\n"
    help += "             and the pickled data itself. The data is an array of dicts.\n"
    help += "  getvalues : This sends back the settings of the camera as [pickle data]. It\n"
    help += "              is the same format as for listcams. The data is a dict.\n"
    help += "  setvalues : This sets the settings of the camera as [pickle data]. This is\n"
    help += "              the same format as for getvalues. If s are the [pickle data],\n"
    help += "              you shoud send \"setvalues %d %s\" % (len(s),s)\n"
    help += "  startcam : This starts the camera.\n"
    help += "  get1frame : This sends the actual frame back.\n"
    help += "  startrec : This starts recording.\n"
    help += "  stoprec : This stops recording.\n"
    help += "  rec1frame : This records 1 frame.\n"
    help += "  stopcam : This stops the camera.\n"
    help += "  setpathes : Set the pathes/prefixes to write the images to. It is the same\n"
    help += "              format as for setvalues\n"
    help += "  quit : quit the server\n"
    help += "  version : response the version of the server\n"
    help += "\nIf you have problems with your camera or firewire system, try: \"DC1394_DEBUG=1 camera_server.py -d 1\"\n"
    parser = argparse.ArgumentParser(
        description='camera_server is a socket server to control a camera on firewire. A friendly kill (SIGTERM) should be possible.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__camera_server_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-listcams',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='listcams',
                        help='Only list available cams and exit.')
    parser.add_argument('-guid',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='guid',
                        help='A camera with this guid will be used.',
                        metavar='id')
    parser.add_argument('-mode',
                        nargs=1,
                        default="FORMAT7_0",
                        type=str,
                        required=False,
                        dest='mode',
                        help='Set the camera mode. default: FORMAT7_0',
                        metavar='m')
    parser.add_argument('-color_coding',
                        nargs=1,
                        default="Y8",
                        type=str,
                        required=False,
                        dest='color_coding',
                        help='Set the color_coding for the camera. default: Y8',
                        metavar='c')
    parser.add_argument('-framerate',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='framerate',
                        help='Set the framerate for the camera.',
                        metavar='i')
    parser.add_argument('-logfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"camera.log"),
                        type=str,
                        required=False,
                        dest='logfile',
                        help='Set the logfile to f. The WatchedFileHandler is used. This means, the logfile grows indefinitely until an other process (e. g. logrotate or the user itself) move or delete the logfile. Under Windows moving or deleting of open files is impossible and therefore the logfile grows indefinitely. default: %s' % os.path.join(tempfile.gettempdir(),"camera.log"),
                        metavar='f')
    parser.add_argument('-runfile',
                        nargs=1,
                        default=os.path.join(tempfile.gettempdir(),"camera.pids"),
                        type=str,
                        required=False,
                        dest='runfile',
                        help='Set the runfile to f. If an other process is running with a given pid and writing to the same device, the program will not start. Setting f=\"\" will disable this function. default: %s' % os.path.join(tempfile.gettempdir(),"camera.pids"),
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
                        default=15114,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15114',
                        metavar='p')
    parser.add_argument('-choosenextport',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='choosenextport',
                        help='By specifying this flag the next available port after the given one will be choosen. Without this flag a socket.error is raised if the port is not available.')
    parser.add_argument('-ringbuf',
                        nargs=1,
                        default=8,
                        type=int,
                        required=False,
                        dest='ringbuf',
                        help='Set the number of buffers in the ring buffer of dc1394. Try to keep the total buffer size under a reasonable size. Kernel problems may occur over 32MB or 64MB. default: 8',
                        metavar='n')
    parser.add_argument('-recvbuf',
                        nargs=1,
                        default=4096,
                        type=int,
                        required=False,
                        dest='recvbuf',
                        help='Set the number of Bytes to receive at once by the socket communication. default: 4096',
                        metavar='n')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    args = parser.parse_args()
    if not isinstance(args.listcams,bool):
        args.listcams = args.listcams[0]
    if not isinstance(args.guid,str):
        args.guid = args.guid[0]
    try:
        if (args.guid[0:2] == "0x") or (args.guid[0:2] == "0X"):
            args.guid = int(args.guid,16)
        else:
            args.guid = int(args.guid)
    except: pass
    if not isinstance(args.mode,str):
        args.mode = args.mode[0]
    if not isinstance(args.color_coding,str):
        args.color_coding = args.color_coding[0]
    if not isinstance(args.framerate,str):
        args.framerate = args.framerate[0]
    try:
        args.framerate = float(args.framerate)
    except: pass
    if not isinstance(args.logfile,str):
        args.logfile = args.logfile[0]
    if not isinstance(args.runfile,str):
        args.runfile = args.runfile[0]
    if not isinstance(args.ip,str):
        args.ip = args.ip[0]
    if not isinstance(args.port,int):
        args.port = args.port[0]
    if not isinstance(args.ringbuf,int):
        args.ringbuf = args.ringbuf[0]
    if not isinstance(args.recvbuf,int):
        args.recvbuf = args.recvbuf[0]
    if not isinstance(args.choosenextport,bool):
        args.choosenextport = args.choosenextport[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if args.listcams:
        print("All cameras on the firewire-bus:\n")
        l = pydc1394.DC1394Library()
        cams = l.enumerate_cameras()
        for c in cams:
            s = "### %s %s ###" % (c['vendor'],c['model'])
            print((len(s)*"#"))
            print(s)
            print((len(s)*"#"))
            for k in ['vendor','model','guid','unit']:
                print(("%s: %s" % (k,c[k])))
            cc = pydc1394.Camera(l,c['guid'])
            s = cc.isospeed
            try:
                cc.isospeed = 800
                if s != cc.isospeed:
                    print(("switch isospeed to %d" % cc.isospeed))
            except: pass
            print(("isospeed: %d" % cc.isospeed))
            print(("modes: %s" % cc.modes))
            print(("features: %s" % cc.features))
            for f in cc.features:
                print(("%s: %s (%s in %s)" % (f,cc.__getattribute__(f).val,cc.__getattribute__(f).mode,cc.__getattribute__(f).pos_modes)))
            # analyse FORMAT7
            #for f in filter(lambda m: m.name[0:6] == "FORMAT", cc.modes):
            for f in cc.modes:
                if f.name[0:6] == "FORMAT":
                    #m, = filter(lambda m: m.name == f.name, cc.modes)
                    print(("%s max_image_size: %s" % (f.name,f.max_image_size)))
                    print(("%s color_codings: %s" % (f.name,f.color_codings)))
                    #m.image_size(width, height)
                    #m.unit_position
                    print(("%s unit_position: %d x %d" % (f.name,f.unit_position[0],f.unit_position[1])))
                    #print "unit_position",f.unit_position
                    #m.image_position(pos) # pos = (0,0) # The image position can only be a multiple of the unit position
                    #m.color_coding('Y8')
                    #m.roi
                    #m.packet_size
                    #m.recommended_packet_size
                    #packet_parameters
                    #m.total_bytes
                    #m.data_depth
                    #m.pixel_number
                else:
                    print(("%s framerates: %s" % (f.name,f.framerates)))
        sys.exit(0)
    # logging
    log = logging.getLogger('cs')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create file handler
    #fh = logging.handlers.WatchedFileHandler(args.logfile)
    fh = QueuedWatchedFileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(created)f %(name)s %(levelname)s %(message)s'))
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO) # logging.WARNING = 30
    ch.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(fh)
    log.addHandler(ch)
    log.info("start logging in camera_server: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    log.info("logging to \"%s\"" % args.logfile)
    signal.signal(signal.SIGTERM,shutdown)
    # check runfile
    if args.runfile != "":
        ori = [os.getpid(),args.guid]
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
                if rr and row[1] != args.guid: # checking iff same guid
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
            nri = [newpid,args.guid]
            index = runinfo.index(ori)
            runinfo[index] = nri
            f = open(args.runfile,'w')
            writer = csv.writer(f)
            for i in range(len(runinfo)):
                writer.writerows([runinfo[i]])
                f.close()
            time.sleep(0.053) # time for first communication with device
            sys.exit(0)
        log.removeHandler(ch)
        # threads in the default process are dead
        # in particular this means QueuedWatchedFileHandler is not working anymore
        fh.startloopthreadagain()
        log.info("removed console log handler")
    else:
        log.info("due to debug=1 will _not_ go to background (fork)")
    controller = controller_class(log=log,guid=args.guid,mode=args.mode,color_coding=args.color_coding,framerate=args.framerate,ringbuf=args.ringbuf,recvbuf=args.recvbuf)
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
    server_thread.name = "ThreadedTCPServer"
    server_thread.start()
    while controller.running:
        time.sleep(1) # it takes at least 1 second to exit
    if threading.activeCount() > 2:
        time.sleep(0.1)
    server.shutdown()
    controller.__del__()
    for i in range(12):
        if threading.activeCount() > 2:
            time.sleep(0.01)
        else:
            break
    log.info("exit")
    if threading.activeCount() > 2:
        log.error("still %d threads running! (SocketServer needs up to 0.5 seconds)" % threading.activeCount())
        threadinfos(log)
        log.error("enumerate: %s" % threading.enumerate())
        log.error("wait 3 seconds for these threads.")
        time.sleep(3)
        if threading.activeCount() > 2:
            log.error("still %d threads running!" % threading.activeCount())
            log.error("enumerate: %s" % threading.enumerate())
            log.error("exit with os._exit (critical abort)")
            os._exit(os.EX_SOFTWARE)
    # 2 threas should run: me and QueuedWatchedFileHandler
    fh.close() # stopping QueuedWatchedFileHandler
    log.debug("stop logging to file")
    time.sleep(0.01)
    for i in range(10):
        if threading.activeCount() > 2:
            time.sleep(0.01)
        else:
            break
    threadinfos()
    sys.exit(0)

def threadinfos(log=None):
    if log:
        log.debug("%d threads running:" % threading.activeCount())
    else:
        print(("%d threads running:" % threading.activeCount()))
    for t in threading.enumerate():
        s = ""
        if threading.currentThread() == t:
            s = " (me)"
        if t.daemon:
            s+= " [daemon]"
        if log:
            log.debug("   %s%s" % (t.name,s))
        else:
            print(("   %s%s" % (t.name,s)))

if __name__ == "__main__":
    main()
