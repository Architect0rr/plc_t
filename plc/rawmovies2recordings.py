#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-10-20, 2014-07-22, 2017-05-30

__rawmovies2recordings_date__ = "2017-05-30"
__rawmovies2recordings_version__ = __rawmovies2recordings_date__

import argparse
import os
import zipfile
import time
import logging
import logging.handlers
import re
import io
import PIL.Image
import pickle

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
           "picturesize": None,
           "header": ""}
    magic = fd.read(2)
    pic["headerlength"] += 2
    pic["header"] += magic
    if magic == "P7":
        log.debug("OK, right format")
        t = fd.readline() # first line with magic
        pic["header"] += t
        t = t.strip()
        pic["headerlength"] += len(t)+1
        while (t != "ENDHDR"):
            t = fd.readline()
            pic["header"] += t
            t = t.strip()
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

def main():
    # command line parameter
    parser = argparse.ArgumentParser(
        description='rawmovies2recordings.py',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\nExample: rawmovies2recordings.py -d 1 -f cam_0_PF2011-CAM3_2012-09-11_006.img -o t -p \"2012-09-11_PF2011-CAM3_rec_\"" % __rawmovies2recordings_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
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
    parser.add_argument('-prefix',
                        nargs=1,
                        default="rec",
                        type=str,
                        required=False,
                        dest='prefix',
                        help='Set the prexif for the archiv names. Default: rec',
                        metavar='dir')
    parser.add_argument('-optimizedpng',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='optimizedpng',
                        help='If set this flag, optimized png graphics will be created inside the zip archives. On default, no optimized png will be created. Creation of optimized png takes long and saves space. (no optimized png: 100 %% time and data; optimized png: 589 %% time and 93 %% data)')
    parser.add_argument('-nowriteheader',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='no_write_header',
                        help='If set this flag, the original image headers are not written to the zip-files.')
    parser.add_argument('-writepickledata',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='write_pickle_data',
                        help='If set this flag, the image data are written as pickled files to the zip-files.')
    parser.add_argument('-writepickledatawithpicture',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='write_pickle_data_with_picture',
                        help='If set this flag, the image data together with the images itselfs and the complete header are written as pickled files to the zip-files')
    args = parser.parse_args()
    configname = ""
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.outdir,str):
        args.outdir = args.outdir[0]
    if not isinstance(args.prefix,str):
        args.prefix = args.prefix[0]
    if not isinstance(args.optimizedpng,bool):
        args.optimizedpng = args.optimizedpng[0]
    if not isinstance(args.no_write_header,bool):
        args.no_write_header = args.no_write_header[0]
    if not isinstance(args.write_pickle_data,bool):
        args.write_pickle_data = args.write_pickle_data[0]
    if not isinstance(args.write_pickle_data_with_picture,bool):
        args.write_pickle_data_with_picture = args.write_pickle_data_with_picture[0]
    # logging
    log = logging.getLogger('rawmovies2recordings')
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
    log.info("start logging in rawmovies2recordings: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    # do something
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
            pic = readimage(log,fd,True)
            if pic["picture"] != None:
                p = True
                pics += [pic]
            while pic["picture"] != None:
                pic = readimage(log,fd,True)
                if pic["picture"] != None:
                    p = True
                    pics += [pic]
            fd.close()
            if p:
                n = len(pics)
                log.debug("found %d pictures in %s" % (n,f))
                log.debug("converting...")
                outdir = os.path.join(args.outdir,"%s%03d.zip" % (args.prefix,rec))
                if not os.path.isdir(os.path.dirname(outdir)):
                    os.mkdir(os.path.dirname(outdir))
                log.debug("write to archiv %s" % outdir)
                zip = zipfile.ZipFile(outdir,"a",zipfile.ZIP_STORED,allowZip64=True)
                infofilefd = open(os.path.join(args.outdir,"info.txt"),'a')
                infofilefd.write('%s <-> %s\n' % (os.path.normpath(outdir),os.path.normpath(f)))
                infofilefd.close()
                for i in range(n):
                    log.debug("i: %d" % i)
                    if pics[i]["timestamp"] != None:
                        timestamp = pics[i]["timestamp"]
                        pic = PIL.Image.frombuffer("L",(pics[i]["width"],pics[i]["height"]),pics[i]["picture"],'raw',"L",0,1)
                    if (timestamp != None) and (lasttimestamp != None):
                        if (timestamp - lasttimestamp) > 1:
                            z = zipfile.ZipInfo()
                            z.filename = "timestamps.txt"
                            z.date_time = time.localtime(time.time())[0:6]
                            z.compress_type = zipfile.ZIP_DEFLATED
                            z.external_attr = 0o600 << 16
                            zip.writestr(z,timestampsoutput)
                            zip.close()
                            rec = rec + 1
                            timestampsoutput = ""
                            outdir = os.path.join(args.outdir,"%s%03d.zip" % (args.prefix,rec))
                            if not os.path.isdir(os.path.dirname(outdir)):
                                os.mkdir(os.path.dirname(outdir))
                            recit = 1
                            log.debug("write to archiv %s" % outdir)
                            zip = zipfile.ZipFile(outdir,"a",zipfile.ZIP_STORED,allowZip64=True)
                            infofilefd = open(os.path.join(args.outdir,"info.txt"),'a')
                            infofilefd.write('%s <-> %s\n' % (os.path.normpath(outdir),os.path.normpath(f)))
                            infofilefd.close()
                    # write image
                    output = io.StringIO()
                    if args.optimizedpng:
                        pic.save(output,"PNG",optimize=True)
                    else:
                        pic.save(output,"PNG")
                    contents = output.getvalue()
                    output.close()
                    z = zipfile.ZipInfo()
                    z.filename = "%s%03d_%06d.png" % (args.prefix,rec,recit)
                    if (timestamp != None):
                        z.date_time = time.localtime(timestamp)[0:6]
                        timestampsoutput = "%s\n%s%03d_%06d.png\t%f" % (timestampsoutput,args.prefix,rec,recit,timestamp)
                        lasttimestamp = timestamp
                    else:
                        z.date_time = time.localtime(time.time())[0:6]
                    z.external_attr = 0o600 << 16
                    zip.writestr(z,contents)
                    # write header
                    if not args.no_write_header:
                        z = zipfile.ZipInfo()
                        z.filename = "%s%03d_%06d.header" % (args.prefix,rec,recit)
                        if (timestamp != None):
                            z.date_time = time.localtime(timestamp)[0:6]
                        else:
                            z.date_time = time.localtime(time.time())[0:6]
                        z.compress_type = zipfile.ZIP_DEFLATED
                        z.external_attr = 0o600 << 16
                        zip.writestr(z,pics[i]["header"])
                    # write pickle
                    if args.write_pickle_data:
                        tpic = pics[i]
                        if not args.write_pickle_data_with_picture:
                            del tpic["picture"]
                            del tpic["header"]
                        z = zipfile.ZipInfo()
                        z.filename = "%s%03d_%06d.pickle" % (args.prefix,rec,recit)
                        if (timestamp != None):
                            z.date_time = time.localtime(timestamp)[0:6]
                        else:
                            z.date_time = time.localtime(time.time())[0:6]
                        z.compress_type = zipfile.ZIP_DEFLATED
                        z.external_attr = 0o600 << 16
                        zip.writestr(z,pickle.dumps(tpic,-1))
                    # increase recit
                    recit += 1
                zip.close()
    if len(timestampsoutput) > 0:
        zip = zipfile.ZipFile(outdir,"a",zipfile.ZIP_STORED,allowZip64=True)
        # write timestamps
        z = zipfile.ZipInfo()
        z.filename = "timestamps.txt"
        z.date_time = time.localtime(time.time())[0:6]
        z.compress_type = zipfile.ZIP_DEFLATED
        z.external_attr = 0o600 << 16
        zip.writestr(z,timestampsoutput)
        zip.close()

if __name__ == "__main__":
    main()
