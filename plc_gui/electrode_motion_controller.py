"""class for electrode motion controller (zpos)

Author: Daniel Mohr
Date: 2013-02-04
"""

import os
import os.path
import re
import serial
import string
import sys
import tkinter
import time

    
class electrode_motion_controller():
    """class for electrode motion controller (zpos)

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
        self.devicename = self.config.values.get('electrode motion controller','devicename')
        self.boudrate = int(self.config.values.get('electrode motion controller','boudrate'))
        databits = [None,None,None,None,None,serial.FIVEBITS,serial.SIXBITS,serial.SEVENBITS,serial.EIGHTBITS]
        self.databits = databits[int(self.config.values.get('electrode motion controller','databits'))]
        self.parity = serial.PARITY_NONE
        if self.config.values.get('electrode motion controller','stopbits') == "1":
            self.stopbits = serial.STOPBITS_ONE
        elif self.config.values.get('electrode motion controller','stopbits') == "1.5":
            self.stopbits = serial.STOPBITS_ONE_POINT_FIVE
        elif self.config.values.get('electrode motion controller','stopbits') == "2":
            self.stopbits = serial.STOPBITS_TWO
            
        self.readtimeout = float(self.config.values.get('electrode motion controller','readtimeout'))
        self.writetimeout = float(self.config.values.get('electrode motion controller','writetimeout'))
        self.device = serial.Serial(port=None,
                                    baudrate=self.boudrate,
                                    bytesize=self.databits,
                                    parity=self.parity,
                                    stopbits=self.stopbits,
                                    timeout=self.readtimeout,
                                    writeTimeout=self.writetimeout)
        self.device.port = self.devicename
        self.T_off = self.config.values.get('electrode motion controller','T_off')
        self.update_intervall = self.config.values.get('electrode motion controller','update_intervall')
        if self.config.values.get('electrode motion controller','disable_lower_guard_ring') == "1":
            self.disabled_lower_guard_ring = True
        else:
            self.disabled_lower_guard_ring = False
        self.setpoint = dict()
        self.setpoint['upper guard ring'] = None
        self.setpoint['lower guard ring'] = None
        self.setpoint['upper electrode'] = None
        self.setpoint['lower electrode'] = None
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
        self.setpoint['upper guard ring'] = None
        self.setpoint['lower guard ring'] = None
        self.setpoint['upper electrode'] = None
        self.setpoint['lower electrode'] = None

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
            if (self.setpoint['upper guard ring'] != None and
                self.setpoint['upper guard ring'] != 0):
                # move upper guard
                steps = int(self.setpoint['upper guard ring'])
                if steps < 0:
                    cmd = "k" # upper guard ring: down
                    self.setpoint['upper guard ring'] = self.setpoint['upper guard ring'] + 1
                elif steps > 0:
                    cmd = "K" # upper guard ring: up
                    self.setpoint['upper guard ring'] = self.setpoint['upper guard ring'] - 1
                self.debugprint("upper guard ring %d steps up/down" % steps)
                write2dev_string = "%s%s" % (write2dev_string,cmd)
                write2dev = True
            elif (self.setpoint['upper guard ring'] != None and
                self.setpoint['upper guard ring'] == 0):
                self.setpoint['upper guard ring'] = None
            if self.disabled_lower_guard_ring:
                self.setpoint['lower guard ring'] = None
            elif (self.setpoint['lower guard ring'] != None and
                self.setpoint['lower guard ring'] != 0):
                # move lower guard
                steps = int(self.setpoint['lower guard ring'])
                if steps < 0:
                    cmd = "M" # lower guard ring down
                    self.setpoint['lower guard ring'] = self.setpoint['lower guard ring'] + 1
                elif steps > 0:
                    cmd = "m" # lower guard ring up
                    self.setpoint['lower guard ring'] = self.setpoint['lower guard ring'] - 1
                self.debugprint("lower guard ring %d steps up/down" % steps)
                write2dev_string = "%s%s" % (write2dev_string,cmd)
                write2dev = True
            elif (self.setpoint['lower guard ring'] != None and
                self.setpoint['lower guard ring'] == 0):
                self.setpoint['lower guard ring'] = None
            if (self.setpoint['upper electrode'] != None and
                self.setpoint['upper electrode'] != 0):
                # move upper electrode
                steps = int(self.setpoint['upper electrode'])
                if steps < 0:
                    cmd = "l" # upper electrode down
                    self.setpoint['upper electrode'] = self.setpoint['upper electrode'] + 1
                elif steps > 0:
                    cmd = "L" # upper electrode up
                    self.setpoint['upper electrode'] = self.setpoint['upper electrode'] - 1
                self.debugprint("upper electrode %d steps up/down" % steps)
                write2dev_string = "%s%s" % (write2dev_string,cmd)
                write2dev = True
            elif (self.setpoint['upper electrode'] != None and
                self.setpoint['upper electrode'] == 0):
                self.setpoint['upper electrode'] = None
            if (self.setpoint['lower electrode'] != None and
                self.setpoint['lower electrode'] != 0):
                # move lower electrode
                steps = int(self.setpoint['lower electrode'])
                if steps < 0:
                    cmd = "N" # lower electrode down
                    self.setpoint['lower electrode'] = self.setpoint['lower electrode'] + 1
                elif steps > 0:
                    cmd = "n" # lower electrode up
                    self.setpoint['lower electrode'] = self.setpoint['lower electrode'] - 1
                self.debugprint("lower electrode %d steps up/down" % steps)
                write2dev_string = "%s%s" % (write2dev_string,cmd)
                write2dev = True
            elif (self.setpoint['lower electrode'] != None and
                self.setpoint['lower electrode'] == 0):
                self.setpoint['lower electrode'] = None
            l=None
            try: l = self.device.read(self.readbytes)
            except: pass
            if l:
                self.debugprint(l,prefix="[electrode motion received] ",t=1)
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
            if write2dev:
                t = self.T_off
            else:
                t = self.update_intervall
            self.updateid = self.start_button.after(t,func=self.update) # call after ... milliseconds

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
        self.debugprint("start electrode motion controlling on port %s" % self.devicename)
        try:
            self.device.open()
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
            self.debugprint("stop electrode motion controlling on port %s" % self.devicename)
        else:
            self.actualvalue['connect'] = False
            self.setpoint['connect'] = False
