#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-03-28, 2013-09-18, 2013-09-24, 2014-07-22, 2017-05-30

__rawmovies2pngs_date__ = "2017-05-30"
__rawmovies2pngs_version__ = __rawmovies2pngs_date__

import argparse
import os
import zipfile
import time
import logging
import logging.handlers
import re
import PIL.Image
import pickle

import PIL.ImageEnhance
import PIL.ImageOps

def enhance_image(pic,args):
    if args.ebrightness != 1.0:
        enhancer = PIL.ImageEnhance.Brightness(pic)
        pic = enhancer.enhance(args.ebrightness)
    if args.econtrast != 1.0:
        enhancer = PIL.ImageEnhance.Contrast(pic)
        pic = enhancer.enhance(args.econtrast)
    if args.esharpness != 1.0:
        enhancer = PIL.ImageEnhance.Sharpness(pic)
        pic = enhancer.enhance(args.esharpness)
    if args.doequalize:
        pic = PIL.ImageOps.equalize(pic)
    if args.autocontrast:
        pic = PIL.ImageOps.autocontrast(pic)
    if args.invert:
        pic = PIL.ImageOps.invert(pic)
    if args.horizontal_mirror:
        pic = PIL.ImageOps.mirror(pic)
    if args.vertical_mirror:
        pic = PIL.ImageOps.flip(pic)
    return pic

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

def ifromtime(t,db):
    i = 0
    imin = 0
    imax = max(0,len(db) - 1)
    #i = int((imax + imin + 1) / 2)
    #print("########## %d ########## %f ########## %f ##########" % (i,db[i]["timestamp"],t))
    while imax-imin > 1:
        if t <= db[i]["timestamp"]:
            imax = i
        if t >= db[i]["timestamp"]:
            imin = i
        i = int((imax + imin + 1) / 2)
    return i

def read_prefixfile(log,args):
    timeformats = ["%Y-%m-%dT%H:%M:%S","%Y-%m-%d %H:%M:%S"]
    interesting_times = []
    file_names_for_interesting_times = []
    if os.path.isfile(args.prefixfile):
        log.debug("read prefixfile")
        fd = open(args.prefixfile,'r')
        r = fd.readline()
        while r != "":
            t = r.strip()
            if len(t) > 0 and t[0] != "#":
                a = t.split(";")
                if a[0] != "":
                    found = False
                    for f in timeformats:
                        try:
                            tt = time.mktime(time.strptime(a[0],f))
                            found = True
                        except:
                            pass
                        if found:
                            break
                    if found:
                        interesting_times += [tt]
                        file_names_for_interesting_times += [a[1]]
                    else:
                        log.debug("do not understand time format \"%s\"" % a[0])
            r = fd.readline()
        fd.close()
    return [interesting_times,file_names_for_interesting_times]

