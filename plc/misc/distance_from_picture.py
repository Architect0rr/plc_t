#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-09-22, 2013-10-21, 2017-05-30

__distance_from_picture_date__ = "2017-05-30"
__distance_from_picture_version__ = __distance_from_picture_date__

import argparse
import logging
import logging.handlers
import PIL.Image
import time
import numpy

def main():
    # command line parameter
    parser = argparse.ArgumentParser(
        description='distance_from_picture.py',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n" % __distance_from_picture_date__,
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
    parser.add_argument('-showimage',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='showimage',
                        help='0 do not show the image (default); 1 show the image.',
                        metavar='i')
    parser.add_argument('-hdistance_factor',
                        nargs=1,
                        default=0.5,
                        type=float,
                        required=False,
                        dest='xf',
                        help='gives the distance factor in x direction in mm. Ddefault: 0.05',
                        metavar='xf')
    parser.add_argument('-vdistance_factor',
                        nargs=1,
                        default=0.5,
                        type=float,
                        required=False,
                        dest='yf',
                        help='gives the distance factor in x direction in mm. Ddefault: 0.05',
                        metavar='yf')
    parser.add_argument('-smooth',
                        nargs=1,
                        default=-1,
                        type=int,
                        required=False,
                        dest='smooth',
                        help='0 do not smooth the data. For l > 0 gives the length of smoothing intervall. Default: 1 %% of image height/width.',
                        metavar='l')
    args = parser.parse_args()
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.showimage,int):
        args.showimage = args.showimage[0]
    if not isinstance(args.xf,float):
        args.xf = args.xf[0]
    if not isinstance(args.yf,float):
        args.yf = args.yf[0]
    if not isinstance(args.smooth,int):
        args.smooth = args.smooth[0]
    # logging
    log = logging.getLogger('distance_from_picture')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO) # logging.INFO = ??
        #ch.setLevel(logging.WARNING) # logging.WARNING = 30
    #ch.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s',datefmt='%H:%M:%S'))    # add the handlers to log
    ch.setFormatter(logging.Formatter('%(message)s',datefmt='%H:%M:%S'))    # add the handlers to log
    log.addHandler(ch)
    #log.info("start logging in distance_from_picture: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    # do something
    for f in args.file:
        log.debug("file: %s" % f)
        pic = PIL.Image.open(f)
        if args.showimage > 0:
            pic.show()
        hist = pic.histogram() # hist is a list
        hsum = list(numpy.array(pic).sum(1)) # horizontal sums
        vsum = list(numpy.array(pic).sum(0)) # vertical sums
        if (args.smooth > 1) or (args.smooth == -1): # smooth
            if args.smooth == -1:
                si = max(1,pic.size[0]/100) # smooth intervall length
            else:
                si = args.smooth # smooth intervall length
            hsumn = list(range(len(hsum)))
            for i in range(len(hsum)): # all hsum values
                s = 0.0
                for j in range(si): # smooth over si values
                    jj = j - si/2
                    if (0 <= i+jj) and (i+jj <len(hsum)):
                        s += hsum[i+jj]
                    else:
                        s += hsum[i]
                hsumn[i] = s / si
            hsum = hsumn
            if args.smooth == -1:
                si = max(1,pic.size[1]/100) # smooth intervall length
            else:
                si = args.smooth # smooth intervall length
            vsumn = list(range(len(vsum)))
            for i in range(len(vsum)): # all vsum values
                s = 0.0
                for j in range(si): # smooth over si values
                    jj = j - si/2
                    if (0 <= i+jj) and (i+jj <len(vsum)):
                        s += vsum[i+jj]
                    else:
                        s += vsum[i]
                vsumn[i] = s / si
            vsum = vsumn
        totalbrightness = sum(hsum)
        m = (max(vsum)+min(vsum))/2.0
        vdownindizes = []
        vupindizes = []
        for i in range(len(vsum)-1): # all vsum values
            if (vsum[i] > m) and (vsum[i+1] < m):
                vdownindizes += [i]
            elif (vsum[i] < m) and (vsum[i+1] > m):
                vupindizes += [i]
        if (0 < len(vdownindizes)) and (0 < len(vupindizes)):
            hdistance = (args.xf*len(vupindizes)*pic.size[0]/(vupindizes[-1]-vupindizes[0]) + args.xf*len(vupindizes)*pic.size[0]/(vdownindizes[-1]-vdownindizes[0])) / 2.0
        else:
            hdistance = -1
        hm = (max(hsum)+min(hsum))/2.0
        hdownindizes = []
        hupindizes = []
        for i in range(len(hsum)-1): # all hsum values
            if (hsum[i] > hm) and (hsum[i+1] < hm):
                hdownindizes += [i]
            elif (hsum[i] < hm) and (hsum[i+1] > hm):
                hupindizes += [i]
        if (0 < len(hdownindizes)) and (0 < len(hupindizes)):
            vdistance = (args.yf*len(hupindizes)*pic.size[1]/(hdownindizes[-1]-hdownindizes[0]) + args.yf*len(hupindizes)*pic.size[1]/(hupindizes[-1]-hupindizes[0])) / 2.0
        else:
            vdistance = -1
        log.debug("down: %d x %d   up: %d x %d" % (len(vdownindizes),len(hdownindizes),len(vupindizes),len(hupindizes)))
        log.info("%s: %d x %d: %f mm x %f mm" % (f,pic.size[0],pic.size[1],hdistance,vdistance))
        

if __name__ == "__main__":
    main()
