#!/usr/bin/python -BO
# Author: Daniel Mohr
# Date: 2013-02-04, 2014-07-22
"""debug controller for PlasmaLabControl
"""

__plc_date__ = "2014-07-22"
__plc_version__ = __plc_date__

import argparse
import types
import sys
#import string
import os
import os.path
import re
import time
import tkinter
import tkinter.messagebox

import plc_gui
import plc_gui.controller
import plc_gui.read_config_file

def b2i(b):
    if b:
        return 1
    else:
        return 0

def i2b(b):
    if b==1:
        return True
    else:
        return False

def b2s(b):
    if b:
        return "True"
    else:
        return "False"

def s2i(b):
    if b=="True":
        return 1
    else:
        return 0

class gui():
    def __init__(self,args,configname=None):
        self.debug = 1
        self.update_intervall = 500
        self.updateid = None
        # set default values
        self.configs = plc_gui.read_config_file.read_config_file(system_wide_ini_file=args.system_config,user_ini_file=args.config)
        #self.configs = plc_gui.read_config_file.read_config_file()
        self.main_window = tkinter.Tk()
        if (configname != None) and (len(configname)>0):
            self.main_window.title("debug controller for PlasmaLabControl (%s)" % configname)
        else:
            self.main_window.title("debug controller for PlasmaLabControl")
        # create block for controller
        self.controller_window = tkinter.LabelFrame(self.main_window,text="controller")
        self.controller_window.pack()
        self.digital_controller_window = tkinter.LabelFrame(self.controller_window,text="digital controller",labelanchor='n')
        self.digital_controller_window.grid(column=0,row=0)
        self.digital_controller_window_crt = tkinter.Frame(self.digital_controller_window)
        self.digital_controller_window_crt.pack()
        self.digital_controller = plc_gui.controller.digital_controller(config=self.configs,pw=self.digital_controller_window_crt)
        # e. g. self.digital_controller.setpoint['A'][0] = True
        self.multi_purpose_controller_window = tkinter.LabelFrame(self.controller_window,text="multi purpose controller",labelanchor='n')
        self.multi_purpose_controller_window.grid(column=1,row=0)
        self.multi_purpose_controller_window_crt = tkinter.Frame(self.multi_purpose_controller_window)
        self.multi_purpose_controller_window_crt.pack()
        self.multi_purpose_controller = plc_gui.controller.multi_purpose_controller(config=self.configs,pw=self.multi_purpose_controller_window_crt)
        # e. g. self.multi_purpose_controller.setpoint['DAC'][3] = 0
        self.controller = dict()
        self.controller['dc'] = self.digital_controller
        self.controller['mpc'] = self.multi_purpose_controller
        # e. g. self.controller['dc'].actualvalue['A'][1] = False
        self.controller['dc'].gui()
        self.controller['dc'].set_default_values()
        self.controller['mpc'].gui()
        self.controller['mpc'].set_default_values()

        # content
        # digital controller
        self.dcw = tkinter.Frame(self.digital_controller_window)
        self.dcw.pack()
        self.dc_setpoint_frame = tkinter.LabelFrame(self.dcw,text="setpoints")
        self.dc_setpoint_frame.grid(row=0,column=1)
        self.dc_actualvalue_frame = tkinter.LabelFrame(self.dcw,text="actual values")
        self.dc_actualvalue_frame.grid(row=0,column=0)
        
        self.dc_label_setpoint = dict()
        for port in ['A','B','C','D']:
            self.dc_label_setpoint[port] = [None,None,None,None,None,None,None,None]
            for i in range(8):
                self.dc_label_setpoint[port][i] = dict()
                self.dc_label_setpoint[port][i]['val'] = tkinter.IntVar()
                self.dc_label_setpoint[port][i]['label'] = tkinter.Checkbutton(self.dc_setpoint_frame,text="%s %d" % (port,i),command=self.click_dc_setpoint,variable=self.dc_label_setpoint[port][i]['val'])
                self.dc_label_setpoint[port][i]['label'].pack()
                self.dc_label_setpoint[port][i]['label'].deselect()
        self.dc_label_actualvalue = dict()
        for port in ['A','B','C','D']:
            self.dc_label_actualvalue[port] = [None,None,None,None,None,None,None,None]
            for i in range(8):
                self.dc_label_actualvalue[port][i] = dict()
                self.dc_label_actualvalue[port][i]['val'] = tkinter.StringVar()
                self.dc_label_actualvalue[port][i]['val'].set("bool")
                self.dc_label_actualvalue[port][i]['frame'] = tkinter.Frame(self.dc_actualvalue_frame)
                self.dc_label_actualvalue[port][i]['frame'].pack()
                f = self.dc_label_actualvalue[port][i]['frame']
                self.dc_label_actualvalue[port][i]['label1'] = tkinter.Label(f,text="%s %d:" % (port,i))
                self.dc_label_actualvalue[port][i]['label1'].grid(row=0,column=0)
                self.dc_label_actualvalue[port][i]['label2'] = tkinter.Label(f,textvariable=self.dc_label_actualvalue[port][i]['val'],height=1,width=5)
                self.dc_label_actualvalue[port][i]['label2'].grid(row=0,column=1)
        # multi purpose controller
        self.mpcw = tkinter.Frame(self.multi_purpose_controller_window)
        self.mpcw.pack()
        self.mpc_setpoint_frame = tkinter.LabelFrame(self.mpcw,text="setpoints")
        self.mpc_setpoint_frame.grid(row=0,column=1)
        self.mpc_actualvalue_frame = tkinter.LabelFrame(self.mpcw,text="actual values")
        self.mpc_actualvalue_frame.grid(row=0,column=0)
        
        self.mpc_label_setpoint = dict()
        port = 'DO'
        self.mpc_label_setpoint[port] = [None,None,None,None]
        for i in range(4):
            self.mpc_label_setpoint[port][i] = dict()
            self.mpc_label_setpoint[port][i]['val'] = tkinter.IntVar()
            self.mpc_label_setpoint[port][i]['label'] = tkinter.Checkbutton(self.mpc_setpoint_frame,text="%s %d" % (port,i),command=self.click_DO_setpoint,variable=self.mpc_label_setpoint[port][i]['val'])
            self.mpc_label_setpoint[port][i]['label'].pack()
            self.mpc_label_setpoint[port][i]['label'].deselect()
        port = 'R'
        self.mpc_label_setpoint[port] = [None,None]
        for i in range(2):
            self.mpc_label_setpoint[port][i] = dict()
            self.mpc_label_setpoint[port][i]['val'] = tkinter.IntVar()
            self.mpc_label_setpoint[port][i]['label'] = tkinter.Checkbutton(self.mpc_setpoint_frame,text="%s %d" % (port,i),command=self.click_R_setpoint,variable=self.mpc_label_setpoint[port][i]['val'])
            self.mpc_label_setpoint[port][i]['label'].pack()
            self.mpc_label_setpoint[port][i]['label'].deselect()
        for port in ['U05','U15','U24']:
            self.mpc_label_setpoint[port] = dict()
            self.mpc_label_setpoint[port]['val'] = tkinter.IntVar()
            self.mpc_label_setpoint[port]['label'] = tkinter.Checkbutton(self.mpc_setpoint_frame,text="%s" % (port),command=self.click_Ux_setpoint,variable=self.mpc_label_setpoint[port]['val'])
            self.mpc_label_setpoint[port]['label'].pack()
            self.mpc_label_setpoint[port]['label'].deselect()
        port = 'DAC'
        self.mpc_label_setpoint[port] = [None,None,None,None]
        for i in range(4):
            self.mpc_label_setpoint[port][i] = dict()
            self.mpc_label_setpoint[port][i]['frame'] = tkinter.Frame(self.mpc_setpoint_frame)
            self.mpc_label_setpoint[port][i]['frame'].pack()
            f = self.mpc_label_setpoint[port][i]['frame']
            self.mpc_label_setpoint[port][i]['val'] = tkinter.StringVar()
            self.mpc_label_setpoint[port][i]['label'] = tkinter.Label(f,text="DAC %d:" % i)
            self.mpc_label_setpoint[port][i]['label'].grid(row=0,column=0)
            self.mpc_label_setpoint[port][i]['entry'] = tkinter.Entry(f,textvariable=self.mpc_label_setpoint[port][i]['val'])
            self.mpc_label_setpoint[port][i]['entry'].grid(row=0,column=1)
            self.mpc_label_setpoint[port][i]['button'] = tkinter.Button(f,command=self.click_DAC_setpoint,text="set")
            self.mpc_label_setpoint[port][i]['button'].grid(row=0,column=2)

        self.mpc_label_actualvalue = dict()
        port = 'DO'
        self.mpc_label_actualvalue[port] = [None,None,None,None]
        for i in range(4):
            self.mpc_label_actualvalue[port][i] = dict()
            self.mpc_label_actualvalue[port][i]['val'] = tkinter.StringVar()
            self.mpc_label_actualvalue[port][i]['val'].set("bool")
            self.mpc_label_actualvalue[port][i]['frame'] = tkinter.Frame(self.mpc_actualvalue_frame)
            self.mpc_label_actualvalue[port][i]['frame'].pack()
            f = self.mpc_label_actualvalue[port][i]['frame']
            self.mpc_label_actualvalue[port][i]['label1'] = tkinter.Label(f,text="DO %d:" % i)
            self.mpc_label_actualvalue[port][i]['label1'].grid(row=0,column=0)
            self.mpc_label_actualvalue[port][i]['label2'] = tkinter.Label(f,textvariable=self.mpc_label_actualvalue[port][i]['val'],height=1,width=5)
            self.mpc_label_actualvalue[port][i]['label2'].grid(row=0,column=1)
        self.mpc_label_actualvalue['R'] = [None,None]
        for i in range(2):
            self.mpc_label_actualvalue['R'][i] = dict()
            self.mpc_label_actualvalue['R'][i]['val'] = tkinter.StringVar()
            self.mpc_label_actualvalue['R'][i]['val'].set("bool")
            self.mpc_label_actualvalue['R'][i]['frame'] = tkinter.Frame(self.mpc_actualvalue_frame)
            self.mpc_label_actualvalue['R'][i]['frame'].pack()
            f = self.mpc_label_actualvalue['R'][i]['frame']
            self.mpc_label_actualvalue['R'][i]['label1'] = tkinter.Label(f,text="R %d:" % i)
            self.mpc_label_actualvalue['R'][i]['label1'].grid(row=0,column=0)
            self.mpc_label_actualvalue['R'][i]['label2'] = tkinter.Label(f,textvariable=self.mpc_label_actualvalue['R'][i]['val'],height=1,width=5)
            self.mpc_label_actualvalue['R'][i]['label2'].grid(row=0,column=1)
        for port in ['U05','U15','U24']:
            self.mpc_label_actualvalue[port] = dict()
            self.mpc_label_actualvalue[port]['val'] = tkinter.StringVar()
            self.mpc_label_actualvalue[port]['val'].set("bool")
            self.mpc_label_actualvalue[port]['frame'] = tkinter.Frame(self.mpc_actualvalue_frame)
            self.mpc_label_actualvalue[port]['frame'].pack()
            f = self.mpc_label_actualvalue[port]['frame']
            self.mpc_label_actualvalue[port]['label1'] = tkinter.Label(f,text="%s:" % port)
            self.mpc_label_actualvalue[port]['label1'].grid(row=0,column=0)
            self.mpc_label_actualvalue[port]['label2'] = tkinter.Label(f,textvariable=self.mpc_label_actualvalue[port]['val'],height=1,width=5)
            self.mpc_label_actualvalue[port]['label2'].grid(row=0,column=1)
        self.mpc_label_actualvalue['DAC'] = [None,None,None,None]
        for i in range(4):
            self.mpc_label_actualvalue['DAC'][i] = dict()
            self.mpc_label_actualvalue['DAC'][i]['val'] = tkinter.StringVar()
            self.mpc_label_actualvalue['DAC'][i]['val'].set("uint")
            self.mpc_label_actualvalue['DAC'][i]['frame'] = tkinter.Frame(self.mpc_actualvalue_frame)
            self.mpc_label_actualvalue['DAC'][i]['frame'].pack()
            f = self.mpc_label_actualvalue['DAC'][i]['frame']
            self.mpc_label_actualvalue['DAC'][i]['label1'] = tkinter.Label(f,text="DAC %d:" % i)
            self.mpc_label_actualvalue['DAC'][i]['label1'].grid(row=0,column=0)
            self.mpc_label_actualvalue['DAC'][i]['label2'] = tkinter.Label(f,textvariable=self.mpc_label_actualvalue['DAC'][i]['val'],height=1,width=5)
            self.mpc_label_actualvalue['DAC'][i]['label2'].grid(row=0,column=1)
        self.mpc_label_actualvalue['DI'] = [None,None,None,None]
        for i in range(4):
            self.mpc_label_actualvalue['DI'][i] = dict()
            self.mpc_label_actualvalue['DI'][i]['val'] = tkinter.StringVar()
            self.mpc_label_actualvalue['DI'][i]['val'].set("bool")
            self.mpc_label_actualvalue['DI'][i]['frame'] = tkinter.Frame(self.mpc_actualvalue_frame)
            self.mpc_label_actualvalue['DI'][i]['frame'].pack()
            f = self.mpc_label_actualvalue['DI'][i]['frame']
            self.mpc_label_actualvalue['DI'][i]['label1'] = tkinter.Label(f,text="DI %d:" % i)
            self.mpc_label_actualvalue['DI'][i]['label1'].grid(row=0,column=0)
            self.mpc_label_actualvalue['DI'][i]['label2'] = tkinter.Label(f,textvariable=self.mpc_label_actualvalue['DI'][i]['val'],height=1,width=5)
            self.mpc_label_actualvalue['DI'][i]['label2'].grid(row=0,column=1)
        self.mpc_label_actualvalue['ADC'] = [None,None,None,None,None,None,None,None]
        for i in range(8):
            self.mpc_label_actualvalue['ADC'][i] = dict()
            self.mpc_label_actualvalue['ADC'][i]['val'] = tkinter.StringVar()
            self.mpc_label_actualvalue['ADC'][i]['val'].set("uint")
            self.mpc_label_actualvalue['ADC'][i]['frame'] = tkinter.Frame(self.mpc_actualvalue_frame)
            self.mpc_label_actualvalue['ADC'][i]['frame'].pack()
            f = self.mpc_label_actualvalue['ADC'][i]['frame']
            self.mpc_label_actualvalue['ADC'][i]['label1'] = tkinter.Label(f,text="ADC %d:" % i)
            self.mpc_label_actualvalue['ADC'][i]['label1'].grid(row=0,column=0)
            self.mpc_label_actualvalue['ADC'][i]['label2'] = tkinter.Label(f,textvariable=self.mpc_label_actualvalue['ADC'][i]['val'],height=1,width=5)
            self.mpc_label_actualvalue['ADC'][i]['label2'].grid(row=0,column=1)



    def quit(self):
        if self.updateid:
                self.main_window.after_cancel(self.updateid)
        self.main_window.destroy()

    def update(self):
        for port in ['A','B','C','D']:
            for i in range(8):
                self.dc_label_actualvalue[port][i]['val'].set(b2s(self.controller['dc'].actualvalue[port][i]))
        port = 'DO'
        for i in range(4):
            self.mpc_label_actualvalue[port][i]['val'].set(b2s(self.controller['mpc'].actualvalue[port][i]))
        port = 'R'
        for i in range(2):
            self.mpc_label_actualvalue[port][i]['val'].set(b2s(self.controller['mpc'].actualvalue[port][i]))
        for port in ['U05','U15','U24']:
            self.mpc_label_actualvalue[port]['val'].set(b2s(self.controller['mpc'].actualvalue[port]))
        port = 'DAC'
        for i in range(4):
            self.mpc_label_actualvalue[port][i]['val'].set(self.controller['mpc'].actualvalue[port][i])
        port = 'DI'
        for i in range(4):
            self.mpc_label_actualvalue[port][i]['val'].set(b2s(self.controller['mpc'].actualvalue[port][i]))
        port = 'ADC'
        for i in range(8):
            self.mpc_label_actualvalue[port][i]['val'].set(self.controller['mpc'].actualvalue[port][i])

        if self.updateid:
                self.main_window.after_cancel(self.updateid)
        self.updateid = self.main_window.after(self.update_intervall,func=self.update)

    def click_DO_setpoint(self):
        port = 'DO'
        for i in range(4):
            if self.mpc_label_setpoint[port][i]['val'].get() != s2i(self.mpc_label_actualvalue[port][i]['val'].get()):
                self.controller['mpc'].setpoint[port][i] = i2b(self.mpc_label_setpoint[port][i]['val'].get())
    def click_R_setpoint(self):
        port = 'R'
        for i in range(2):
            if self.mpc_label_setpoint[port][i]['val'].get() != s2i(self.mpc_label_actualvalue[port][i]['val'].get()):
                self.controller['mpc'].setpoint[port][i] = i2b(self.mpc_label_setpoint[port][i]['val'].get())
    def click_Ux_setpoint(self):
        for port in ['U05','U15','U24']:
            if self.mpc_label_setpoint[port]['val'].get() != s2i(self.mpc_label_actualvalue[port]['val'].get()):
                self.controller['mpc'].setpoint[port] = i2b(self.mpc_label_setpoint[port]['val'].get())
    def click_DAC_setpoint(self):
        port = 'DAC'
        for i in range(4):
            v = self.mpc_label_setpoint[port][i]['val'].get()
            if len(v)>0:
                try:
                    self.controller['mpc'].setpoint[port][i] = int(v)
                    self.mpc_label_setpoint[port][i]['val'].set("")
                except:
                    self.mpc_label_setpoint[port][i]['val'].set("ERROR")
    def click_dc_setpoint(self):
        for port in ['A','B','C','D']:
            for i in range(4):
                if self.dc_label_setpoint[port][i]['val'].get() != s2i(self.dc_label_actualvalue[port][i]['val'].get()):
                    self.controller['dc'].setpoint[port][i] = i2b(self.dc_label_setpoint[port][i]['val'].get())

    def debugprint(self,o,prefix="",t=0):
        if self.debug >= 1:
            p = prefix
            if t>0:
                if t==1:
                    p = "%s%s" %(p,time.strftime("(%H:%M:%S) "))
                elif t==2:
                    p = "%s%s" %(p,time.strftime("(%Y-%m-%dT%H:%M:%S %Z) "))
            #o = string.split(o,"\n")
            #o = string.join(o,"\n%s" % p)
            o = o.split("\n")
            o = ("\n%s" % p).join(o)
            o = "%s%s" %(p,o)
            print(("%s" % o))

    def start(self):
        self.updateid = self.main_window.after(self.update_intervall,func=self.update) # call update every ... milliseconds
        self.main_window.mainloop()
        try:
            self.controller['dc'].stop()
        except:
            pass
        try:
            self.controller['mpc'].stop()
        except:
            pass
        time.sleep(0.6)
        print("good bye!")

def main():
    parser = argparse.ArgumentParser(
        description='debug controller"',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007" % __plc_date__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-system_config',
                        nargs=1,
                        default="/etc/plc.cfg",
                        type=str,
                        required=False,
                        dest='system_config',
                        help='Set system wide config file to use. This will be read first. (default: \'/etc/plc.cfg\')',
                        metavar='file')
    parser.add_argument('-config',
                        nargs=1,
                        default="~/.plc.cfg",
                        type=str,
                        required=False,
                        dest='config',
                        help='Set user config file to use. This will be read after the system wide config file. (default: \'~/.plc.cfg\')',
                        metavar='file')
    args = parser.parse_args()
    configname = ""
    if type(args.system_config) == list:
        args.system_config = args.system_config[0]
        configname = "%s%s" % (configname,args.system_config)
    if type(args.config) == list:
        args.config = args.config[0]
        configname = "%s%s" % (configname,args.config)
    g = gui(args,configname=configname)
    g.start()

if __name__ == "__main__":
    main()
