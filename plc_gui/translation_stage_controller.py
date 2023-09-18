"""class for translation stage controller (trinamix_tmcm_351)

Author: Daniel Mohr
Date: 2013-03-05
"""

import os
import os.path
import re
import serial
import string
import sys
import tkinter
import time
    
class translation_stage_controller():
    """class for translation stage controller (trinamix_tmcm_351)

    Author: Daniel Mohr
    Date: 2012-08-27
    """
    def __init__(self,config=None,pw=None,debugprint=None):
        self.readbytes = 4096 # read this number of bytes at a time
        self.readbytes = 16384 # read this number of bytes at a time
        self.debug = True
        self.config = config
        self.padx = self.config.values.get('gui','padx')
        self.pady = self.config.values.get('gui','pady')
        self.pw = pw
        self.debugprint = debugprint
        self.lastupdate = time.time()
        self.device = None
        self.devicename = self.config.values.get('translation stage controller','devicename')
        self.boudrate = int(self.config.values.get('translation stage controller','boudrate'))
        databits = [None,None,None,None,None,serial.FIVEBITS,serial.SIXBITS,serial.SEVENBITS,serial.EIGHTBITS]
        self.databits = databits[int(self.config.values.get('translation stage controller','databits'))]
        self.parity = serial.PARITY_NONE
        if self.config.values.get('translation stage controller','stopbits') == "1":
            self.stopbits = serial.STOPBITS_ONE
        elif self.config.values.get('translation stage controller','stopbits') == "1.5":
            self.stopbits = serial.STOPBITS_ONE_POINT_FIVE
        elif self.config.values.get('translation stage controller','stopbits') == "2":
            self.stopbits = serial.STOPBITS_TWO
            
        self.readtimeout = float(self.config.values.get('translation stage controller','readtimeout'))
        self.writetimeout = int(self.config.values.get('translation stage controller','writetimeout'))
        self.device = serial.Serial(port=None,
                                    baudrate=self.boudrate,
                                    bytesize=self.databits,
                                    parity=self.parity,
                                    stopbits=self.stopbits,
                                    timeout=self.readtimeout,
                                    writeTimeout=self.writetimeout)
        self.device.port = self.devicename
        self.update_intervall = self.config.values.get('translation stage controller','update_intervall')
        self.setpoint = dict()
        self.setpoint['connect'] = False
        self.setpoint['x rel'] = None
        self.setpoint['y rel'] = None
        self.setpoint['z rel'] = None
        self.actualvalue = dict()
        self.actualvalue['connect'] = False
        self.write = self.defaultprint
        # values for the gui
        self.isgui = False
        self.start_button = None
        self.stop_button = None
        self.updateid = None

    def debugprint(self,s):
        if self.debug:
            print(s)
    def defaultprint(self,s):
        if False:
            print(s)

    def set_default_values(self):
        """set default values

        set setpoint[...] to None
        set actualvalue[...] to None
        
        Author: Daniel Mohr
        Date: 2012-08-27
        """
        self.setpoint['x rel'] = None
        self.setpoint['y rel'] = None
        self.setpoint['z rel'] = None

    def update(self,restart=True):
        """if necessary write values self.setpoint to device
        and read them from device to self.actualvalue

        Author: Daniel Mohr
        Date: 2012-08-27
        """
        selfrestart = False
        write2dev = False
        write2dev_string = ""
        if self.actualvalue['connect']:
            selfrestart = True
            if (self.setpoint['x rel'] != None and
                self.setpoint['x rel'] != 0):
                steps = int(self.setpoint['x rel'])
                self.debugprint("translation stage x %d" % steps)
                write2dev_string = "%sAMVP REL,0,%d\r" % (write2dev_string,steps)
                write2dev = True
                self.setpoint['x rel'] = None
            if (self.setpoint['y rel'] != None and
                self.setpoint['y rel'] != 0):
                steps = int(self.setpoint['y rel'])
                self.debugprint("translation stage y %d" % steps)
                write2dev_string = "%sAMVP REL,1,%d\r" % (write2dev_string,steps)
                write2dev = True
                self.setpoint['y rel'] = None
            if (self.setpoint['z rel'] != None and
                self.setpoint['z rel'] != 0):
                steps = int(self.setpoint['z rel'])
                self.debugprint("translation stage z %d" % steps)
                write2dev_string = "%sAMVP REL,2,%d\r" % (write2dev_string,steps)
                write2dev = True
                self.setpoint['z rel'] = None
            l=None
            try: l = self.device.read(self.readbytes)
            except: pass
            if l:
                self.debugprint(l,prefix="[translation stage received] ",t=1)
        if self.setpoint['connect'] != self.actualvalue['connect']:
            if self.setpoint['connect']:
                self.actualvalue['connect'] = True
                self.start()
                self.selfrestart = True
            elif self.setpoint['connect'] == False:
                self.actualvalue['connect'] = False
                self.stop()
                self.selfrestart = False
        elif write2dev:
            print(("write \"%s\"\n" % write2dev_string))
            self.device.write(write2dev_string)
        if restart and selfrestart and self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.start_button.after(self.update_intervall,func=self.update) # call after ... milliseconds

    def gui(self):
        self.isgui = True
        self.start_button = tkinter.Button(self.pw,text="open",command=self.start_request,padx=self.padx,pady=self.pady)
        self.start_button.grid(row=0,column=0)
        self.stop_button = tkinter.Button(self.pw,text="close",command=self.stop_request,state=tkinter.DISABLED,padx=self.padx,pady=self.pady)
        self.stop_button.grid(row=0,column=1)
        self.set_default_values()

    def start_request(self):
        self.setpoint['connect'] = True
        if self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.update()
    def start(self):
        self.debugprint("start translation stage controlling on port %s" % self.devicename)
        try:
            self.device.open()
            self.device.write("\x01\x8b\x00\x00\x00\x00\x00\x00\x8c\r") # 0x018b 0x0000 0x0000 0x0000 0x8c
            self.actualvalue['connect'] = True
            self.setpoint['connect'] = True
            self.debugprint("connect")
        except:
            self.actualvalue['connect'] = False
            self.setpoint['connect'] = False
            self.debugprint("cannot connect")
        if self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.update()
            self.start_button.configure(state=tkinter.DISABLED)
            self.stop_button.configure(state=tkinter.NORMAL)

    def check_buttons(self):
        if self.isgui:
            if self.actualvalue['connect']:
                self.start_button.configure(state=tkinter.DISABLED)
                self.stop_button.configure(state=tkinter.NORMAL)
            else:
                self.start_button.configure(state=tkinter.NORMAL)
                self.stop_button.configure(state=tkinter.DISABLED)


    def stop_request(self):
        self.setpoint['connect'] = False
        if self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.update()
    def stop(self):
        if self.device.isOpen():
            self.device.close()
            self.actualvalue['connect'] = False
            self.setpoint['connect'] = False
            self.debugprint("stop translation stage controlling on port %s" % self.devicename)
        else:
            self.actualvalue['connect'] = False
            self.setpoint['connect'] = False
