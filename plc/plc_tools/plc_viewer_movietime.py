"""movietime for plc_viewer

Author: Daniel Mohr
Date: 2012-09-28
"""

import time

class movietime():
    def __init__(self,timestamp_min,timestamp_max,timeratefactor):
        self.timestamp_min = timestamp_min
        self.timestamp_max = timestamp_max
        self.timeratefactor = timeratefactor
        self.status = "stop"
        self.offset = time.time()
        self.time = self.timestamp_min
    def setstatus(self,s):
        # possible status: stop, play, yalp
        if self.status != s:
            a = self.gettime()
            self.time = a
            if (s == "play") or (s == "yalp"):
                self.offset = time.time()
            self.status = s
    def getstatus(self):
        return self.status
    def gettime(self):
        if self.status == "stop":
            r = self.time
        elif self.status == "play":
            r = min(max(self.timestamp_min,self.time + self.timeratefactor*(time.time()-self.offset)),self.timestamp_max)
        elif self.status == "yalp":
            r = min(max(self.timestamp_min,self.time - self.timeratefactor*(time.time()-self.offset)),self.timestamp_max)
        return r
    def tunnel(self,step):
        self.time = min(max(self.timestamp_min,self.time + step),self.timestamp_max)
