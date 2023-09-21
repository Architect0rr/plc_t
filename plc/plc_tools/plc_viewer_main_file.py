"""main_file for plc_viewer

Author: Daniel Mohr
Date: 2012-10-10, 2013-04-09
"""

import re
import zipfile
import sys

from plc_tools.plc_viewer_gui import gui

def main_file(log,args):
    log.debug("start main_file")
    f = args.dir
    # create database
    r = re.findall("([^.]+)[0-9]{3}.zip",f)
    if r:
        cameras_file_prefix = r[0]
    else:
        log.error("\"%s\" is not a zip file!" % args.dir)
        sys.exit(1)
    timestamps = []
    timestamps += [[]]
    archives = []
    archives += [f]
    zips = zipfile.ZipFile(f,"r")
    lines = zips.read("timestamps.txt").split("\n")
    zips.close()
    for l in lines:
        if len(l) > 1:
            [fn,ts] = l.split("\t")
            timestamps[0] += [[float(ts),f,fn]]
    timestamps[0] = sorted(timestamps[0], key=lambda a: a[0])
    timestamp_min = timestamps[0][0][0]
    timestamp_max = timestamps[0][0][0]
    for i in range(len(timestamps)):
        for j in range(len(timestamps[i])):
            if timestamps[i][j][0] < timestamp_min:
                timestamp_min = timestamps[i][j][0]
            if timestamps[i][j][0] > timestamp_max:
                timestamp_max = timestamps[i][j][0]
    log.debug("frames from %f to %f" % (timestamp_min,timestamp_max))
    t = gui(log=log,timestamps=timestamps,camcolumn=args.camcolumn,timeratefactor=args.timeratefactor,scale=args.scale,absolutscale=args.absolutscale,timestamp_min=timestamp_min,timestamp_max=timestamp_max,minupdateinterval1=3,maxupdateinterval1=14,minupdateinterval2=1,maxupdateinterval2=7,create_info_graphics=args.create_info_graphics,gamma=args.gamma)
    t.main_window.mainloop()
    t.destroy()
    log.debug("exit main_file")
