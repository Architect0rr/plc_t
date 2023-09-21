"""gui for Electrode Motion

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


class electrode_motion():
    """gui for Electrode Motion

    Author: Daniel Mohr
    Date: 2012-08-29
    """
    def __init__(self,config=None,pw=None,debugprint=None,controller=None):
        """__init__(self,config=None,pw=None,debugprint=None,controller=None)

        create gui for Electrode Motion

        Parameters:
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           debugprint : function
                        function to call for print debug information

        Author: Daniel Mohr
        Date: 2012-08-27
        """
        self.config=config
        self.padx = self.config.values.get('gui','padx')
        self.pady = self.config.values.get('gui','pady')
        self.pw=pw
        self.debugprint=debugprint
        self.controller=controller
        # create gui
        self.init_frame = tkinter.Frame(pw)
        self.init_frame.grid(column=0,row=0)
        self.power_status = tkinter.IntVar()
        self.power_button = tkinter.Checkbutton(self.init_frame,text="Power",command=self.power,variable=self.power_status,state=tkinter.DISABLED)
        self.power_button.pack()
        self.start_controller_button = tkinter.Button(self.init_frame,text="open RS232 (emc)",command=self.controller['emc'].start_request,padx=self.padx,pady=self.pady)
        self.start_controller_button.pack()
        self.stop_controller_button = tkinter.Button(self.init_frame,text="close RS232 (emc)",command=self.controller['emc'].stop_request,padx=self.padx,pady=self.pady)
        self.stop_controller_button.pack()
        # control area
        #self.guard_ring_frame = Tkinter.LabelFrame(pw,text="Guard Ring")
        self.guard_ring_frame = tkinter.Frame(pw)
        self.guard_ring_frame.grid(column=1,row=0)
        self.upper_guard_ring_frame = tkinter.LabelFrame(self.guard_ring_frame,text="Upper Guard Ring")
        self.upper_guard_ring_frame.pack()
        self.lower_guard_ring_frame = tkinter.LabelFrame(self.guard_ring_frame,text="Lower Guard Ring")
        self.lower_guard_ring_frame.pack()
        #self.electrode_frame = Tkinter.LabelFrame(pw,text="Electrode")
        self.electrode_frame = tkinter.Frame(pw)
        self.electrode_frame.grid(column=2,row=0)
        self.upper_electrode_frame = tkinter.LabelFrame(self.electrode_frame,text="Upper Electrode")
        self.upper_electrode_frame.pack()
        self.lower_electrode_frame = tkinter.LabelFrame(self.electrode_frame,text="Lower Electrode")
        self.lower_electrode_frame.pack()
        # lower guard ring
        f = self.lower_guard_ring_frame
        self.lower_guard_ring = dict()
        self.lower_guard_ring["10 down cmd"] = self.lower_guard_ring_10_down
        self.lower_guard_ring["1 down cmd"] = self.lower_guard_ring_1_down
        self.lower_guard_ring["n up/down cmd"] = self.lower_guard_ring_n_up_down
        self.lower_guard_ring["1 up cmd"] = self.lower_guard_ring_1_up
        self.lower_guard_ring["10 up cmd"] = self.lower_guard_ring_10_up
        self.lower_guard_ring["10 down button"] = tkinter.Button(f,command=self.lower_guard_ring["10 down cmd"],text="10 down",padx=self.padx,pady=self.pady)
        self.lower_guard_ring["10 down button"].grid(column=0,row=0)
        self.lower_guard_ring["1 down button"] = tkinter.Button(f,command=self.lower_guard_ring["1 down cmd"],text="1 down",padx=self.padx,pady=self.pady)
        self.lower_guard_ring["1 down button"].grid(column=1,row=0)
        self.lower_guard_ring["n up/down frame"] = tkinter.LabelFrame(f,text="n-steps (down: n<0)")
        self.lower_guard_ring["n up/down frame"].grid(column=2,row=0)
        self.lower_guard_ring["n up/down val"] = tkinter.IntVar()
        self.lower_guard_ring["n up/down entry"] = tkinter.Entry(self.lower_guard_ring["n up/down frame"],textvariable=self.lower_guard_ring["n up/down val"],width=6)
        self.lower_guard_ring["n up/down entry"].grid(column=0,row=0)
        self.lower_guard_ring["n up/down button"] = tkinter.Button(self.lower_guard_ring["n up/down frame"],command=self.lower_guard_ring["n up/down cmd"],text="do",padx=self.padx,pady=self.pady)
        self.lower_guard_ring["n up/down button"].grid(column=1,row=0)
        self.lower_guard_ring["1 up button"] = tkinter.Button(f,command=self.lower_guard_ring["1 up cmd"],text="1 up",padx=self.padx,pady=self.pady)
        self.lower_guard_ring["1 up button"].grid(column=3,row=0)
        self.lower_guard_ring["10 up button"] = tkinter.Button(f,command=self.lower_guard_ring["10 up cmd"],text="10 up",padx=self.padx,pady=self.pady)
        self.lower_guard_ring["10 up button"].grid(column=4,row=0)
        # upper guard ring
        f = self.upper_guard_ring_frame
        self.upper_guard_ring = dict()
        self.upper_guard_ring["10 down cmd"] = self.upper_guard_ring_10_down
        self.upper_guard_ring["1 down cmd"] = self.upper_guard_ring_1_down
        self.upper_guard_ring["n up/down cmd"] = self.upper_guard_ring_n_up_down
        self.upper_guard_ring["1 up cmd"] = self.upper_guard_ring_1_up
        self.upper_guard_ring["10 up cmd"] = self.upper_guard_ring_10_up
        self.upper_guard_ring["10 down button"] = tkinter.Button(f,command=self.upper_guard_ring["10 down cmd"],text="10 down",padx=self.padx,pady=self.pady)
        self.upper_guard_ring["10 down button"].grid(column=0,row=0)
        self.upper_guard_ring["1 down button"] = tkinter.Button(f,command=self.upper_guard_ring["1 down cmd"],text="1 down",padx=self.padx,pady=self.pady)
        self.upper_guard_ring["1 down button"].grid(column=1,row=0)
        self.upper_guard_ring["n up/down frame"] = tkinter.LabelFrame(f,text="n-steps (down: n<0)")
        self.upper_guard_ring["n up/down frame"].grid(column=2,row=0)
        self.upper_guard_ring["n up/down val"] = tkinter.IntVar()
        self.upper_guard_ring["n up/down entry"] = tkinter.Entry(self.upper_guard_ring["n up/down frame"],textvariable=self.upper_guard_ring["n up/down val"],width=6)
        self.upper_guard_ring["n up/down entry"].grid(column=0,row=0)
        self.upper_guard_ring["n up/down button"] = tkinter.Button(self.upper_guard_ring["n up/down frame"],command=self.upper_guard_ring["n up/down cmd"],text="do",padx=self.padx,pady=self.pady)
        self.upper_guard_ring["n up/down button"].grid(column=1,row=0)
        self.upper_guard_ring["1 up button"] = tkinter.Button(f,command=self.upper_guard_ring["1 up cmd"],text="1 up",padx=self.padx,pady=self.pady)
        self.upper_guard_ring["1 up button"].grid(column=3,row=0)
        self.upper_guard_ring["10 up button"] = tkinter.Button(f,command=self.upper_guard_ring["10 up cmd"],text="10 up",padx=self.padx,pady=self.pady)
        self.upper_guard_ring["10 up button"].grid(column=4,row=0)




        # lower electrode
        f = self.lower_electrode_frame
        self.lower_electrode = dict()
        self.lower_electrode["10 down cmd"] = self.lower_electrode_10_down
        self.lower_electrode["1 down cmd"] = self.lower_electrode_1_down
        self.lower_electrode["n up/down cmd"] = self.lower_electrode_n_up_down
        self.lower_electrode["1 up cmd"] = self.lower_electrode_1_up
        self.lower_electrode["10 up cmd"] = self.lower_electrode_10_up
        self.lower_electrode["10 down button"] = tkinter.Button(f,command=self.lower_electrode["10 down cmd"],text="10 down",padx=self.padx,pady=self.pady)
        self.lower_electrode["10 down button"].grid(column=0,row=0)
        self.lower_electrode["1 down button"] = tkinter.Button(f,command=self.lower_electrode["1 down cmd"],text="1 down",padx=self.padx,pady=self.pady)
        self.lower_electrode["1 down button"].grid(column=1,row=0)
        self.lower_electrode["n up/down frame"] = tkinter.LabelFrame(f,text="n-steps (down: n<0)")
        self.lower_electrode["n up/down frame"].grid(column=2,row=0)
        self.lower_electrode["n up/down val"] = tkinter.IntVar()
        self.lower_electrode["n up/down entry"] = tkinter.Entry(self.lower_electrode["n up/down frame"],textvariable=self.lower_electrode["n up/down val"],width=6)
        self.lower_electrode["n up/down entry"].grid(column=0,row=0)
        self.lower_electrode["n up/down button"] = tkinter.Button(self.lower_electrode["n up/down frame"],command=self.lower_electrode["n up/down cmd"],text="do",padx=self.padx,pady=self.pady)
        self.lower_electrode["n up/down button"].grid(column=1,row=0)
        self.lower_electrode["1 up button"] = tkinter.Button(f,command=self.lower_electrode["1 up cmd"],text="1 up",padx=self.padx,pady=self.pady)
        self.lower_electrode["1 up button"].grid(column=3,row=0)
        self.lower_electrode["10 up button"] = tkinter.Button(f,command=self.lower_electrode["10 up cmd"],text="10 up",padx=self.padx,pady=self.pady)
        self.lower_electrode["10 up button"].grid(column=4,row=0)
        # upper electrode
        f = self.upper_electrode_frame
        self.upper_electrode = dict()
        self.upper_electrode["10 down cmd"] = self.upper_electrode_10_down
        self.upper_electrode["1 down cmd"] = self.upper_electrode_1_down
        self.upper_electrode["n up/down cmd"] = self.upper_electrode_n_up_down
        self.upper_electrode["1 up cmd"] = self.upper_electrode_1_up
        self.upper_electrode["10 up cmd"] = self.upper_electrode_10_up
        self.upper_electrode["10 down button"] = tkinter.Button(f,command=self.upper_electrode["10 down cmd"],text="10 down",padx=self.padx,pady=self.pady)
        self.upper_electrode["10 down button"].grid(column=0,row=0)
        self.upper_electrode["1 down button"] = tkinter.Button(f,command=self.upper_electrode["1 down cmd"],text="1 down",padx=self.padx,pady=self.pady)
        self.upper_electrode["1 down button"].grid(column=1,row=0)
        self.upper_electrode["n up/down frame"] = tkinter.LabelFrame(f,text="n-steps (down: n<0)")
        self.upper_electrode["n up/down frame"].grid(column=2,row=0)
        self.upper_electrode["n up/down val"] = tkinter.IntVar()
        self.upper_electrode["n up/down entry"] = tkinter.Entry(self.upper_electrode["n up/down frame"],textvariable=self.upper_electrode["n up/down val"],width=6)
        self.upper_electrode["n up/down entry"].grid(column=0,row=0)
        self.upper_electrode["n up/down button"] = tkinter.Button(self.upper_electrode["n up/down frame"],command=self.upper_electrode["n up/down cmd"],text="do",padx=self.padx,pady=self.pady)
        self.upper_electrode["n up/down button"].grid(column=1,row=0)
        self.upper_electrode["1 up button"] = tkinter.Button(f,command=self.upper_electrode["1 up cmd"],text="1 up",padx=self.padx,pady=self.pady)
        self.upper_electrode["1 up button"].grid(column=3,row=0)
        self.upper_electrode["10 up button"] = tkinter.Button(f,command=self.upper_electrode["10 up cmd"],text="10 up",padx=self.padx,pady=self.pady)
        self.upper_electrode["10 up button"].grid(column=4,row=0)



    def power(self):
        if self.power_status.get()==0:
            s = False
        else:
            s = True
        self.debugprint("switch electrode motion to %s" % b2onoff(s))
        self.controller[self.config.values.get('electrode motion controller','power_controller')].setpoint[self.config.values.get('electrode motion controller','power_port')][int(self.config.values.get('electrode motion controller','power_channel'))] = s


    def lower_guard_ring_10_down(self):
        self.controller['emc'].setpoint['lower guard ring'] = -10
    def lower_guard_ring_1_down(self):
        self.controller['emc'].setpoint['lower guard ring'] = -1
    def lower_guard_ring_n_up_down(self):
        steps = 0
        try:
            steps = int(self.lower_guard_ring["n up/down val"].get())
        except:
            self.lower_guard_ring["n up/down val"].set("ERROR")
            return
        self.controller['emc'].setpoint['lower guard ring'] = steps
    def lower_guard_ring_10_up(self):
        self.controller['emc'].setpoint['lower guard ring'] = 10
    def lower_guard_ring_1_up(self):
        self.controller['emc'].setpoint['lower guard ring'] = 1

    def upper_guard_ring_10_down(self):
        self.controller['emc'].setpoint['upper guard ring'] = -10
    def upper_guard_ring_1_down(self):
        self.controller['emc'].setpoint['upper guard ring'] = -1
    def upper_guard_ring_n_up_down(self):
        steps = 0
        try:
            steps = int(self.upper_guard_ring["n up/down val"].get())
        except:
            self.upper_guard_ring["n up/down val"].set("ERROR")
            return
        self.controller['emc'].setpoint['upper guard ring'] = steps
    def upper_guard_ring_10_up(self):
        self.controller['emc'].setpoint['upper guard ring'] = 10
    def upper_guard_ring_1_up(self):
        self.controller['emc'].setpoint['upper guard ring'] = 1











    def lower_electrode_10_down(self):
        self.controller['emc'].setpoint['lower electrode'] = -10
    def lower_electrode_1_down(self):
        self.controller['emc'].setpoint['lower electrode'] = -1
    def lower_electrode_n_up_down(self):
        steps = 0
        try:
            steps = int(self.lower_electrode["n up/down val"].get())
        except:
            self.lower_electrode["n up/down val"].set("ERROR")
            return
        self.controller['emc'].setpoint['lower electrode'] = steps
    def lower_electrode_10_up(self):
        self.controller['emc'].setpoint['lower electrode'] = 10
    def lower_electrode_1_up(self):
        self.controller['emc'].setpoint['lower electrode'] = 1

    def upper_electrode_10_down(self):
        self.controller['emc'].setpoint['upper electrode'] = -10
    def upper_electrode_1_down(self):
        self.controller['emc'].setpoint['upper electrode'] = -1
    def upper_electrode_n_up_down(self):
        steps = 0
        try:
            steps = int(self.upper_electrode["n up/down val"].get())
        except:
            self.upper_electrode["n up/down val"].set("ERROR")
            return
        self.controller['emc'].setpoint['upper electrode'] = steps
    def upper_electrode_10_up(self):
        self.controller['emc'].setpoint['upper electrode'] = 10
    def upper_electrode_1_up(self):
        self.controller['emc'].setpoint['upper electrode'] = 1

    def check_buttons(self):
        if self.controller['dc'].isconnect:
            self.power_button.configure(state=tkinter.NORMAL)
        else:
            self.power_button.configure(state=tkinter.DISABLED)
        if self.controller['emc'].actualvalue['connect']:
            self.start_controller_button.configure(state=tkinter.DISABLED)
            self.stop_controller_button.configure(state=tkinter.NORMAL)
            # lower_guard_ring
            if self.controller['emc'].disabled_lower_guard_ring == False:
                self.lower_guard_ring["10 down button"].configure(state=tkinter.NORMAL)
                self.lower_guard_ring["1 down button"].configure(state=tkinter.NORMAL)
                self.lower_guard_ring["n up/down entry"].configure(state=tkinter.NORMAL)
                self.lower_guard_ring["n up/down button"].configure(state=tkinter.NORMAL)
                self.lower_guard_ring["1 up button"].configure(state=tkinter.NORMAL)
                self.lower_guard_ring["10 up button"].configure(state=tkinter.NORMAL)
            # upper_guard_ring
            self.upper_guard_ring["10 down button"].configure(state=tkinter.NORMAL)
            self.upper_guard_ring["1 down button"].configure(state=tkinter.NORMAL)
            self.upper_guard_ring["n up/down entry"].configure(state=tkinter.NORMAL)
            self.upper_guard_ring["n up/down button"].configure(state=tkinter.NORMAL)
            self.upper_guard_ring["1 up button"].configure(state=tkinter.NORMAL)
            self.upper_guard_ring["10 up button"].configure(state=tkinter.NORMAL)
            # lower_electrode
            self.lower_electrode["10 down button"].configure(state=tkinter.NORMAL)
            self.lower_electrode["1 down button"].configure(state=tkinter.NORMAL)
            self.lower_electrode["n up/down entry"].configure(state=tkinter.NORMAL)
            self.lower_electrode["n up/down button"].configure(state=tkinter.NORMAL)
            self.lower_electrode["1 up button"].configure(state=tkinter.NORMAL)
            self.lower_electrode["10 up button"].configure(state=tkinter.NORMAL)
            # upper_electrode
            self.upper_electrode["10 down button"].configure(state=tkinter.NORMAL)
            self.upper_electrode["1 down button"].configure(state=tkinter.NORMAL)
            self.upper_electrode["n up/down entry"].configure(state=tkinter.NORMAL)
            self.upper_electrode["n up/down button"].configure(state=tkinter.NORMAL)
            self.upper_electrode["1 up button"].configure(state=tkinter.NORMAL)
            self.upper_electrode["10 up button"].configure(state=tkinter.NORMAL)
        else:
            self.start_controller_button.configure(state=tkinter.NORMAL)
            self.stop_controller_button.configure(state=tkinter.DISABLED)
            # lower_guard_ring
            self.lower_guard_ring["10 down button"].configure(state=tkinter.DISABLED)
            self.lower_guard_ring["1 down button"].configure(state=tkinter.DISABLED)
            self.lower_guard_ring["n up/down entry"].configure(state=tkinter.DISABLED)
            self.lower_guard_ring["n up/down button"].configure(state=tkinter.DISABLED)
            self.lower_guard_ring["1 up button"].configure(state=tkinter.DISABLED)
            self.lower_guard_ring["10 up button"].configure(state=tkinter.DISABLED)
            # upper_guard_ring
            self.upper_guard_ring["10 down button"].configure(state=tkinter.DISABLED)
            self.upper_guard_ring["1 down button"].configure(state=tkinter.DISABLED)
            self.upper_guard_ring["n up/down entry"].configure(state=tkinter.DISABLED)
            self.upper_guard_ring["n up/down button"].configure(state=tkinter.DISABLED)
            self.upper_guard_ring["1 up button"].configure(state=tkinter.DISABLED)
            self.upper_guard_ring["10 up button"].configure(state=tkinter.DISABLED)
            # lower_electrode
            self.lower_electrode["10 down button"].configure(state=tkinter.DISABLED)
            self.lower_electrode["1 down button"].configure(state=tkinter.DISABLED)
            self.lower_electrode["n up/down entry"].configure(state=tkinter.DISABLED)
            self.lower_electrode["n up/down button"].configure(state=tkinter.DISABLED)
            self.lower_electrode["1 up button"].configure(state=tkinter.DISABLED)
            self.lower_electrode["10 up button"].configure(state=tkinter.DISABLED)
            # upper_electrode
            self.upper_electrode["10 down button"].configure(state=tkinter.DISABLED)
            self.upper_electrode["1 down button"].configure(state=tkinter.DISABLED)
            self.upper_electrode["n up/down entry"].configure(state=tkinter.DISABLED)
            self.upper_electrode["n up/down button"].configure(state=tkinter.DISABLED)
            self.upper_electrode["1 up button"].configure(state=tkinter.DISABLED)
            self.upper_electrode["10 up button"].configure(state=tkinter.DISABLED)
