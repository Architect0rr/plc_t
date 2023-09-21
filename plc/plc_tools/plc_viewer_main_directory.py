"""main_directory for plc_viewer

Author: Daniel Mohr
Date: 2013-04-09
"""

import os
import pickle
import re
#import string
import zipfile
import sys
import fnmatch
import zipfile
import time

import plc_gui.read_config_file
from plc_tools.plc_viewer_gui import gui
from plc_gui.class_rf_generator import *

def main_directory(log,args):
    log.debug("start main_directory")
    log.debug("scale to %f" % args.scale)
    indexfile = os.path.join(args.dir,"index.zip")
    timestampsfile = "timestamps.pkl" # file in the indexfile
    mpclogdatafile = "mpclogdata.pkl" # file in the indexfile
    logdatafile = "logdata.pkl" # file in the indexfile
    rflogdatafile = "rflogdata.pkl" # file in the indexfile
    brightnessfile = "brightness.pkl" # file in the indexfile
    diffsfile = "diffs.pkl" # file in the indexfile
    brightness = None
    diffs = None
    if not os.path.isdir(args.dir):
        log.error("Directory \"%s\" does not exists!" % args.dir)
        sys.exit(1)
    log.debug("read \"%s\"" % args.config)
    configs = plc_gui.read_config_file.read_config_file(system_wide_ini_file="",user_ini_file=args.config)
    if os.path.isfile(os.path.join(args.dir,indexfile)):
        log.debug("read data from index.zip")
        # read database from index.zip
        zip = zipfile.ZipFile(indexfile,"r")
        # read timestamps
        timestamps = pickle.loads(zip.read(timestampsfile))
        # read mpclogdata
        mpclogdata = pickle.loads(zip.read(mpclogdatafile))
        # read logdata
        logdata = pickle.loads(zip.read(logdatafile))
        # read rflogdata
        rflogdata = pickle.loads(zip.read(rflogdatafile))
        # try to read brightness
        if brightnessfile in zip.namelist():
            brightness = pickle.loads(zip.read(brightnessfile))
        # try to read diffs
        if diffsfile in zip.namelist():
            diffs = pickle.loads(zip.read(diffsfile))
        zip.close()
        log.debug("data read: %d, %d, %d, %d" % (len(timestamps),len(mpclogdata),len(logdata),len(rflogdata)))
    else:
        # create database and write it to index.pkl
        # find all cameras
        cameras_file_prefix = []
        files = sorted(os.listdir(args.dir))
        for f in files:
            if fnmatch.fnmatch(f,'*.zip'):
                r = re.findall("([^.]+)[0-9]{3}.zip",f)
                if r:
                    if not (r[0] in cameras_file_prefix):
                        cameras_file_prefix = cameras_file_prefix + [r[0]]
        cameras_file_prefix = sorted(cameras_file_prefix)
        #log.debug("found %d sets of camera data: %s" % (len(cameras_file_prefix),string.join(cameras_file_prefix,", ")))
        log.debug("found %d sets of camera data: %s" % (len(cameras_file_prefix),", ".join(cameras_file_prefix)))
        # find all camera data and put them in the database
        timestamps = []
        archives = []
        zips = dict()
        for i in range(len(cameras_file_prefix)):
            timestamps += [[]]
        for f in files:
            if fnmatch.fnmatch(f,'*.zip'):
                r = re.findall("([^.]+)[0-9]{3}.zip",f)
                if r:
                    log.debug("read timestamps from %s" % f)
                    archives += [f]
                    zips[f] = zipfile.ZipFile(f,"r")
                    lines = zips[f].read("timestamps.txt").split("\n")
                    zips[f].close()
                    for l in lines:
                        if len(l) > 1:
                            [fn,ts] = l.split("\t")
                            timestamps[cameras_file_prefix.index(r[0])] += [[float(ts),f,fn]]
        for i in range(len(cameras_file_prefix)):
            timestamps[i] = sorted(timestamps[i], key=lambda a: a[0])
        timestamp_min = timestamps[0][0][0]
        timestamp_max = timestamps[0][0][0]
        for i in range(len(timestamps)):
            for j in range(len(timestamps[i])):
                if timestamps[i][j][0] < timestamp_min:
                    timestamp_min = timestamps[i][j][0]
                if timestamps[i][j][0] > timestamp_max:
                    timestamp_max = timestamps[i][j][0]
        log.debug("timestamps from %f to %f" % (timestamp_min,timestamp_max))
        # create mpclogdata and logdata and rflogdata
        mpclogdata = None
        logdata = None
        if os.path.isfile(os.path.join(args.dir,"data.log")):
            # analyze data.log
            log.info("read logfiles")
            log.debug("read logfiles from \"data.log\"")
            generator = [None,None,None]
            for g in range(3):
                #['RF-Generator 1','RF-Generator 2','RF-Generator 3']
                generator[g] = class_rf_generator()

                if configs.values.get("RF-Generator %d" % (g+1),'power_controller') == "-1":
                    generator[g].exists = False
                else:
                    generator[g].exists = True
            log_file = open(os.path.join(args.dir,"data.log"),"r")
            datalog_content = log_file.readlines()
            log_file.close()
            mpclogdata = []
            logdata = []
            rflogdata = []
            for l in datalog_content:
                r = re.findall("([^\t]+)\tMPC transmitted: ([^\t]+)",l)
                if r:
                    # mpc
                    if ((len(r[0][1]) == 59) and
                        (timestamp_min <= float(r[0][0])) and
                         (float(r[0][0]) <= timestamp_max)): # enough data and the right time
                        tlogdata = dict()
                        tlogdata['mpc'] = dict()
                        adcvalues = r[0][1][23:55]
                        adc = []
                        for i in range(8):
                            adc += [int(adcvalues[i*4:i*4+4],16)]
                        tlogdata['mpc']['ADC'] = adc
                        #print "re",adc[0],int(adc[0],16)
                        mpclogdata += [[float(r[0][0]),tlogdata]]
                else:
                    r = re.findall("([^\t]+)\tto (rf-dc|rf-gen) ([0-9]+): ([^\t]+)",l)
                    if r:
                        # RF
                        t = r[0][0]
                        if ((timestamp_min <= float(t)) and
                             (float(t) <= timestamp_max)): # the right time
                            g = int(r[0][2])
                            s = re.sub("[\n\r]+","",r[0][3])
                            # #O#DE803E803E803E803
                            # @X06@P00000000@E
                            if r[0][1] == "rf-dc":
                                r = re.findall("#(O|o)",s) # #o #O
                                if r:
                                    if r[len(r)-1] == "O":
                                        pass
                                    elif r[len(r)-1] == "o":
                                        pass
                                r = re.findall("#D([A-F0-9]{16})",s) # #D
                                if r:
                                    v = r[len(r)-1]
                                    ii = [2,3,0,1]
                                    for i in range(4):
                                        vv = v[i*4+0:i*4+4]
                                        vv = "%s%s" % (vv[2:4],v[0:2])
                                        generator[g].actualvalue_channel[ii[i]].current = int(vv,16)
                            elif r[0][1] == "rf-gen":
                                r = re.findall("@(E|D)",s) # @E @D
                                if r:
                                    if r[len(r)-1] == 'D':
                                        generator[g].actualvalue_rf_onoff = False
                                    elif r[len(r)-1] == 'E':
                                        generator[g].actualvalue_rf_onoff = True
                                r = re.findall("@X([A-F0-9]{2})",s) # @X
                                if r:
                                    v = '{0:04b}'.format(int(r[len(r)-1],16))
                                    for i in range(4):
                                        if v[i] == '1':
                                            generator[g].actualvalue_channel[i].onoff = True
                                        else:
                                            generator[g].actualvalue_channel[i].onoff = False
                                r = re.findall("@P([A-F0-9]{8})",s) # @P
                                if r:
                                    v = r[len(r)-1]
                                    for i in range(4):
                                        generator[g].actualvalue_channel[i].phase = int(v[i*2+0:i*2+2],16)
                        # create storeable data
                        gen = [None,None,None]
                        for g in range(3):
                            gen[g] = dict()
                            gen[g]['exists'] = generator[g].exists
                            if gen[g]['exists']:
                                gen[g]['rf_onoff'] = generator[g].actualvalue_rf_onoff
                                gen[g]['channel'] = [None,None,None,None]
                                ii = [2,3,0,1]
                                for i in range(4):
                                    gen[g]['channel'][i] = dict()
                                    gen[g]['channel'][i]['current'] = generator[g].actualvalue_channel[ii[i]].current
                                    gen[g]['channel'][i]['onoff'] = generator[g].actualvalue_channel[i].onoff
                                    gen[g]['channel'][i]['phase'] = generator[g].actualvalue_channel[i].phase
                        rflogdata += [[float(t),gen]]
                    else:
                        # somthing else
                        r = re.findall("([^\t]+)\t([^\t]+)",l)
                        if r:
                            logdata += [[float(r[0][0]),re.sub("[\n\r]+","",r[0][1])]]
            datalog_content = None
            mpclogdata = sorted(mpclogdata, key=lambda a: a[0])
            logdata = sorted(logdata, key=lambda a: a[0])
            rflogdata = sorted(rflogdata, key=lambda a: a[0])
            # data.log analyzed
            #print "bla",mpclogdata[0][0],mpclogdata[0][1]['mpc']['ADC'][0]
        # write data
        log.debug("save data to \"%s\"" % indexfile)
        zip = zipfile.ZipFile(indexfile,"w",zipfile.ZIP_DEFLATED)
        # write timestamps
        z = zipfile.ZipInfo()
        z.external_attr = 0o600 << 16
        z.compress_type = zipfile.ZIP_DEFLATED
        z.filename = timestampsfile
        z.date_time = time.localtime(time.time())[0:6]
        zip.writestr(z,pickle.dumps(timestamps))
        # write mpclogdata
        z = zipfile.ZipInfo()
        z.external_attr = 0o600 << 16
        z.compress_type = zipfile.ZIP_DEFLATED
        z.filename = mpclogdatafile
        z.date_time = time.localtime(time.time())[0:6]
        zip.writestr(z,pickle.dumps(mpclogdata))
        # write logdata
        z = zipfile.ZipInfo()
        z.external_attr = 0o600 << 16
        z.compress_type = zipfile.ZIP_DEFLATED
        z.filename = logdatafile
        z.date_time = time.localtime(time.time())[0:6]
        zip.writestr(z,pickle.dumps(logdata))
        # write rflogdata
        z = zipfile.ZipInfo()
        z.external_attr = 0o600 << 16
        z.compress_type = zipfile.ZIP_DEFLATED
        z.filename = rflogdatafile
        z.date_time = time.localtime(time.time())[0:6]
        zip.writestr(z,pickle.dumps(rflogdata))
        gen = None
        generator = None
        zip.close()
        z = None
        # database created
    timestamp_min = timestamps[0][0][0]
    timestamp_max = timestamps[0][0][0]
    for i in range(len(timestamps)):
        for j in range(len(timestamps[i])):
            if timestamps[i][j][0] < timestamp_min:
                timestamp_min = timestamps[i][j][0]
            if timestamps[i][j][0] > timestamp_max:
                timestamp_max = timestamps[i][j][0]
    log.debug("frames from %f to %f" % (timestamp_min,timestamp_max))
    if args.index != 1:
        t = gui(log=log,mpclogdata=mpclogdata,logdata=logdata,rflogdata=rflogdata,brightness=brightness,diffs=diffs,indexfile=indexfile,brightnessfile=brightnessfile,diffsfile=diffsfile,configs=configs,timestamps=timestamps,camcolumn=args.camcolumn,timeratefactor=args.timeratefactor,scale=args.scale,absolutscale=args.absolutscale,timestamp_min=timestamp_min,timestamp_max=timestamp_max,minupdateinterval1=6,maxupdateinterval1=42,minupdateinterval2=1,maxupdateinterval2=23,create_info_graphics=args.create_info_graphics,gamma=args.gamma)
        t.main_window.mainloop()
        t.destroy()
    log.debug("exit main_directory")

# 1347250946.728442       MPC transmitted: @Q000D0000000000000000A07F3094920BD000120C520CC20D120D8IFC
#@Q000D0000000000000000A
#07F3094920BD000120C520CC20D120D8
#IFC
