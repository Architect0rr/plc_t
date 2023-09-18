"""gui for RF-Generator

Author: Daniel Mohr
Date: 2013-04-22
"""

import configparser
import logging
import logging.handlers
import os
import os.path
import re
import string
import tkinter.filedialog
import tkinter
from typing import Callable

from . import read_config_file

log = logging.getLogger("plc.rf_gen")
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

# from plc_tools.conversion import *

# from .class_rf_generator import *


class rf_generator_gui:
    """gui for rf_generator

    Author: Daniel Mohr
    Date: 2012-08-26
    """

    def __init__(self, config: read_config_file.read_config_file, pw: tkinter.Frame, debugprint, controller):
        """__init__(self,config=None,pw=None,debugprint=None,controller=None)

        create gui for rf_generator

        Parameters:
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           debugprint : function
                        function to call for print debug information

        Author: Daniel Mohr
        Date: 2012-09-07
        """
        self.config = config
        self.padx = self.config.values.get("gui", "padx")
        self.pady = self.config.values.get("gui", "pady")
        self.pw = pw
        self.debugprint = debugprint
        self.controller = controller
        self.maxcurrent = int(self.config.values.get("RF-Generator", "maxcurrent"))
        self.maxphase = int(self.config.values.get("RF-Generator", "maxphase"))
        if self.config.values.get("RF-Generator", "RF_only_master") == "1":
            self.RF_only_master = True
        else:
            self.RF_only_master = False
        # init
        self.generator = [None, None, None]
        for g in range(3):
            # ['RF-Generator 1','RF-Generator 2','RF-Generator 3']
            self.generator[g] = class_rf_generator()
            if self.config.values.get("RF-Generator %d" % (g + 1), "power_controller") == "-1":
                self.generator[g].exists = False
            else:
                self.generator[g].exists = True
                self.generator[g].power_controller = self.config.values.get("RF-Generator %d" % (g + 1), "power_controller")
                self.generator[g].power_port = self.config.values.get("RF-Generator %d" % (g + 1), "power_port")
                self.generator[g].power_channel = self.config.values.get("RF-Generator %d" % (g + 1), "power_channel")
                if g == 0:
                    self.generator[g].power_cmd = self.power_0
                elif g == 1:
                    self.generator[g].power_cmd = self.power_1
                elif g == 2:
                    self.generator[g].power_cmd = self.power_2
                elif g == 3:
                    self.generator[g].power_cmd = self.power_3
        # create gui
        self.frame = tkinter.LabelFrame(pw, text="RF-Generator")
        self.frame.pack()
        self.power_pattern_frame = tkinter.Frame(self.frame)
        self.power_pattern_frame.grid(column=0, row=0)
        self.power_frame = tkinter.LabelFrame(self.power_pattern_frame, text="Power")
        self.power_frame.pack()
        self.control_frame = tkinter.LabelFrame(self.frame, text="Control")
        self.control_frame.grid(column=1, row=0)
        self.pattern_frame = tkinter.LabelFrame(self.power_pattern_frame, text="Pattern")
        self.pattern_frame.pack()
        self.power_status = tkinter.IntVar()
        # Power
        for g in range(3):
            if self.generator[g].exists:
                self.generator[g].power_status = tkinter.IntVar()
                self.generator[g].power_status_checkbutton = tkinter.Checkbutton(
                    self.power_frame, text="Power RF-Generator %d" % (g + 1), command=self.generator[g].power_cmd, variable=self.generator[g].power_status, state=tkinter.DISABLED
                )
                self.generator[g].power_status_checkbutton.pack()
        self.start_controller_button = tkinter.Button(self.power_frame, text="open RS232 (rfgc)", command=self.controller["rfgc"].start_request, padx=self.padx, pady=self.pady)
        self.start_controller_button.pack()
        self.stop_controller_button = tkinter.Button(self.power_frame, text="close RS232 (rfgc)", command=self.controller["rfgc"].stop_request, padx=self.padx, pady=self.pady)
        self.stop_controller_button.pack()
        # Pattern
        self.pattern = dict()
        self.pattern_file = None  # will be set later as set in config
        self.pattern_config = None
        self.pattern_controller_var = tkinter.StringVar()
        self.pattern_controller_listbox = tkinter.OptionMenu(self.pattern_frame, self.pattern_controller_var, "microcontroller", "computer")
        self.pattern_controller_listbox.pack()
        self.pattern_controller_var.set("microcontroller")
        self.pattern_pattern_entry_val = tkinter.StringVar()
        self.pattern_pattern_entry = tkinter.Entry(self.pattern_frame, textvariable=self.pattern_pattern_entry_val, width=20)
        self.pattern_pattern_entry.pack()
        self.pattern_pattern_entry_val.set(" - no pattern - ")
        self.pattern_length_frame = tkinter.LabelFrame(self.pattern_frame, text="intervall length (us)", padx=self.padx, pady=self.pady)
        self.pattern_length_frame.pack()
        self.pattern_length_button = dict()
        self.pattern_length_button["- 100"] = tkinter.Button(self.pattern_length_frame, text="-100", command=self.pattern_length_cmd_down, padx=self.padx, pady=self.pady)
        self.pattern_length_button["- 100"].pack(side=tkinter.LEFT)
        self.pattern_length_val = tkinter.IntVar()
        self.pattern_length_entry = tkinter.Entry(self.pattern_length_frame, textvariable=self.pattern_length_val, width=8)
        self.pattern_length_entry.pack(side=tkinter.LEFT)
        self.pattern_length_val.set(
            int(
                round(
                    self.config.values.getfloat("RF-Generator", "pattern_microcontroller_intervall_length_factor")
                    * self.config.values.getint("RF-Generator", "pattern_microcontroller_min_intervall_length")
                    * 1000000
                )
            )
        )
        self.pattern_length_button["+ 100"] = tkinter.Button(self.pattern_length_frame, text="+100", command=self.pattern_length_cmd_up, padx=self.padx, pady=self.pady)
        self.pattern_length_button["+ 100"].pack(side=tkinter.LEFT)
        self.pattern_write_on_off_frame = tkinter.Frame(self.pattern_frame, padx=self.padx, pady=self.pady)
        self.pattern_write_on_off_frame.pack()

        self.pattern_load_button = tkinter.Button(self.pattern_write_on_off_frame, text="load", command=self.pattern_ask_for_load_file, padx=self.padx, pady=self.pady)
        self.pattern_load_button.pack(side=tkinter.LEFT)

        self.pattern_write_button = tkinter.Button(self.pattern_write_on_off_frame, text="write2gen", command=self.pattern_write_to_generator, padx=self.padx, pady=self.pady)
        self.pattern_write_button.pack(side=tkinter.LEFT)
        self.pattern_on_off_status = tkinter.IntVar()
        self.pattern_on_off_checkbutton = tkinter.Checkbutton(self.pattern_write_on_off_frame, text="On/Off", command=self.pattern_on_off, variable=self.pattern_on_off_status)
        self.pattern_on_off_checkbutton.pack(side=tkinter.LEFT)
        # Control
        self.ignite_plasma_button = tkinter.Button(self.control_frame, command=self.ignite_plasma, text="ignite plasma", padx=self.padx, pady=self.pady)
        self.ignite_plasma_button.grid(column=8, row=6)
        self.info1 = tkinter.Button(self.control_frame, command=self.set_currents, text=" set currents:", padx=self.padx, pady=self.pady)
        self.info1.grid(column=1, row=1)
        self.info2 = tkinter.Button(self.control_frame, command=self.set_phases, text=" set phases:", padx=self.padx, pady=self.pady)
        self.info2.grid(column=3, row=1)
        self.info3 = tkinter.Label(self.control_frame, text=" combined Changes:")
        self.info3.grid(column=5, row=1)
        self.combined_change_button1 = tkinter.Button(self.control_frame, command=self.combined_change_button1_cmd, text="Pwr On", padx=self.padx, pady=self.pady)
        self.combined_change_button1.grid(column=7, row=1)
        self.combined_change_button2 = tkinter.Button(self.control_frame, command=self.combined_change_button2_cmd, text="Pwr Off", padx=self.padx, pady=self.pady)
        self.combined_change_button2.grid(column=8, row=1)

        self.combined_change_button3 = tkinter.Button(self.control_frame, command=self.combined_change_button3_cmd, text="RF On", padx=self.padx, pady=self.pady)
        self.combined_change_button3.grid(column=7, row=2)
        self.combined_change_button4 = tkinter.Button(self.control_frame, command=self.combined_change_button4_cmd, text="RF Off", padx=self.padx, pady=self.pady)
        self.combined_change_button4.grid(column=8, row=2)

        self.combined_change_button5 = tkinter.Button(self.control_frame, command=self.combined_change_button5_cmd, text="current: -10", padx=self.padx, pady=self.pady)
        self.combined_change_button5.grid(column=7, row=3)
        self.combined_change_button6 = tkinter.Button(self.control_frame, command=self.combined_change_button6_cmd, text="current: +10", padx=self.padx, pady=self.pady)
        self.combined_change_button6.grid(column=8, row=3)

        self.combined_change_button7 = tkinter.Button(self.control_frame, command=self.combined_change_button7_cmd, text="current: -100", padx=self.padx, pady=self.pady)
        self.combined_change_button7.grid(column=7, row=4)
        self.combined_change_button8 = tkinter.Button(self.control_frame, command=self.combined_change_button8_cmd, text="current: +100", padx=self.padx, pady=self.pady)
        self.combined_change_button8.grid(column=8, row=4)

        self.combined_change_button9 = tkinter.Button(self.control_frame, command=self.combined_change_button9_cmd, text="current: -1000", padx=self.padx, pady=self.pady)
        self.combined_change_button9.grid(column=7, row=5)
        self.combined_change_button10 = tkinter.Button(self.control_frame, command=self.combined_change_button10_cmd, text="current: +1000", padx=self.padx, pady=self.pady)
        self.combined_change_button10.grid(column=8, row=5)

        cn = 1
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    # power on/off
                    self.generator[g].channel[i].onoff_status = tkinter.IntVar()
                    self.generator[g].channel[i].onoff_status_checkbutton = tkinter.Checkbutton(
                        self.control_frame,
                        text="Pwr Channel %d" % (cn),
                        command=self.rf_channel_onoff_cmd,
                        variable=self.generator[g].channel[i].onoff_status,
                        state=tkinter.DISABLED,
                    )
                    self.generator[g].channel[i].onoff_status_checkbutton.grid(column=0, row=cn)
                    # currents
                    self.generator[g].channel[i].current_status = tkinter.IntVar()
                    self.generator[g].channel[i].current_status_entry = tkinter.Entry(self.control_frame, textvariable=self.generator[g].channel[i].current_status, width=5)
                    self.generator[g].channel[i].current_status_entry.grid(column=2, row=cn)
                    # phases
                    self.generator[g].channel[i].phase_status = tkinter.IntVar()
                    self.generator[g].channel[i].phase_status_entry = tkinter.Entry(self.control_frame, textvariable=self.generator[g].channel[i].phase_status, width=4)
                    self.generator[g].channel[i].phase_status_entry.grid(column=4, row=cn)
                    # combined changes
                    self.generator[g].channel[i].choose = tkinter.IntVar()
                    self.generator[g].channel[i].choose_checkbutton = tkinter.Checkbutton(
                        self.control_frame, text="Channel %d" % (cn), variable=self.generator[g].channel[i].choose
                    )
                    self.generator[g].channel[i].choose_checkbutton.grid(column=6, row=cn)
                    self.generator[g].channel[i].choose_checkbutton.select()

                    cn = cn + 1
        # Pattern
        if self.config.values.get("RF-Generator", "pattern_file") != "-1":
            self.pattern_file = self.config.values.get("RF-Generator", "pattern_file")
            self.pattern_load_file()

    def rf_channel_onoff_cmd(self):
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    if self.generator[g].channel[i].onoff_status.get() == 1:
                        self.controller["rfgc"].generator[g].setpoint_channel[i].onoff = True
                        log.debug("switch channel %d at generator %d to %s" % (i, g, b2onoff(True)))
                    else:
                        self.controller["rfgc"].generator[g].setpoint_channel[i].onoff = False
                        log.debug("switch channel %d at generator %d to %s" % (i, g, b2onoff(False)))

    def set_currents(self):
        cn = 1
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    try:
                        a = int(self.generator[g].channel[i].current_status.get())
                    except:
                        a = None
                    if a == None:
                        log.warning("ERROR: do not understand current to set in channel %d" % cn)
                        self.generator[g].channel[i].current_status.set(self.controller["rfgc"].generator[g].actualvalue_channel[i].current)
                    else:
                        if (0 <= a) and (a <= self.maxcurrent):
                            self.controller["rfgc"].generator[g].setpoint_channel[i].current = max(0, min(a, self.maxcurrent))
                        else:
                            a = max(0, min(a, self.maxcurrent))
                            self.controller["rfgc"].generator[g].setpoint_channel[i].current = a
                            log.debug("wanted current %s for channel %d out of range [%d;%d]" % (a, cn, 0, self.maxcurrent))
                            self.generator[g].channel[i].current_status.set(a)
                    cn = cn + 1

    def set_phases(self):
        cn = 1
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    try:
                        a = int(self.generator[g].channel[i].phase_status.get())
                    except:
                        a = None
                    if a == None:
                        log.warning("ERROR: do not understand phase to set in channel %d" % cn)
                        self.generator[g].channel[i].phase_status.set(self.controller["rfgc"].generator[g].actualvalue_channel[i].phase)
                    else:
                        if (0 <= a) and (a <= self.maxphase):
                            self.controller["rfgc"].generator[g].setpoint_channel[i].phase = max(0, min(a, self.maxphase))
                        else:
                            a = max(0, min(a, self.maxphase))
                            self.controller["rfgc"].generator[g].setpoint_channel[i].phase = a
                            log.debug("wanted phase %s for channel %d out of range [%d;%d]" % (a, cn, 0, self.maxphase))
                            self.generator[g].channel[i].phase_status.set(a)
                    cn = cn + 1

    def pattern_length_cmd_down(self):
        a = self.pattern_length_val.get()
        self.pattern_length_val.set(a - 100)

    def pattern_length_cmd_up(self):
        a = self.pattern_length_val.get()
        self.pattern_length_val.set(a + 100)

    def pattern_ask_for_load_file(self):
        log.debug("ask for file to read pattern from")
        f = tkinter.filedialog.askopenfilename(defaultextension=".cfg", initialdir="~", title="read pattern from file")
        try:
            if len(f) > 0:
                self.pattern_file = f
                self.pattern_load_file()
        except:
            pass

    def pattern_load_file(self):
        if self.pattern_file != None:
            self.pattern_config = configparser.ConfigParser()
            self.pattern_config.read(os.path.expanduser(self.pattern_file))
            if (
                self.pattern_config.has_option("pattern", "number_of_generators")
                and self.pattern_config.has_option("pattern", "pattern_length")
                and self.pattern_config.has_option("pattern", "pattern_intervall_length")
                and self.pattern_config.has_option("pattern", "pattern")
            ):
                log.info("pattern file '%s' loaded" % self.pattern_file)
                self.pattern["number_of_generators"] = self.pattern_config.getint("pattern", "number_of_generators")
                self.pattern["pattern_length"] = self.pattern_config.getint("pattern", "pattern_length")
                self.pattern["pattern_intervall_length"] = self.pattern_config.getint("pattern", "pattern_intervall_length")
                self.pattern["pattern"] = re.sub("[%s]+" % string.whitespace, "", self.pattern_config.get("pattern", "pattern"))
                self.pattern_pattern_entry_val.set("%d;%d;%s" % (self.pattern["number_of_generators"], self.pattern["pattern_length"], self.pattern["pattern"]))
                self.pattern_length_val.set(self.pattern["pattern_intervall_length"])
                if self.pattern_config.has_option("pattern", "controller"):
                    if self.pattern_config.get("pattern", "controller") == "microcontroller":
                        self.pattern_controller_var.set("microcontroller")
                    elif self.pattern_config.get("pattern", "controller") == "computer":
                        self.pattern_controller_var.set("computer")
            else:
                log.warning("do not understand pattern file '%s'" % self.pattern_file)
                self.pattern_file = None
                self.pattern_config = None

    def pattern_write_to_generator(self):
        self.pattern["controller"] = self.pattern_controller_var.get()
        self.pattern["pattern_intervall_length"] = self.pattern_length_val.get()
        if self.pattern["controller"] == "microcontroller":
            log.debug("microcontroller")
            self.pattern["pattern_intervall_length"] = max(
                self.config.values.getint("RF-Generator", "pattern_microcontroller_min_intervall_length"),
                min(self.pattern["pattern_intervall_length"], self.config.values.getint("RF-Generator", "pattern_microcontroller_max_intervall_length")),
            )
            self.pattern_length_val.set(self.pattern["pattern_intervall_length"])
        # a = string.split(self.pattern_pattern_entry_val.get(),";")
        a = self.pattern_pattern_entry_val.get().split(";")
        self.pattern["number_of_generators"] = int(a[0])
        self.pattern["pattern_length"] = int(a[1])
        self.pattern["pattern"] = a[2]
        if len(self.pattern["pattern"]) == self.pattern["number_of_generators"] * 4 * self.pattern["pattern_length"]:
            if self.pattern["controller"] == "computer":
                log.debug(
                    "initiate using pattern '%s' with length %d in %d generators" % (self.pattern["pattern"], self.pattern["pattern_length"], self.pattern["number_of_generators"])
                )
            else:
                log.debug(
                    "initiate writing pattern '%s' with length %d to %d generators"
                    % (self.pattern["pattern"], self.pattern["pattern_length"], self.pattern["number_of_generators"])
                )
            self.controller["rfgc"].setpoint["pattern_controller"] = self.pattern["controller"]
            self.controller["rfgc"].setpoint["pattern_number_of_generators"] = self.pattern["number_of_generators"]
            self.controller["rfgc"].setpoint["pattern_length"] = self.pattern["pattern_length"]
            self.controller["rfgc"].setpoint["pattern_intervall_length"] = self.pattern["pattern_intervall_length"]
            self.controller["rfgc"].setpoint["pattern"] = self.pattern["pattern"]
            self.controller["rfgc"].setpoint["write_pattern"] = True
        else:
            log.warning("cannot write pattern; do not understand setting")

    def pattern_on_off(self):
        if self.pattern_on_off_status.get() == 1:
            # start running pattern
            self.pattern["controller"] = self.pattern_controller_var.get()
            if self.pattern["controller"] == "computer":
                self.pattern_write_to_generator()
            self.pattern["pattern_intervall_length"] = self.pattern_length_val.get()
            # a = string.split(self.pattern_pattern_entry_val.get(),";")
            a = self.pattern_pattern_entry_val.get().split(";")
            self.pattern["number_of_generators"] = int(a[0])
            self.pattern["pattern_length"] = int(a[1])
            self.pattern["pattern"] = a[2]
            if len(self.pattern["pattern"]) == self.pattern["number_of_generators"] * 4 * self.pattern["pattern_length"]:
                log.info("initiate start pattern run")
                self.controller["rfgc"].setpoint["pattern_controller"] = self.pattern["controller"]
                self.controller["rfgc"].setpoint["pattern_number_of_generators"] = self.pattern["number_of_generators"]
                self.controller["rfgc"].setpoint["pattern_length"] = self.pattern["pattern_length"]
                self.controller["rfgc"].setpoint["pattern_intervall_length"] = self.pattern["pattern_intervall_length"]
                self.controller["rfgc"].setpoint["pattern"] = self.pattern["pattern"]
                self.controller["rfgc"].setpoint["run_pattern"] = True
            else:
                log.warning("cannot initiate pattern run; do not understand setting")
        else:
            # stop running pattern
            log.info("initiate stop pattern run")
            self.controller["rfgc"].setpoint["run_pattern"] = False

    def combined_change_button1_cmd(self):
        # Power On
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    if self.generator[g].channel[i].choose.get() == 1:
                        log.debug("switch channel %d at generator %d to %s" % (i, g, b2onoff(True)))
                        self.controller["rfgc"].generator[g].setpoint_channel[i].onoff = True
                        self.generator[g].channel[i].onoff_status_checkbutton.select()

    def combined_change_button2_cmd(self):
        # Power Off
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    if self.generator[g].channel[i].choose.get() == 1:
                        log.debug("switch channel %d at generator %d to %s" % (i, g, b2onoff(False)))
                        self.controller["rfgc"].generator[g].setpoint_channel[i].onoff = False
                        self.generator[g].channel[i].onoff_status_checkbutton.deselect()

    def combined_change_button3_cmd(self):
        # RF Off
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    if self.generator[g].channel[i].choose.get() == 1:
                        if (self.RF_only_master == False) or (g == 0):
                            self.controller["rfgc"].generator[g].setpoint_rf_onoff = True

    def combined_change_button4_cmd(self):
        # RF On
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    if self.generator[g].channel[i].choose.get() == 1:
                        if (self.RF_only_master == False) or (g == 0):
                            self.controller["rfgc"].generator[g].setpoint_rf_onoff = False

    def combined_change_button5_cmd(self):
        self.combined_change_current(-10)

    def combined_change_button6_cmd(self):
        self.combined_change_current(+10)

    def combined_change_button7_cmd(self):
        self.combined_change_current(-100)

    def combined_change_button8_cmd(self):
        self.combined_change_current(+100)

    def combined_change_button9_cmd(self):
        self.combined_change_current(-1000)

    def combined_change_button10_cmd(self):
        self.combined_change_current(+1000)

    def combined_change_current(self, a):
        # change current
        for g in range(3):
            if self.generator[g].exists:
                for i in range(4):
                    if self.generator[g].channel[i].choose.get() == 1:
                        na = max(0, min(self.controller["rfgc"].generator[g].actualvalue_channel[i].current + a, self.maxcurrent))
                        self.controller["rfgc"].generator[g].setpoint_channel[i].current = na
                        self.generator[g].channel[i].current_status.set(na)

    def ignite_plasma(self):
        # ignite plasma
        for g in range(3):
            if self.controller["rfgc"].generator[g].exists:
                self.controller["rfgc"].generator[g].setpoint_ignite_plasma = True

    def power_0(self):
        self.power(0)

    def power_1(self):
        self.power(1)

    def power_2(self):
        self.power(2)

    def power_3(self):
        self.power(4)

    def power(self, g):
        if self.generator[g].exists:
            if self.generator[g].power_status.get() == 0:
                s = False
            else:
                s = True
            log.info("switch RF-Generator power to %s" % b2onoff(s))
            self.controller[self.generator[g].power_controller].setpoint[self.generator[g].power_port][int(self.generator[g].power_channel)] = s

    def check_buttons(self):
        if self.pattern_controller_var.get() == "microcontroller":
            self.pattern_write_button.configure(state=tkinter.NORMAL)
        else:
            self.pattern_write_button.configure(state=tkinter.DISABLED)
        if self.controller["dc"].isconnect:
            for g in range(3):
                if self.generator[g].exists:
                    self.generator[g].power_status_checkbutton.configure(state=tkinter.NORMAL)
        else:
            for g in range(3):
                if self.generator[g].exists:
                    self.generator[g].power_status_checkbutton.configure(state=tkinter.DISABLED)
        if self.controller["rfgc"].actualvalue["connect"]:
            self.start_controller_button.configure(state=tkinter.DISABLED)
            self.stop_controller_button.configure(state=tkinter.NORMAL)
            self.ignite_plasma_button.configure(state=tkinter.NORMAL)
            self.info1.configure(state=tkinter.NORMAL)
            self.info2.configure(state=tkinter.NORMAL)
            self.info3.configure(state=tkinter.NORMAL)
            self.combined_change_button1.configure(state=tkinter.NORMAL)
            self.combined_change_button2.configure(state=tkinter.NORMAL)
            self.combined_change_button3.configure(state=tkinter.NORMAL)
            self.combined_change_button4.configure(state=tkinter.NORMAL)
            self.combined_change_button5.configure(state=tkinter.NORMAL)
            self.combined_change_button6.configure(state=tkinter.NORMAL)
            self.combined_change_button7.configure(state=tkinter.NORMAL)
            self.combined_change_button8.configure(state=tkinter.NORMAL)
            self.combined_change_button9.configure(state=tkinter.NORMAL)
            self.combined_change_button10.configure(state=tkinter.NORMAL)
            for g in range(3):
                if self.generator[g].exists:
                    for i in range(4):
                        self.generator[g].channel[i].onoff_status_checkbutton.configure(state=tkinter.NORMAL)
                        self.generator[g].channel[i].current_status_entry.configure(state=tkinter.NORMAL)
                        self.generator[g].channel[i].phase_status_entry.configure(state=tkinter.NORMAL)
                        self.generator[g].channel[i].choose_checkbutton.configure(state=tkinter.NORMAL)
        else:
            self.start_controller_button.configure(state=tkinter.NORMAL)
            self.stop_controller_button.configure(state=tkinter.DISABLED)
            self.ignite_plasma_button.configure(state=tkinter.DISABLED)
            self.info1.configure(state=tkinter.DISABLED)
            self.info2.configure(state=tkinter.DISABLED)
            self.info3.configure(state=tkinter.DISABLED)
            self.combined_change_button1.configure(state=tkinter.DISABLED)
            self.combined_change_button2.configure(state=tkinter.DISABLED)
            self.combined_change_button3.configure(state=tkinter.DISABLED)
            self.combined_change_button4.configure(state=tkinter.DISABLED)
            self.combined_change_button5.configure(state=tkinter.DISABLED)
            self.combined_change_button6.configure(state=tkinter.DISABLED)
            self.combined_change_button7.configure(state=tkinter.DISABLED)
            self.combined_change_button8.configure(state=tkinter.DISABLED)
            self.combined_change_button9.configure(state=tkinter.DISABLED)
            self.combined_change_button10.configure(state=tkinter.DISABLED)
            for g in range(3):
                if self.generator[g].exists:
                    for i in range(4):
                        self.generator[g].channel[i].onoff_status_checkbutton.configure(state=tkinter.DISABLED)
                        self.generator[g].channel[i].current_status_entry.configure(state=tkinter.DISABLED)
                        self.generator[g].channel[i].phase_status_entry.configure(state=tkinter.DISABLED)
                        self.generator[g].channel[i].choose_checkbutton.configure(state=tkinter.DISABLED)