def main():
    # command line parameter
    parser = argparse.ArgumentParser(
        description='rawmovie2pngs.py',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\nExample: rawmovie2pngs.py -d 1 -f cam_0_PF2011-CAM3_2012-09-11_006.img -o t" % __rawmovies2pngs_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-f',
                        nargs="+",
                        type=str,
                        required=True,
                        dest='file',
                        help='will convert this/theses file(s)',
                        metavar='file')
    parser.add_argument('-outdir',
                        nargs=1,
                        default="./",
                        type=str,
                        required=False,
                        dest='outdir',
                        help='Set the output directory. Default: ./',
                        metavar='dir')
    parser.add_argument('-info',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='info',
                        help='If set to 1 gives only informations.',
                        metavar='i')
    parser.add_argument('-prefix',
                        nargs=1,
                        default="frame",
                        type=str,
                        required=False,
                        dest='prefix',
                        help='Set the prexif for the names. Default: "frame". Possible variables in prefix are "[timestamp]" and "[nr]".',
                        metavar='pre')
    parser.add_argument('-suffix',
                        nargs=1,
                        default="_[timestamp].png",
                        type=str,
                        required=False,
                        dest='suffix',
                        help='Set the suffix for the names. Default: "_[timestamp].png". Possible variables in suffix are "[timestamp]" and "[nr]".',
                        metavar='suf')
    parser.add_argument('-nrlength',
                        nargs=1,
                        default=5,
                        type=int,
                        required=False,
                        dest='nrlength',
                        help='Set the length of the frame number [nr] in prefix and suffix. Default: 5',
                        metavar='n')
    parser.add_argument('-prefixfile',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='prefixfile',
                        help='Set the prexifile with the names. The file should have the structure \"[time];[name]\", where [time] represents a local time and [name] represents the filename; e. g. \"2013-03-22 13:59:53;frame_40Vpp_phase_160_%%s\". Only the frames of the given time are converted. \"%%s\" will be replaced by the timestamp of the frame. The frame will only be choosen, if the time difference is less than 1 second.',
                        metavar='f')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    parser.add_argument('-optimizedpng',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='optimizedpng',
                        help='If set this flag, optimized png graphics will be created. On default, no optimized png will be created. Creation of optimized png takes long and saves space. (no optimized png: 100 %% time and data; optimized png: 604 %% time and 93 %% data)')
    parser.add_argument('-ebrightness',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='ebrightness',
                        help='Enhanced the brightness by a value. default: 1.0 (do not change something)',
                        metavar='fac')
    parser.add_argument('-econtrast',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='econtrast',
                        help='Enhanced the contrast by a value. default: 1.0 (do not change something)',
                        metavar='fac')
    parser.add_argument('-esharpness',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='esharpness',
                        help='Enhanced the sharpness by a value. default: 1.0 (do not change something)',
                        metavar='fac')
    parser.add_argument('-equalize',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='doequalize',
                        help='If set this flag, the images will be equalized due to their histogram. (only useful for view)')
    parser.add_argument('-autocontrast',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='autocontrast',
                        help='If set this flag, the image contrast will be normalized/maximized.')
    parser.add_argument('-invert',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='invert',
                        help='If set this flag, the image will be inverted.')
    parser.add_argument('-horizontal_mirror',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='horizontal_mirror',
                        help='If set this flag, the image will be mirrored (left to rigth).')
    parser.add_argument('-vertical_mirror',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='vertical_mirror',
                        help='If set this flag, the image will be mirrored (top to bottom).')
    args = parser.parse_args()
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.outdir,str):
        args.outdir = args.outdir[0]
    if not isinstance(args.prefix,str):
        args.prefix = args.prefix[0]
    if not isinstance(args.suffix,str):
        args.suffix = args.suffix[0]
    if not isinstance(args.nrlength,int):
        args.nrlength = args.nrlength[0]
    if not isinstance(args.prefixfile,str):
        args.prefixfile = args.prefixfile[0]
    if not isinstance(args.optimizedpng,bool):
        args.optimizedpng = args.optimizedpng[0]
    if not isinstance(args.ebrightness,float):
        args.ebrightness = args.ebrightness[0]
    if not isinstance(args.econtrast,float):
        args.econtrast = args.econtrast[0]
    if not isinstance(args.esharpness,float):
        args.esharpness = args.esharpness[0]
    if not isinstance(args.doequalize,bool):
        args.doequalize = args.doequalize[0]
    if not isinstance(args.autocontrast,bool):
        args.autocontrast = args.autocontrast[0]
    if not isinstance(args.invert,bool):
        args.invert = args.invert[0]
    if not isinstance(args.horizontal_mirror,bool):
        args.horizontal_mirror = args.horizontal_mirror[0]
    if not isinstance(args.vertical_mirror,bool):
        args.vertical_mirror = args.vertical_mirror[0]
    # logging
    log = logging.getLogger('rawmovie2pngs')
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
    log.info("start logging in rawmovie2pngs: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    # do something
    if args.prefixfile != "":
        # read prefixfile
        [interesting_times,file_names_for_interesting_times] = read_prefixfile(log,args)
    rec = 1
    recit = 1
    timestampsoutput = ""
    lasttimestamp = None
    for f in args.file:
        log.debug("file: %s" % f)
        headerlength = 0
        if os.path.isfile(f):
            p = False
            pics = []
            fd = open(f,'rb')
            #[timestamp,width,depth,maxval,headerlength,picture]
            readimagebytes = True
            if args.info or args.prefixfile != "":
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
            if p:
                #n = os.path.getsize(f)/(headerlength+width*height*depth)
                n = len(pics)
                log.debug("found %d pictures in %s" % (n,f))
                if args.info:
                    log.debug("timestamps:")
                    for p in pics:
                        log.debug("%f" % p["timestamp"])
                elif args.prefixfile != "":
                    log.debug("converting (%s) ..." % args.prefixfile)
                    fd = open(f,'rb')
                    outdir = os.path.join(args.outdir,"")
                    if not os.path.isdir(os.path.dirname(outdir)):
                        os.mkdir(os.path.dirname(outdir))
                    for t in interesting_times:
                        if t > 0:
                            # find pic
                            i = ifromtime(t,pics)
                            if abs(pics[i]["timestamp"]-t) < 1:
                                fn = file_names_for_interesting_times[interesting_times.index(t)]
                                fn = fn.replace("%s","%d" % pics[i]["timestamp"])
                                log.debug("%d <-> %f <-> %s" % (i,t,fn))
                                # read image
                                fd.seek(pics[i]["fileposition"])
                                pics[i]["picture"] = fd.read(pics[i]["picturesize"])
                                # write image
                                outputname = os.path.join(args.outdir,"%s.png" % (fn))
                                output =  open(outputname,'wb')
                                pic = PIL.Image.frombuffer("L",(pics[i]["width"],pics[i]["height"]),pics[i]["picture"],'raw',"L",0,1)
                                pic = enhance_image(pic,args)
                                if args.optimizedpng:
                                    pic.save(output,"PNG",optimize=True)
                                else:
                                    pic.save(output,"PNG")
                                output.flush()
                                output.close()
                                interesting_times[interesting_times.index(t)] = -1
                    fd.close()
                else:
                    log.debug("converting...")
                    outdir = os.path.join(args.outdir,args.prefix)
                    if not os.path.isdir(os.path.dirname(outdir)):
                        os.mkdir(os.path.dirname(outdir))
                    log.debug("write to %s" % outdir)
                    nrformat = "%0"+"%d" % args.nrlength+"d"
                    i = 0
                    for p in pics:
                        log.debug("i: %d" % i)
                        timestamp = None
                        if p["timestamp"] != None:
                            timestamp = p["timestamp"]
                            pic = PIL.Image.frombuffer("L",(p["width"],p["height"]),p["picture"],'raw',"L",0,1)
                        if (timestamp != None) and (lasttimestamp != None):
                            if (timestamp - lasttimestamp) > 1:
                                rec = rec + 1
                                timestampsoutput = ""
                                recit = 1
                        pic = enhance_image(pic,args)
                        # write image
                        outputname = "%s%s" % (outdir,args.suffix)
                        outputname = outputname.replace("[timestamp]","%d" % pics[i]["timestamp"])
                        outputname = outputname.replace("[nr]",nrformat % i)
                        #outputname = "%s_%s.png" % (outdir,timestamp)
                        output =  open(outputname,'wb')
                        if args.optimizedpng:
                            pic.save(output,"PNG",optimize=True)
                        else:
                            pic.save(output,"PNG")
                        output.flush()
                        output.close()
                        if (timestamp != None):
                            timestampsoutput = "%s\n%s%03d_%06d.png\t%f" % (timestampsoutput,args.prefix,rec,recit,timestamp)
                            lasttimestamp = timestamp
                        recit += 1
                        i += 1
                    fd.close()

if __name__ == "__main__":
    main()
