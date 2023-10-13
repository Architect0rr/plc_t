#!/usr/bin/python
# Author: Daniel Mohr
# Date: 2013-02-13, 2014-07-22

__communication_statistic_date__ = "2014-07-22"

import argparse
import numpy
import os
import re
import sys
import time

def main():
    help = ""
    parser = argparse.ArgumentParser(
        description='communication_statistic.py creates statistic over the communication log of a multi_purpose_controller_server',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__communication_statistic_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-file',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='file',
                        help='Gives the file name of the log.',
                        metavar='f')
    parser.add_argument('-problems',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='problems',
                        help='By specifying this flag problems will be searched.')
    parser.add_argument('-time',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='time',
                        help='By specifying this flag a statistic about time differences between communications will be build.')
    parser.add_argument('-bins',
                        nargs=1,
                        default=10,
                        type=int,
                        required=False,
                        dest='bins',
                        help='Set n bins for histogram of the time statistic.',
                        metavar='n')
    parser.add_argument('-min',
                        nargs=1,
                        default="default",
                        type=str,
                        required=False,
                        dest='hmin',
                        help='Sets the minimum of the range of the histogram of the time statistic. default: default',
                        metavar='s')
    parser.add_argument('-max',
                        nargs=1,
                        default="default",
                        type=str,
                        required=False,
                        dest='hmax',
                        help='Sets the maximum of the range of the histogram of the time statistic. default: default',
                        metavar='s')
    args = parser.parse_args()
    if not isinstance(args.file,str):
        args.file = args.file[0]
    if not isinstance(args.problems,bool):
        args.problems = args.problems[0]
    if not isinstance(args.time,bool):
        args.time = args.time[0]
    if not isinstance(args.bins,int):
        args.bins = args.bins[0]
    if not isinstance(args.hmin,str):
        args.hmin = args.hmin[0]
    if not isinstance(args.hmax,str):
        args.hmax = args.hmax[0]
    if not os.path.isfile(args.file):
        print(("File \"%s\" does not exists!" % args.file))
        sys.exit(1)
    if args.problems or args.time:
        created = -1
        if args.time:
            tdi = 0
            ddn = 1000000
            data = numpy.empty((ddn,),dtype=float)
        with open(args.file,'r') as file:
            line = file.readline()
            while line:
                r = re.findall("([0-9\.]+) ([^\n]+)",line)
                #print "line",line
                if r:
                    last_created = created
                    created = float(r[0][0])
                    message = r[0][1]
                    if ((args.problems) and re.findall("problem",message)):
                        print(("%s.%03d: %s" %
                              (time.strftime("%Y-%m-%dT%H:%M:%S",
                                             time.localtime(created)),
                               round(created%1*1000),message)))
                    if (args.time and
                        (last_created != -1) and
                        (re.findall("SENDRECEIVE:",message) or
                         re.findall("Transmitted:",message))):
                        td = created - last_created
                        if tdi >= data.shape[0]:
                            data = numpy.append(data,numpy.empty((ddn,),dtype=float))
                        data[tdi] = td
                        tdi += 1
                line = file.readline()
        file.close()
    if args.time:
        #print "data",data
        data=numpy.resize(data,(tdi,))
        #print "data",data
        print(("number of communications: %d" % (tdi+1)))
        print("time difference:")
        print((" minimum: %f" % numpy.amin(data)))
        print((" maximum: %f" % numpy.amax(data)))
        print((" arithmetic mean: %f" % numpy.mean(data)))
        print((" standard deviation: %f" % numpy.std(data)))
        print((" variance: %f" % numpy.var(data)))
        n = 1000
        n = 10
        n = args.bins
        #h = numpy.histogram(data,bins=n)
        #h = numpy.histogram(data,bins=n,range=(0.064,0.077))
        #h = numpy.histogram(data,bins=n,range=(0.0643,0.082))
        #h = numpy.histogram(data,bins=n,range=(0.0643,0.090))
        hmin = numpy.amin(data)
        if not args.hmin == "default":
            try:
                hmin = float(args.hmin)
            except: pass
        hmax = min(2*hmin,numpy.amax(data))
        if not args.hmax == "default":
            try:
                hmax = float(args.hmax)
            except: pass
        h = numpy.histogram(data,bins=n,range=(hmin,hmax))
        print(" histogram:")
        for i in range(n):
            print(("  %f %d" % (h[1][i],h[0][i])))

if __name__ == "__main__":
    main()
