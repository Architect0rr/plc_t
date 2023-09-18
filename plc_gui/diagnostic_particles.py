"""gui for Diagnostics/Particles

Author: Daniel Mohr
Date: 2013-01-26
"""

import sys
import string
import os
import os.path
import re
import tkinter

from plc_tools.conversion import *

class diagnostic_particles():
    """gui for Diagnostics/Particles

    Author: Daniel Mohr
    Date: 2012-11-27
    """
    def __init__(self,config=None,pw=None,debugprint=None,controller=None):
        """__init__(self,config=None,pw=None,debugprint=None,controller=None)

        create gui for Diagnostics/Particles

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
        self.laser_frame = tkinter.LabelFrame(pw,text="Laser")
        self.laser_frame.pack()
        self.dispenser_frame = tkinter.LabelFrame(pw,text="Dispenser")
        self.dispenser_frame.pack()
        # Laser
##        self.laser_frame_0 = Tkinter.Frame(pw)
##        self.laser_frame_0.pack()
##        self.laser1_frame = Tkinter.Frame(pw)
##        self.laser1_frame.pack()
##        self.laser2_frame = Tkinter.Frame(pw)
##        self.laser2_frame.pack()
        self.laser_frame_0 = tkinter.Frame(self.laser_frame)
        self.laser_frame_0.grid(column=0,row=0)
        self.laser1_frame = tkinter.Frame(self.laser_frame)
        self.laser1_frame.grid(column=1,row=0)
        self.laser2_frame = tkinter.Frame(self.laser_frame)
        self.laser2_frame.grid(column=1,row=1)
        self.laser_status = tkinter.IntVar()
        self.laser_checkbutton = tkinter.Checkbutton(self.laser_frame_0,text="Laser Power",command=self.laser,variable=self.laser_status,state=tkinter.DISABLED)
        self.laser_checkbutton.grid(row=1,column=0)
        self.laser_status_val = tkinter.StringVar()
        self.laser_status_val_label = tkinter.Label(self.laser_frame_0,textvariable=self.laser_status_val,height=1,width=3)
        self.laser_status_val.set("val")
        self.laser_status_val_label.grid(row=1,column=1)
        # Laser 1
        self.laser1_status = tkinter.IntVar()
        self.laser1_checkbutton = tkinter.Checkbutton(self.laser1_frame,text="Laser 1",command=self.laser1,variable=self.laser1_status,state=tkinter.DISABLED,offvalue=False,onvalue=True)
        self.laser1_checkbutton.grid(column=0,row=0)
        self.laser1_status_val = tkinter.StringVar()
        self.laser1_status_label = tkinter.Label(self.laser1_frame,textvariable=self.laser1_status_val,height=1,width=5)
        self.laser1_status_val.set("val")
        self.laser1_status_label.grid(column=1,row=0)
        self.laser1_set_diode_voltage_val = tkinter.DoubleVar()
        self.laser1_set_diode_voltage_entry = tkinter.Entry(self.laser1_frame,textvariable=self.laser1_set_diode_voltage_val,width=6)
        self.laser1_set_diode_voltage_entry.grid(column=2,row=0)
        self.laser1_set_diode_voltage_button = tkinter.Button(self.laser1_frame,command=self.laser1_set_diode_voltage_command,text="set V",padx=self.padx,pady=self.pady)
        self.laser1_set_diode_voltage_button.grid(column=3,row=0)
        self.laser1_diode_voltage_label1 = tkinter.Label(self.laser1_frame,text="Voltage: ")
        self.laser1_diode_voltage_label1.grid(column=4,row=0)
        self.laser1_diode_voltage_val = tkinter.StringVar()
        self.laser1_diode_voltage_label = tkinter.Label(self.laser1_frame,textvariable=self.laser1_diode_voltage_val,height=1,width=8)
        self.laser1_diode_voltage_val.set("0")
        self.laser1_diode_voltage_label.grid(column=5,row=0)
        self.laser1_diode_current_label1 = tkinter.Label(self.laser1_frame,text="Current: ")
        self.laser1_diode_current_label1.grid(column=6,row=0)
        self.laser1_diode_current_val = tkinter.StringVar()
        self.laser1_diode_current_label = tkinter.Label(self.laser1_frame,textvariable=self.laser1_diode_current_val,height=1,width=11)
        self.laser1_diode_current_val.set("0")
        self.laser1_diode_current_label.grid(column=7,row=0)
        self.laser1_diode_power_label1 = tkinter.Label(self.laser1_frame,text="Power: ")
        self.laser1_diode_power_label1.grid(column=8,row=0)
        self.laser1_diode_power_val = tkinter.StringVar()
        self.laser1_diode_power_label = tkinter.Label(self.laser1_frame,textvariable=self.laser1_diode_power_val,height=1,width=9)
        self.laser1_diode_power_val.set("0")
        self.laser1_diode_power_label.grid(column=9,row=0)
        # Laser 2
        self.laser2_status = tkinter.IntVar()
        self.laser2_checkbutton = tkinter.Checkbutton(self.laser2_frame,text="Laser 2",command=self.laser2,variable=self.laser2_status,state=tkinter.DISABLED,offvalue=False,onvalue=True)
        self.laser2_checkbutton.grid(column=0,row=0)
        self.laser2_status_val = tkinter.StringVar()
        self.laser2_status_label = tkinter.Label(self.laser2_frame,textvariable=self.laser2_status_val,height=1,width=5)
        self.laser2_status_val.set("val")
        self.laser2_status_label.grid(column=1,row=0)
        self.laser2_set_diode_voltage_val = tkinter.DoubleVar()
        self.laser2_set_diode_voltage_entry = tkinter.Entry(self.laser2_frame,textvariable=self.laser2_set_diode_voltage_val,width=6)
        self.laser2_set_diode_voltage_entry.grid(column=2,row=0)
        self.laser2_set_diode_voltage_button = tkinter.Button(self.laser2_frame,command=self.laser2_set_diode_voltage_command,text="set V",padx=self.padx,pady=self.pady)
        self.laser2_set_diode_voltage_button.grid(column=3,row=0)
        self.laser2_diode_voltage_label1 = tkinter.Label(self.laser2_frame,text="Voltage: ")
        self.laser2_diode_voltage_label1.grid(column=4,row=0)
        self.laser2_diode_voltage_val = tkinter.StringVar()
        self.laser2_diode_voltage_label = tkinter.Label(self.laser2_frame,textvariable=self.laser2_diode_voltage_val,height=1,width=8)
        self.laser2_diode_voltage_val.set("0")
        self.laser2_diode_voltage_label.grid(column=5,row=0)
        self.laser2_diode_current_label1 = tkinter.Label(self.laser2_frame,text="Current: ")
        self.laser2_diode_current_label1.grid(column=6,row=0)
        self.laser2_diode_current_val = tkinter.StringVar()
        self.laser2_diode_current_label = tkinter.Label(self.laser2_frame,textvariable=self.laser2_diode_current_val,height=1,width=11)
        self.laser2_diode_current_val.set("0")
        self.laser2_diode_current_label.grid(column=7,row=0)
        self.laser2_diode_power_label1 = tkinter.Label(self.laser2_frame,text="Power: ")
        self.laser2_diode_power_label1.grid(column=8,row=0)
        self.laser2_diode_power_val = tkinter.StringVar()
        self.laser2_diode_power_label = tkinter.Label(self.laser2_frame,textvariable=self.laser2_diode_power_val,height=1,width=9)
        self.laser2_diode_power_val.set("0")
        self.laser2_diode_power_label.grid(column=9,row=0)
        # dispensers
        self.dispenser_frame_0 = tkinter.Frame(self.dispenser_frame)
        self.dispenser_frame_0.pack()
        # values for dispensers
        self.dispensers = dict()
        dispensoren = ['dispenser1','dispenser2','dispenser3','dispenser4']
        self.dispensoren = []
        for d in dispensoren:
            self.dispensers[d] = dict()
            if self.config.values.get(d,'controller') == "-1":
                self.dispensers[d]['exists'] = False
            else:
                self.dispensers[d]['exists'] = True
                self.dispensoren = self.dispensoren + [d]
                self.dispensers[d]['gui'] = dict()
                if d=="dispenser1":
                    self.dispensers[d]['gui']['cmd'] = self.shake_dispenser1
                elif d=="dispenser2":
                    self.dispensers[d]['gui']['cmd'] = self.shake_dispenser2
                elif d=="dispenser3":
                    self.dispensers[d]['gui']['cmd'] = self.shake_dispenser3
                elif d=="dispenser4":
                    self.dispensers[d]['gui']['cmd'] = self.shake_dispenser4
                self.dispensers[d]['controller'] = self.config.values.get(d,'controller')
                self.dispensers[d]['port'] = self.config.values.get(d,'port')
                self.dispensers[d]['channel'] = self.config.values.get(d,'channel')
                self.dispensers[d]['shakes'] = self.config.values.get(d,'shakes')
                self.dispensers[d]['Toff'] = self.config.values.get(d,'Toff')
                self.dispensers[d]['Ton'] = self.config.values.get(d,'Ton')
        # create gui for dispensers
        for d in self.dispensoren:
            if self.dispensers[d]['exists']:
                self.dispensers[d]['gui']['frame'] = tkinter.Frame(self.dispenser_frame_0)
                self.dispensers[d]['gui']['frame'].pack()
                self.dispensers[d]['gui']['label1'] = tkinter.Label(self.dispensers[d]['gui']['frame'],text="%s: " % d)
                self.dispensers[d]['gui']['label1'].grid(column=0,row=0)
                self.dispensers[d]['gui']['shakes'] = tkinter.IntVar()
                self.dispensers[d]['gui']['shakes'].set(int(self.dispensers[d]['shakes']))
                self.dispensers[d]['gui']['shakes_entry'] = tkinter.Entry(self.dispensers[d]['gui']['frame'],textvariable=self.dispensers[d]['gui']['shakes'],width=3,state=tkinter.DISABLED)
                self.dispensers[d]['gui']['shakes_entry'].grid(column=1,row=0)
                self.dispensers[d]['gui']['shakes_label'] = tkinter.Label(self.dispensers[d]['gui']['frame'],text="shakes. ")
                self.dispensers[d]['gui']['shakes_label'].grid(column=2,row=0)
                self.dispensers[d]['gui']['Ton'] = tkinter.IntVar()
                self.dispensers[d]['gui']['Ton'].set(int(self.dispensers[d]['Ton']))
                self.dispensers[d]['gui']['Ton_label1'] = tkinter.Label(self.dispensers[d]['gui']['frame'],text="T_on: ")
                self.dispensers[d]['gui']['Ton_label1'].grid(column=3,row=0)
                self.dispensers[d]['gui']['Ton_entry'] = tkinter.Entry(self.dispensers[d]['gui']['frame'],textvariable=self.dispensers[d]['gui']['Ton'],width=5,state=tkinter.DISABLED)
                self.dispensers[d]['gui']['Ton_entry'].grid(column=4,row=0)
                self.dispensers[d]['gui']['Ton_label'] = tkinter.Label(self.dispensers[d]['gui']['frame'],text="ms. ")
                self.dispensers[d]['gui']['Ton_label'].grid(column=5,row=0)
                self.dispensers[d]['gui']['Toff'] = tkinter.IntVar()
                self.dispensers[d]['gui']['Toff'].set(int(self.dispensers[d]['Toff']))
                self.dispensers[d]['gui']['Toff_label1'] = tkinter.Label(self.dispensers[d]['gui']['frame'],text="T_off: ")
                self.dispensers[d]['gui']['Toff_label1'].grid(column=6,row=0)
                self.dispensers[d]['gui']['Toff_entry'] = tkinter.Entry(self.dispensers[d]['gui']['frame'],textvariable=self.dispensers[d]['gui']['Toff'],width=5,state=tkinter.DISABLED)
                self.dispensers[d]['gui']['Toff_entry'].grid(column=7,row=0)
                self.dispensers[d]['gui']['Toff_label'] = tkinter.Label(self.dispensers[d]['gui']['frame'],text="ms. ")
                self.dispensers[d]['gui']['Toff_label'].grid(column=8,row=0)

                self.dispensers[d]['gui']['shake'] = tkinter.Button(self.dispensers[d]['gui']['frame'],command=self.dispensers[d]['gui']['cmd'],state=tkinter.DISABLED,text="do the shake",padx=self.padx,pady=self.pady)
                self.dispensers[d]['gui']['shake'].grid(column=9,row=0)

    def shake_dispenser1(self):
        self.shake_dispenser('dispenser1')
    def shake_dispenser2(self):
        self.shake_dispenser('dispenser2')
    def shake_dispenser3(self):
        self.shake_dispenser('dispenser3')
    def shake_dispenser4(self):
        self.shake_dispenser('dispenser4')

    def shake_dispenser(self,d=None):
        if d!=None:
            if self.controller[self.dispensers[d]['controller']].isconnect:
                # init
                err = False
                try:
                    self.dispensers[d]['shakes'] = self.dispensers[d]['gui']['shakes'].get()
                except:
                    err = True
                try:
                    self.dispensers[d]['Toff'] = self.dispensers[d]['gui']['Toff'].get()
                except:
                    err = True
                try:
                    self.dispensers[d]['Ton'] = self.dispensers[d]['gui']['Ton'].get()
                except:
                    err = True
                # shake
                if err == False:
                    self.debugprint("shake %s" % d)
##                    self.controller[self.dispensers[d]['controller']].setpoint['shake']['port'] = self.dispensers[d]['port']
##                    self.controller[self.dispensers[d]['controller']].setpoint['shake']['channel'] = self.dispensers[d]['channel']
##                    self.controller[self.dispensers[d]['controller']].setpoint['shake']['n'] = self.dispensers[d]['shakes']
##                    self.controller[self.dispensers[d]['controller']].setpoint['shake']['toff'] = self.dispensers[d]['Toff']
##                    self.controller[self.dispensers[d]['controller']].setpoint['shake']['ton'] = self.dispensers[d]['Ton']
##                    self.controller[self.dispensers[d]['controller']].setpoint['shake']['shake'] = True
                    #print "controller",self.controller[self.dispensers[d]['controller']].setpoint
                    ctr = self.dispensers[d]['controller']
                    self.controller[ctr].lock.acquire() # lock
                    self.controller[ctr].setpoint['dispenser']['port'] = self.dispensers[d]['port']
                    self.controller[ctr].setpoint['dispenser']['channel'] = int(self.dispensers[d]['channel'])
                    self.controller[ctr].setpoint['dispenser']['n'] = int(self.dispensers[d]['shakes'])
                    self.controller[ctr].setpoint['dispenser']['toff'] = float(self.dispensers[d]['Toff'])/1000.0
                    self.controller[ctr].setpoint['dispenser']['ton'] = float(self.dispensers[d]['Ton'])/1000.0
                    self.controller[ctr].setpoint['dispenser']['shake'] = True
                    self.controller[ctr].lock.release() # release the lock
                    self.dispensers[d]['gui']['shake'].flash()
                    self.controller[ctr].update()
                    self.dispensers[d]['gui']['shake'].flash()

    def laser(self):
        if self.laser_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch laser power to %s" % b2onoff(s))
        ctr = self.config.values.get('laser','laser_power_status_controller')
        self.controller[ctr].lock.acquire() # lock
        self.controller[ctr].setpoint[self.config.values.get('laser','laser_power_status_port')][self.config.values.getint('laser','laser_power_status_channel')] = s
        self.controller[ctr].lock.release() # release the lock

    def laser1(self):
        if self.laser1_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch laser1 power to %s" % b2onoff(s))
        ctr = self.config.values.get('laser','laser1_power_status_controller')
        self.controller[ctr].lock.acquire() # lock
        self.controller[ctr].setpoint[self.config.values.get('laser','laser1_power_status_port')][self.config.values.getint('laser','laser1_power_status_channel')] = s
        self.controller[ctr].lock.release() # release the lock

    def laser1_set_diode_voltage_command(self):
        # X = 0 ... 10 V
        try:
            v = float(self.laser1_set_diode_voltage_val.get())
        except:
            self.laser1_set_diode_voltage_val.set("ERROR")
            return
        ctr = self.config.values.get('laser','laser1_diode_voltage_controller')
        port = self.config.values.get('laser','laser1_diode_voltage_port')
        channel = self.config.values.getint('laser','laser1_diode_voltage_channel')
        v = max(0.0,min(v,10.0)) # voltage from user
        self.controller[ctr].lock.acquire() # lock
        try:
            self.controller[ctr].setpoint[port][channel] = v
            self.debugprint("set diode voltage from laser 1 to %.2f" % v)
            self.laser1_set_diode_voltage_val.set(round(v,2))
        except:
            try:
                self.controller[ctr].setpoint[port] = v
                self.debugprint("set diode voltage from laser 1 to %.2f" % v)
                self.laser1_set_diode_voltage_val.set(round(v,2))
            except:
                self.laser1_set_diode_voltage_val.set("ERROR")
        self.controller[ctr].lock.release() # release the lock

    def laser2(self):
        if self.laser2_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch laser2 power to %s" % b2onoff(s))
        ctr = self.config.values.get('laser','laser2_power_status_controller')
        self.controller[ctr].lock.acquire() # lock
        self.controller[ctr].setpoint[self.config.values.get('laser','laser2_power_status_port')][self.config.values.getint('laser','laser2_power_status_channel')] = s
        self.controller[ctr].lock.release() # release the lock

    def laser2_set_diode_voltage_command(self):
        # X = 0 ... 10 V
        try:
            v = float(self.laser2_set_diode_voltage_val.get())
        except:
            self.laser2_set_diode_voltage_val.set("ERROR")
            return
        ctr = self.config.values.get('laser','laser2_diode_voltage_controller')
        port = self.config.values.get('laser','laser2_diode_voltage_port')
        channel = self.config.values.getint('laser','laser2_diode_voltage_channel')
        v = max(0.0,min(v,10.0)) # voltage from user
        self.controller[ctr].lock.acquire() # lock
        try:
            self.controller[ctr].setpoint[port][channel] = v
            self.debugprint("set diode voltage from laser 2 to %.2f" % v)
            self.laser2_set_diode_voltage_val.set(round(v,2))
        except:
            try:
                self.controller[ctr].setpoint[port] = v
                self.debugprint("set diode voltage from laser 2 to %.2f" % v)
                self.laser2_set_diode_voltage_val.set(round(v,2))
            except:
                self.laser2_set_diode_voltage_val.set("ERROR")
        self.controller[ctr].lock.release() # release the lock

    def update(self):
        """update every dynamic read values"""
        self.laser_status_val.set(b2onoff(self.controller[self.config.values.get('laser','laser_power_status_controller')].actualvalue[self.config.values.get('laser','laser_power_status_port')][self.config.values.getint('laser','laser_power_status_channel')]))
        self.laser1_status_val.set(b2onoff(self.controller[self.config.values.get('laser','laser1_power_status_controller')].actualvalue[self.config.values.get('laser','laser1_power_status_port')][self.config.values.getint('laser','laser1_power_status_channel')]))
        self.laser2_status_val.set(b2onoff(self.controller[self.config.values.get('laser','laser2_power_status_controller')].actualvalue[self.config.values.get('laser','laser2_power_status_port')][self.config.values.getint('laser','laser2_power_status_channel')]))
        self.laser1_diode_voltage_val.set("%.2f V" % (self.controller[self.config.values.get('laser','laser1_diode_voltage_controller')].actualvalue[self.config.values.get('laser','laser1_diode_voltage_port')][self.config.values.getint('laser','laser1_diode_voltage_channel')]))
        v = self.controller[self.config.values.get('laser','laser1_diode_current_controller')].actualvalue[self.config.values.get('laser','laser1_diode_current_port')][self.config.values.getint('laser','laser1_diode_current_channel')]
        i = v / float(self.config.values.get('laser','R')) # I = U / R
        if i < float(self.config.values.get('laser','I_offset')):
            p = 0.0
        else:
            p = 1000.0 * (i - float(self.config.values.get('laser','I_offset'))) * float(self.config.values.get('laser','I_scale'))
        i = 1000.0 * i
        self.laser1_diode_current_val.set("%.2f mA" % i)
        self.laser1_diode_power_val.set("%.2f mW" % p)
        self.laser2_diode_voltage_val.set("%.2f V" % (self.controller[self.config.values.get('laser','laser2_diode_voltage_controller')].actualvalue[self.config.values.get('laser','laser2_diode_voltage_port')][self.config.values.getint('laser','laser2_diode_voltage_channel')]))
        v = self.controller[self.config.values.get('laser','laser2_diode_current_controller')].actualvalue[self.config.values.get('laser','laser2_diode_current_port')][self.config.values.getint('laser','laser2_diode_current_channel')]
        i = v / float(self.config.values.get('laser','R')) # I = U / R
        if i < float(self.config.values.get('laser','I_offset')):
            p = 0.0
        else:
            p = 1000.0 * (i - float(self.config.values.get('laser','I_offset'))) * float(self.config.values.get('laser','I_scale'))
        i = 1000.0 * i
        self.laser2_diode_current_val.set("%.2f mA" % i)
        self.laser2_diode_power_val.set("%.2f mW" % p)
  
    def check_buttons(self):
        if self.controller['dc'].isconnect:
            self.laser_checkbutton.configure(state=tkinter.NORMAL)
            for d in self.dispensoren:
                if self.dispensers[d]['exists']:
                    self.dispensers[d]['gui']['shake'].configure(state=tkinter.NORMAL)
                    self.dispensers[d]['gui']['shakes_entry'].configure(state=tkinter.NORMAL)
                    self.dispensers[d]['gui']['Ton_entry'].configure(state=tkinter.NORMAL)
                    self.dispensers[d]['gui']['Toff_entry'].configure(state=tkinter.NORMAL)
        else:
            self.laser_checkbutton.configure(state=tkinter.DISABLED)
            for d in self.dispensoren:
                if self.dispensers[d]['exists']:
                    self.dispensers[d]['gui']['shake'].configure(state=tkinter.DISABLED)
                    self.dispensers[d]['gui']['shakes_entry'].configure(state=tkinter.DISABLED)
                    self.dispensers[d]['gui']['Ton_entry'].configure(state=tkinter.DISABLED)
                    self.dispensers[d]['gui']['Toff_entry'].configure(state=tkinter.DISABLED)
        if self.controller['mpc'].isconnect:
            self.laser1_checkbutton.configure(state=tkinter.NORMAL)
            self.laser1_set_diode_voltage_entry.configure(state=tkinter.NORMAL)
            self.laser1_set_diode_voltage_button.configure(state=tkinter.NORMAL)
            self.laser2_checkbutton.configure(state=tkinter.NORMAL)
            self.laser2_set_diode_voltage_entry.configure(state=tkinter.NORMAL)
            self.laser2_set_diode_voltage_button.configure(state=tkinter.NORMAL)
        else:
            self.laser1_checkbutton.configure(state=tkinter.DISABLED)
            self.laser1_set_diode_voltage_entry.configure(state=tkinter.DISABLED)
            self.laser1_set_diode_voltage_button.configure(state=tkinter.DISABLED)
            self.laser2_checkbutton.configure(state=tkinter.DISABLED)
            self.laser2_set_diode_voltage_entry.configure(state=tkinter.DISABLED)
            self.laser2_set_diode_voltage_button.configure(state=tkinter.DISABLED)
