"""gui for controlling gas system

Author: Daniel Mohr
Date: 2013-01-26
"""

import os
import os.path
import re
import string
import sys
import tkinter

from plc_tools.conversion import *

class gas_system():
    """gui for gas system control

    Author: Daniel Mohr
    Date: 2012-11-27
    """
    def __init__(self,config=None,pw=None,debugprint=None,controller=None):
        """__init__(self,config=None,pw=None,debugprint=None)

        create gui for gas system control

        Parameters:
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           debugprint : function
                        function to call for print debug information

        Author: Daniel Mohr
        Date: 2012-08-29
        """
        self.config=config
        self.padx = self.config.values.get('gui','padx')
        self.pady = self.config.values.get('gui','pady')
        self.pw=pw
        self.debugprint=debugprint
        self.controller=controller
        # create gui
        self.pumps_frame = tkinter.Frame(pw)
        self.pumps_frame.pack()
        self.mass_flow_frame = tkinter.LabelFrame(pw,text="Mass Flow Controller")
        self.mass_flow_frame.pack()
        # membran pump
        self.membran_pump_status = tkinter.IntVar()
        self.membran_pump_checkbutton = tkinter.Checkbutton(self.pumps_frame,text="Mem. Pump",command=self.membran_pump,variable=self.membran_pump_status,state=tkinter.DISABLED)
        self.membran_pump_checkbutton.grid(row=2,column=0)
        self.membran_pump_status_val = tkinter.StringVar()
        self.membran_pump_status_val_label = tkinter.Label(self.pumps_frame,textvariable=self.membran_pump_status_val,height=1,width=3)
        self.membran_pump_status_val.set("val")
        self.membran_pump_status_val_label.grid(row=2,column=1)
        #self.membran_pump_checkbutton.deselect()
        #self.membran_pump_checkbutton.select()
        # turbo pump 1
        self.turbo_pump_1_status = tkinter.IntVar()
        self.turbo_pump_1_checkbutton = tkinter.Checkbutton(self.pumps_frame,text="Turbo Pump 1",command=self.turbo_pump_1,variable=self.turbo_pump_1_status,state=tkinter.DISABLED)
        self.turbo_pump_1_checkbutton.grid(row=2,column=2)
        self.turbo_pump_1_status_val = tkinter.StringVar()
        self.turbo_pump_1_status_label = tkinter.Label(self.pumps_frame,textvariable=self.turbo_pump_1_status_val,height=1,width=5)
        self.turbo_pump_1_status_val.set("val")
        self.turbo_pump_1_status_label.grid(row=2,column=3)
        self.turbo_pump_1_rpm_val = tkinter.StringVar()
        self.turbo_pump_1_rpm_label = tkinter.Label(self.pumps_frame,textvariable=self.turbo_pump_1_rpm_val,height=1,width=5)
        self.turbo_pump_1_rpm_val.set("val")
        self.turbo_pump_1_rpm_label.grid(row=2,column=4)
        self.turbo_pump_1_error_val = tkinter.StringVar()
        self.turbo_pump_1_error_label = tkinter.Label(self.pumps_frame,textvariable=self.turbo_pump_1_error_val,height=1,width=25)
        self.turbo_pump_1_error_val.set("val")
        self.turbo_pump_1_error_label.grid(row=2,column=5)
        # turbo pump 2
        self.turbo_pump_2_status = tkinter.IntVar()
        self.turbo_pump_2_checkbutton = tkinter.Checkbutton(self.pumps_frame,text="Turbo Pump 2",command=self.turbo_pump_2,variable=self.turbo_pump_2_status,state=tkinter.DISABLED,offvalue=False,onvalue=True)
        self.turbo_pump_2_checkbutton.grid(row=3,column=2)
        self.turbo_pump_2_status_val = tkinter.StringVar()
        self.turbo_pump_2_status_label = tkinter.Label(self.pumps_frame,textvariable=self.turbo_pump_2_status_val,height=1,width=5)
        self.turbo_pump_2_status_val.set("val")
        self.turbo_pump_2_status_label.grid(row=3,column=3)
        self.turbo_pump_2_rpm_val = tkinter.StringVar()
        self.turbo_pump_2_rpm_label = tkinter.Label(self.pumps_frame,textvariable=self.turbo_pump_2_rpm_val,height=1,width=5)
        self.turbo_pump_2_rpm_val.set("val")
        self.turbo_pump_2_rpm_label.grid(row=3,column=4)
        self.turbo_pump_2_error_val = tkinter.StringVar()
        self.turbo_pump_2_error_label = tkinter.Label(self.pumps_frame,textvariable=self.turbo_pump_2_error_val,height=1,width=25)
        self.turbo_pump_2_error_val.set("val")
        self.turbo_pump_2_error_label.grid(row=3,column=5)
        # Mass Flow Controller
        self.mass_flow_status = tkinter.IntVar()
        self.mass_flow_checkbutton = tkinter.Checkbutton(self.mass_flow_frame,text="ON/OFF",command=self.mass_flow,variable=self.mass_flow_status,state=tkinter.DISABLED,offvalue=False,onvalue=True)
        self.mass_flow_checkbutton.grid(column=0,row=0)
        self.mass_flow_status_val = tkinter.StringVar()
        self.mass_flow_status_label = tkinter.Label(self.mass_flow_frame,textvariable=self.mass_flow_status_val,height=1,width=5)
        self.mass_flow_status_val.set("val")
        self.mass_flow_status_label.grid(column=1,row=0)
        self.mass_flow_set_flow_rate_val = tkinter.StringVar()
        self.mass_flow_set_flow_rate_entry = tkinter.Entry(self.mass_flow_frame,textvariable=self.mass_flow_set_flow_rate_val,width=8)
        self.mass_flow_set_flow_rate_entry.grid(column=2,row=0)
        self.mass_flow_set_flow_rate_button = tkinter.Button(self.mass_flow_frame,command=self.mass_flow_set_flow_rate_command,text="set",padx=self.padx,pady=self.pady)
        self.mass_flow_set_flow_rate_button.grid(column=3,row=0)
        self.mass_flow_flow_rate_val = tkinter.StringVar()
        self.mass_flow_flow_rate_label = tkinter.Label(self.mass_flow_frame,textvariable=self.mass_flow_flow_rate_val,height=1,width=14)
        self.mass_flow_flow_rate_val.set("val")
        self.mass_flow_flow_rate_label.grid(column=4,row=0)

    def membran_pump(self):
        if self.membran_pump_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch membran pump to %s" % b2onoff(s))
        ctr = self.config.values.get('gas system','membran_pump_status_controller')
        self.controller[ctr].lock.acquire() # lock
        self.controller[ctr].setpoint[self.config.values.get('gas system','membran_pump_status_port')][int(self.config.values.get('gas system','membran_pump_status_channel'))] = s
        self.controller[ctr].lock.release() # release the lock

    def turbo_pump_1(self):
        if self.turbo_pump_1_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch turbo pump 1 to %s" % b2onoff(s))
        ctr = self.config.values.get('gas system','turbo_pump_1_status_controller')
        self.controller[ctr].lock.acquire() # lock
        self.controller[ctr].setpoint[self.config.values.get('gas system','turbo_pump_1_status_port')][int(self.config.values.get('gas system','turbo_pump_1_status_channel'))] = s
        self.controller[ctr].lock.release() # release the lock

    def turbo_pump_2(self):
        if self.turbo_pump_2_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch turbo pump 2 to %s" % b2onoff(s))
        ctr = self.config.values.get('gas system','turbo_pump_2_status_controller')
        self.controller[ctr].lock.acquire() # lock
        self.controller[ctr].setpoint[self.config.values.get('gas system','turbo_pump_2_status_port')][int(self.config.values.get('gas system','turbo_pump_2_status_channel'))] = s
        self.controller[ctr].lock.release() # release the lock

    def mass_flow(self):
        if self.mass_flow_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch mass flow controller to %s" % b2onoff(s))
        ctr = self.config.values.get('gas system','mass_flow_controller_status_controller')
        port = self.config.values.get('gas system','mass_flow_controller_status_port')
        channel = int(self.config.values.get('gas system','mass_flow_controller_status_channel'))
        self.controller[ctr].lock.acquire() # lock
        try:
            self.controller[ctr].setpoint[port][channel] = s
        except:
            try:
                self.controller[ctr].setpoint[port] = s
            except:
                pass
        self.controller[ctr].lock.release() # release the lock

    def mass_flow_set_flow_rate_command(self):
        # X = 0 ... 5 V = 0 ... 1 sccm (flow)
        v = self.mass_flow_set_flow_rate_val.get()
        if len(v)>0:
            ctr = self.config.values.get('gas system','mass_flow_controller_set_rate_controller')
            port = self.config.values.get('gas system','mass_flow_controller_set_rate_port')
            channel = int(self.config.values.get('gas system','mass_flow_controller_set_rate_channel'))
            v = float(v) # msccm from user
            vo = min(max(0.0,msccm2volt(v)),5.0) # voltage
            self.debugprint("set flow rate to (%f V, %f msccm)" % (vo,v))
            self.controller[ctr].lock.acquire() # lock
            try:
                self.controller[ctr].setpoint[port][channel] = vo
                self.debugprint("set flow rate to (%f V, %f msccm)" % (vo,v))
                self.mass_flow_set_flow_rate_val.set("%.2f" % volt2msccm(vo))
            except:
                try:
                    self.controller[ctr].setpoint[port][channel] = vo
                    self.debugprint("set flow rate to (%f V, %f msccm)" % (vo,v))
                    self.mass_flow_set_flow_rate_val.set("%f" % volt2msccm(vo))
                except:
                    self.mass_flow_set_flow_rate_val.set("ERROR")
            self.controller[ctr].lock.release() # release the lock

    def update(self):
        """update every dynamic read values"""
        self.membran_pump_status_val.set(b2onoff(self.controller[self.config.values.get('gas system','membran_pump_status_controller')].actualvalue[self.config.values.get('gas system','membran_pump_status_port')][int(self.config.values.get('gas system','membran_pump_status_channel'))]))
        
        self.turbo_pump_1_status_val.set(b2onoff(self.controller[self.config.values.get('gas system','turbo_pump_1_status_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_1_status_port')][int(self.config.values.get('gas system','turbo_pump_1_status_channel'))]))
        self.turbo_pump_2_status_val.set(b2onoff(self.controller[self.config.values.get('gas system','turbo_pump_2_status_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_2_status_port')][int(self.config.values.get('gas system','turbo_pump_2_status_channel'))]))
        # RPM
        #self.turbo_pump_1_rpm_val.set("%d %%" % round(100*self.controller[self.config.values.get('gas system','turbo_pump_1_rpm_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_1_rpm_port')][int(self.config.values.get('gas system','turbo_pump_1_rpm_channel'))]/32767.0))
        self.turbo_pump_1_rpm_val.set("%d %%" % round((self.controller[self.config.values.get('gas system','turbo_pump_1_rpm_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_1_rpm_port')][int(self.config.values.get('gas system','turbo_pump_1_rpm_channel'))]+0.0)*100/10.0))
        #self.turbo_pump_2_rpm_val.set("%d %%" % round(100*self.controller[self.config.values.get('gas system','turbo_pump_2_rpm_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_2_rpm_port')][int(self.config.values.get('gas system','turbo_pump_2_rpm_channel'))]/32767.0))
        self.turbo_pump_2_rpm_val.set("%d %%" % round((self.controller[self.config.values.get('gas system','turbo_pump_2_rpm_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_2_rpm_port')][int(self.config.values.get('gas system','turbo_pump_2_rpm_channel'))]+0.0)*100/10.0))
        # ERROR
        err1 = False
        err2 = False
        if self.controller[self.config.values.get('gas system','turbo_pump_1_error_rotation_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_1_error_rotation_port')][int(self.config.values.get('gas system','turbo_pump_1_error_rotation_channel'))] == False:
            err1 = True
        if self.controller[self.config.values.get('gas system','turbo_pump_1_error_general_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_1_error_general_port')][int(self.config.values.get('gas system','turbo_pump_1_error_general_channel'))] == False:
            err2 = True
        err = ""
        if err1 == True:
            if err2 == True:
                err = "ERROR: general + rotation"
            else:
                err = "ERROR: rotation"
        elif err2 == True:
                err = "ERROR: general"
        self.turbo_pump_1_error_val.set(err)
        err1 = False
        err2 = False
        if self.controller[self.config.values.get('gas system','turbo_pump_2_error_rotation_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_2_error_rotation_port')][int(self.config.values.get('gas system','turbo_pump_2_error_rotation_channel'))] == False:
            err1 = True
        if self.controller[self.config.values.get('gas system','turbo_pump_2_error_general_controller')].actualvalue[self.config.values.get('gas system','turbo_pump_2_error_general_port')][int(self.config.values.get('gas system','turbo_pump_2_error_general_channel'))] == False:
            err2 = True
        if err1 == True:
            if err2 == True:
                err = "ERROR: general + rotation"
            else:
                err = "ERROR: rotation"
        elif err2 == True:
                err = "ERROR: general"
        self.turbo_pump_2_error_val.set(err)
        # measured flow rate
        ctrl = self.config.values.get('gas system','mass_flow_controller_status_controller')
        port = self.config.values.get('gas system','mass_flow_controller_status_port')
        try:
            channel = int(self.config.values.get('gas system','mass_flow_controller_status_channel'))
            w = b2onoff(self.controller[ctrl].actualvalue[port][channel])
            self.mass_flow_status_val.set(w)
        except:
            w = b2onoff(self.controller[ctrl].actualvalue[port])
            self.mass_flow_status_val.set(w)
        ctr = self.config.values.get('gas system','mass_flow_controller_measure_rate_controller')
        port = self.config.values.get('gas system','mass_flow_controller_measure_rate_port')
        channel = int(self.config.values.get('gas system','mass_flow_controller_measure_rate_channel'))
        self.mass_flow_flow_rate_val.set("%.2f msccm" % volt2msccm(self.controller[ctr].actualvalue[port][channel]))
        #self.mass_flow_flow_rate_val.set("%d ADC" % self.controller[ctr].actualvalue[port][channel])
  
    def check_buttons(self):
        if self.controller['dc'].isconnect:
            self.membran_pump_checkbutton.configure(state=tkinter.NORMAL)
        else:
            self.membran_pump_checkbutton.configure(state=tkinter.DISABLED)
        if self.controller['mpc'].isconnect:
            self.turbo_pump_1_checkbutton.configure(state=tkinter.NORMAL)
            self.turbo_pump_2_checkbutton.configure(state=tkinter.NORMAL)
            self.mass_flow_checkbutton.configure(state=tkinter.NORMAL)
            self.mass_flow_set_flow_rate_entry.configure(state=tkinter.NORMAL)
            self.mass_flow_set_flow_rate_button.configure(state=tkinter.NORMAL)
        else:
            self.turbo_pump_1_checkbutton.configure(state=tkinter.DISABLED)
            self.turbo_pump_2_checkbutton.configure(state=tkinter.DISABLED)
            self.mass_flow_checkbutton.configure(state=tkinter.DISABLED)
            self.mass_flow_set_flow_rate_entry.configure(state=tkinter.DISABLED)
            self.mass_flow_set_flow_rate_button.configure(state=tkinter.DISABLED)
