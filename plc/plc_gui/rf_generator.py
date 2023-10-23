#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Daniel Mohr
#
# Copyright (C) 2023 Perevoshchikov Egor
#
# This file is part of PlasmaLabControl.
#
# PlasmaLabControl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PlasmaLabControl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PlasmaLabControl.  If not, see <http://www.gnu.org/licenses/>.

"""
gui for RF-Generator
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
import tkinter.ttk
from typing import List, Dict, Any

from ..plc_gui.rf_generator_controller import rf_generator_controller

from .read_config_file import read_config_file
from .class_rf_generator import rfg_gui


class rf_generator_gui:
    """
    gui for rf_generator
    """

    def __init__(
        self,
        config: read_config_file,
        pw: tkinter.Frame,
        _rfgc: rf_generator_controller,
        _log: logging.Logger,
    ) -> None:
        """__init__(self,config=None,pw=None,debugprint=None,controller=None)

        create gui for rf_generator

        Parameters:
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           debugprint : function
                        function to call for print debug information
        """
        self.log = _log
        self.config = config
        self.padx = self.config.values.get("gui", "padx")
        self.pady = self.config.values.get("gui", "pady")
        self.pw = pw
        self.rfgc: rf_generator_controller = _rfgc
        self.maxcurrent = int(self.config.values.get("RF-Generator", "maxcurrent"))
        self.maxphase = int(self.config.values.get("RF-Generator", "maxphase"))
        if self.config.values.get("RF-Generator", "RF_only_master") == "1":
            self.RF_only_master = True
        else:
            self.RF_only_master = False
        # create gui
        self.frame = tkinter.LabelFrame(pw, text="RF-Generator")
        self.frame.pack()

        self.control_frame = tkinter.LabelFrame(self.frame, text="Control")
        self.control_frame.grid(column=1, row=0)

        self.power_pattern_frame = tkinter.Frame(self.frame)
        self.power_pattern_frame.grid(column=0, row=0)

        # Power
        self.power_frame = tkinter.LabelFrame(self.power_pattern_frame, text="Power")
        self.power_frame.pack()
        self.start_controller_button = tkinter.Button(
            self.power_frame, text="open RS232 (rfgc)", command=self.btn_open_rfgc, state=tkinter.NORMAL
        )
        self.start_controller_button.pack()
        self.stop_controller_button = tkinter.Button(
            self.power_frame,
            text="close RS232 (rfgc)",
            command=self.btn_close_rfgc,
            state=tkinter.DISABLED,
        )
        self.stop_controller_button.pack()
        # init
        self.gen_frm = tkinter.ttk.LabelFrame(self.frame, text="Generators")
        self.gen_frms: List[rfg_gui] = []
        # ['RF-Generator 1','RF-Generator 2','RF-Generator 3']
        for g in range(3):
            self.gen_frms.append(rfg_gui(self.gen_frm, self.rfgc.generator[g], self.log.getChild(f"rfgg{g}")))
            self.gen_frms[g].grid(row=0, column=g + 1)

        # Pattern
        self.pattern_frame = tkinter.LabelFrame(self.power_pattern_frame, text="Pattern")
        self.pattern_frame.pack()
        self.pattern: Dict[str, Any] = {}
        self.pattern_file = None  # will be set later as set in config
        self.pattern_config = configparser.ConfigParser()
        self.pattern_controller_var = tkinter.StringVar()
        self.pattern_controller_listbox = tkinter.OptionMenu(
            self.pattern_frame, self.pattern_controller_var, "microcontroller", "computer"
        )
        self.pattern_controller_listbox.pack()
        self.pattern_controller_var.set("microcontroller")
        self.pattern_pattern_entry_val = tkinter.StringVar()
        self.pattern_pattern_entry = tkinter.Entry(
            self.pattern_frame, textvariable=self.pattern_pattern_entry_val, width=20
        )
        self.pattern_pattern_entry.pack()
        self.pattern_pattern_entry_val.set(" - no pattern - ")
        self.pattern_length_frame = tkinter.LabelFrame(self.pattern_frame, text="intervall length (us)")
        self.pattern_length_frame.pack()
        self.pattern_length_button = {}
        self.pattern_length_button["- 100"] = tkinter.Button(
            self.pattern_length_frame, text="-100", command=self.pattern_length_cmd_down
        )
        self.pattern_length_button["- 100"].pack(side=tkinter.LEFT)
        self.pattern_length_val = tkinter.IntVar()
        self.pattern_length_entry = tkinter.Entry(
            self.pattern_length_frame, textvariable=self.pattern_length_val, width=8
        )
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
        self.pattern_length_button["+ 100"] = tkinter.Button(
            self.pattern_length_frame, text="+100", command=self.pattern_length_cmd_up
        )
        self.pattern_length_button["+ 100"].pack(side=tkinter.LEFT)
        self.pattern_write_on_off_frame = tkinter.Frame(self.pattern_frame, padx=self.padx, pady=self.pady)
        self.pattern_write_on_off_frame.pack()

        self.pattern_load_button = tkinter.Button(
            self.pattern_write_on_off_frame, text="load", command=self.pattern_ask_for_load_file
        )
        self.pattern_load_button.pack(side=tkinter.LEFT)

        self.pattern_write_button = tkinter.Button(
            self.pattern_write_on_off_frame, text="write2gen", command=self.pattern_write_to_generator
        )
        self.pattern_write_button.pack(side=tkinter.LEFT)
        self.pattern_on_off_status = tkinter.IntVar()
        self.pattern_on_off_checkbutton = tkinter.Checkbutton(
            self.pattern_write_on_off_frame,
            text="On/Off",
            command=self.pattern_on_off,
            variable=self.pattern_on_off_status,
        )
        self.pattern_on_off_checkbutton.pack(side=tkinter.LEFT)

        # Control

        self.ignite_plasma_button = tkinter.Button(
            self.control_frame, command=self.btn_ignite_plasma, text="ignite plasma"
        )
        self.ignite_plasma_button.grid(column=8, row=6)
        self.info3 = tkinter.Label(self.control_frame, text=" combined Changes:")
        self.info3.grid(column=5, row=1)
        self.combined_change_button1 = tkinter.Button(self.control_frame, command=self.btn_pwr_on, text="Pwr On")
        self.combined_change_button1.grid(column=7, row=1)
        self.combined_change_button2 = tkinter.Button(
            self.control_frame, command=self.btn_pwr_off, text="Pwr Off", state=tkinter.DISABLED
        )
        self.combined_change_button2.grid(column=8, row=1)

        self.combined_change_button3 = tkinter.Button(self.control_frame, command=self.btn_rf_on, text="RF On")
        self.combined_change_button3.grid(column=7, row=2)
        self.combined_change_button4 = tkinter.Button(
            self.control_frame, command=self.btn_rf_off, text="RF Off", state=tkinter.DISABLED
        )
        self.combined_change_button4.grid(column=8, row=2)

        self.combined_change_button5 = tkinter.Button(
            self.control_frame,
            command=lambda: self.ccc(-10),
            text="current: -10",
            padx=self.padx,
            pady=self.pady,
        )
        self.combined_change_button5.grid(column=7, row=3)
        self.combined_change_button6 = tkinter.Button(
            self.control_frame,
            command=lambda: self.ccc(10),
            text="current: +10",
            padx=self.padx,
            pady=self.pady,
        )
        self.combined_change_button6.grid(column=8, row=3)

        self.combined_change_button7 = tkinter.Button(
            self.control_frame,
            command=lambda: self.ccc(-100),
            text="current: -100",
            padx=self.padx,
            pady=self.pady,
        )
        self.combined_change_button7.grid(column=7, row=4)
        self.combined_change_button8 = tkinter.Button(
            self.control_frame,
            command=lambda: self.ccc(100),
            text="current: +100",
            padx=self.padx,
            pady=self.pady,
        )
        self.combined_change_button8.grid(column=8, row=4)

        self.combined_change_button9 = tkinter.Button(
            self.control_frame,
            command=lambda: self.ccc(-1000),
            text="current: -1000",
            padx=self.padx,
            pady=self.pady,
        )
        self.combined_change_button9.grid(column=7, row=5)
        self.combined_change_button10 = tkinter.Button(
            self.control_frame,
            command=lambda: self.ccc(1000),
            text="current: +1000",
            padx=self.padx,
            pady=self.pady,
        )
        self.combined_change_button10.grid(column=8, row=5)

        # Pattern
        if self.config.values.get("RF-Generator", "pattern_file") != "-1":
            self.pattern_file = self.config.values.get("RF-Generator", "pattern_file")
            self.pattern_load_file()

    def pattern_length_cmd_down(self) -> None:
        a = self.pattern_length_val.get()
        self.pattern_length_val.set(a - 100)

    def pattern_length_cmd_up(self) -> None:
        a = self.pattern_length_val.get()
        self.pattern_length_val.set(a + 100)

    def pattern_ask_for_load_file(self) -> None:
        self.log.debug("ask for file to read pattern from")
        f = tkinter.filedialog.askopenfilename(defaultextension=".cfg", initialdir="~", title="read pattern from file")
        try:
            if len(f) > 0:
                self.pattern_file = f
                self.pattern_load_file()
        except Exception:
            pass

    def pattern_load_file(self) -> None:
        if self.pattern_file is not None:
            self.pattern_config.read(os.path.expanduser(self.pattern_file))
            if (
                self.pattern_config.has_option("pattern", "number_of_generators")
                and self.pattern_config.has_option("pattern", "pattern_length")
                and self.pattern_config.has_option("pattern", "pattern_intervall_length")
                and self.pattern_config.has_option("pattern", "pattern")
            ):
                self.log.info("pattern file '%s' loaded" % self.pattern_file)
                self.pattern["number_of_generators"] = self.pattern_config.getint("pattern", "number_of_generators")
                self.pattern["pattern_length"] = self.pattern_config.getint("pattern", "pattern_length")
                self.pattern["pattern_intervall_length"] = self.pattern_config.getint(
                    "pattern", "pattern_intervall_length"
                )
                self.pattern["pattern"] = re.sub(
                    "[%s]+" % string.whitespace, "", self.pattern_config.get("pattern", "pattern")
                )
                self.pattern_pattern_entry_val.set(
                    "%d;%d;%s"
                    % (
                        self.pattern["number_of_generators"],
                        self.pattern["pattern_length"],
                        self.pattern["pattern"],
                    )
                )
                self.pattern_length_val.set(self.pattern["pattern_intervall_length"])
                if self.pattern_config.has_option("pattern", "controller"):
                    if self.pattern_config.get("pattern", "controller") == "microcontroller":
                        self.pattern_controller_var.set("microcontroller")
                    elif self.pattern_config.get("pattern", "controller") == "computer":
                        self.pattern_controller_var.set("computer")
            else:
                self.log.warning("do not understand pattern file '%s'" % self.pattern_file)
                self.pattern_file = None
                self.pattern_config = configparser.ConfigParser()

    def pattern_write_to_generator(self) -> None:
        self.pattern["controller"] = self.pattern_controller_var.get()
        self.pattern["pattern_intervall_length"] = self.pattern_length_val.get()
        if self.pattern["controller"] == "microcontroller":
            self.log.debug("microcontroller")
            self.pattern["pattern_intervall_length"] = max(
                self.config.values.getint("RF-Generator", "pattern_microcontroller_min_intervall_length"),
                min(
                    self.pattern["pattern_intervall_length"],
                    self.config.values.getint("RF-Generator", "pattern_microcontroller_max_intervall_length"),
                ),
            )
            self.pattern_length_val.set(self.pattern["pattern_intervall_length"])
        # a = string.split(self.pattern_pattern_entry_val.get(),";")
        a = self.pattern_pattern_entry_val.get().split(";")
        self.pattern["number_of_generators"] = int(a[0])
        self.pattern["pattern_length"] = int(a[1])
        self.pattern["pattern"] = a[2]
        if len(self.pattern["pattern"]) == self.pattern["number_of_generators"] * 4 * self.pattern["pattern_length"]:
            if self.pattern["controller"] == "computer":
                self.log.debug(
                    "initiate using pattern '%s' with length %d in %d generators"
                    % (
                        self.pattern["pattern"],
                        self.pattern["pattern_length"],
                        self.pattern["number_of_generators"],
                    )
                )
            else:
                self.log.debug(
                    "initiate writing pattern '%s' with length %d to %d generators"
                    % (
                        self.pattern["pattern"],
                        self.pattern["pattern_length"],
                        self.pattern["number_of_generators"],
                    )
                )
            self.rfgc.setpoint["pattern_controller"] = self.pattern["controller"]
            self.rfgc.setpoint["pattern_number_of_generators"] = self.pattern["number_of_generators"]
            self.rfgc.setpoint["pattern_length"] = self.pattern["pattern_length"]
            self.rfgc.setpoint["pattern_intervall_length"] = self.pattern["pattern_intervall_length"]
            self.rfgc.setpoint["pattern"] = self.pattern["pattern"]
            self.rfgc.write_pattern()
            # self.rfgc.setpoint["write_pattern"] = True
        else:
            self.log.warning("cannot write pattern; do not understand setting")

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
            if (
                len(self.pattern["pattern"])
                == self.pattern["number_of_generators"] * 4 * self.pattern["pattern_length"]
            ):
                self.log.info("initiate start pattern run")
                self.rfgc.setpoint["pattern_controller"] = self.pattern["controller"]
                self.rfgc.setpoint["pattern_number_of_generators"] = self.pattern["number_of_generators"]
                self.rfgc.setpoint["pattern_length"] = self.pattern["pattern_length"]
                self.rfgc.setpoint["pattern_intervall_length"] = self.pattern["pattern_intervall_length"]
                self.rfgc.setpoint["pattern"] = self.pattern["pattern"]
                self.rfgc.run_pattern()
                # self.rfgc.setpoint["run_pattern"] = True
            else:
                self.log.warning("cannot initiate pattern run; do not understand setting")
        else:
            # stop running pattern
            self.log.info("initiate stop pattern run")
            self.rfgc.unrun_pattern()
            # self.rfgc.setpoint["run_pattern"] = False

    def btn_open_rfgc(self) -> None:
        self.log.debug("btn_open_rfgc")
        self.gen_frm.grid()
        self.rfgc.start_request()
        self.start_controller_button.configure(state=tkinter.DISABLED)
        self.stop_controller_button.configure(state=tkinter.NORMAL)

    def btn_close_rfgc(self) -> None:
        self.log.debug("btn_close_rfgc")
        self.gen_frm.grid_forget()
        self.rfgc.stop_request()
        self.start_controller_button.configure(state=tkinter.NORMAL)
        self.stop_controller_button.configure(state=tkinter.DISABLED)

    def btn_pwr_on(self) -> None:
        # Power On
        self.log.debug("btn_pwr_on")
        self.combined_change_button1.configure(state=tkinter.DISABLED)
        self.combined_change_button2.configure(state=tkinter.NORMAL)
        for g in range(3):
            if self.gen_frms[g].exists:
                self.gen_frms[g].pwr_on()

    def btn_pwr_off(self) -> None:
        # Power Off
        self.log.debug("btn_pwr_off")
        self.combined_change_button1.configure(state=tkinter.NORMAL)
        self.combined_change_button2.configure(state=tkinter.DISABLED)
        for g in range(3):
            if self.gen_frms[g].exists:
                self.gen_frms[g].pwr_off()

    def btn_rf_on(self) -> None:
        # RF Off
        self.log.debug("btn_rf_on")
        self.combined_change_button3.configure(state=tkinter.DISABLED)
        self.combined_change_button4.configure(state=tkinter.NORMAL)
        for g in range(3):
            if self.gen_frms[g].exists:
                if (self.RF_only_master is False) or (g == 0):
                    self.rfgc.generator[g].rf_on()

    def btn_rf_off(self) -> None:
        # RF On
        self.log.debug("btn_rf_off")
        self.combined_change_button3.configure(state=tkinter.NORMAL)
        self.combined_change_button4.configure(state=tkinter.DISABLED)
        for g in range(3):
            if self.gen_frms[g].exists:
                if (self.RF_only_master is False) or (g == 0):
                    self.rfgc.generator[g].rf_off()

    def ccc(self, a) -> None:
        # change current
        for g in range(3):
            if self.gen_frms[g].exists:
                for i in range(4):
                    current = max(
                        0,
                        min(
                            self.rfgc.generator[g].channel[i].current + a,
                            self.maxcurrent,
                        ),
                    )
                    self.gen_frms[g].sc(current)

    def btn_ignite_plasma(self):
        # ignite plasma
        self.rfgc.ignite()

    # def power(self, g):
    #     if self.generator[g].exists:
    #         if self.generator[g].power_status.get() == 0:
    #             s = False
    #         else:
    #             s = True
    #         self.log.info("switch RF-Generator power to %s" % b2onoff(s))
    #         self.controller[self.generator[g].power_controller].setpoint[
    #             self.generator[g].power_port
    #         ][int(self.generator[g].power_channel)] = s

    # def check_buttons(self):
    #     if self.pattern_controller_var.get() == "microcontroller":
    #         self.pattern_write_button.configure(state=tkinter.NORMAL)
    #     else:
    #         self.pattern_write_button.configure(state=tkinter.DISABLED)
    #     # if self.controller["dc"].connected:
    #     #     for g in range(3):
    #     #         if self.generator[g].exists:
    #     #             self.generator[g].power_status_checkbutton.configure(state=tkinter.NORMAL)
    #     # else:
    #     #     for g in range(3):
    #     #         if self.generator[g].exists:
    #     #             self.generator[g].power_status_checkbutton.configure(state=tkinter.DISABLED)
    #     if self.rfgc.actualvalue["connect"]:
    #         self.start_controller_button.configure(state=tkinter.DISABLED)
    #         self.stop_controller_button.configure(state=tkinter.NORMAL)
    #         self.ignite_plasma_button.configure(state=tkinter.NORMAL)
    #         # self.info1.configure(state=tkinter.NORMAL)
    #         # self.info2.configure(state=tkinter.NORMAL)
    #         self.info3.configure(state=tkinter.NORMAL)
    #         self.combined_change_button1.configure(state=tkinter.NORMAL)
    #         self.combined_change_button2.configure(state=tkinter.NORMAL)
    #         self.combined_change_button3.configure(state=tkinter.NORMAL)
    #         self.combined_change_button4.configure(state=tkinter.NORMAL)
    #         self.combined_change_button5.configure(state=tkinter.NORMAL)
    #         self.combined_change_button6.configure(state=tkinter.NORMAL)
    #         self.combined_change_button7.configure(state=tkinter.NORMAL)
    #         self.combined_change_button8.configure(state=tkinter.NORMAL)
    #         self.combined_change_button9.configure(state=tkinter.NORMAL)
    #         self.combined_change_button10.configure(state=tkinter.NORMAL)
    #         # for g in range(3):
    #         #     if self.generator[g].exists:
    #         #         for i in range(4):
    #         #             self.generator[g].channel[i].onoff_status_checkbutton.configure(
    #         #                 state=tkinter.NORMAL
    #         #             )
    #         #             self.generator[g].channel[i].current_status_entry.configure(
    #         #                 state=tkinter.NORMAL
    #         #             )
    #         #             self.generator[g].channel[i].phase_status_entry.configure(
    #         #                 state=tkinter.NORMAL
    #         #             )
    #         #             self.generator[g].channel[i].choose_checkbutton.configure(
    #         #                 state=tkinter.NORMAL
    #         #             )
    #     else:
    #         self.start_controller_button.configure(state=tkinter.NORMAL)
    #         self.stop_controller_button.configure(state=tkinter.DISABLED)
    #         self.ignite_plasma_button.configure(state=tkinter.DISABLED)
    #         # self.info1.configure(state=tkinter.DISABLED)
    #         # self.info2.configure(state=tkinter.DISABLED)
    #         self.info3.configure(state=tkinter.DISABLED)
    #         self.combined_change_button1.configure(state=tkinter.DISABLED)
    #         self.combined_change_button2.configure(state=tkinter.DISABLED)
    #         self.combined_change_button3.configure(state=tkinter.DISABLED)
    #         self.combined_change_button4.configure(state=tkinter.DISABLED)
    #         self.combined_change_button5.configure(state=tkinter.DISABLED)
    #         self.combined_change_button6.configure(state=tkinter.DISABLED)
    #         self.combined_change_button7.configure(state=tkinter.DISABLED)
    #         self.combined_change_button8.configure(state=tkinter.DISABLED)
    #         self.combined_change_button9.configure(state=tkinter.DISABLED)
    #         self.combined_change_button10.configure(state=tkinter.DISABLED)
    #         # for g in range(3):
    #         #     if self.generator[g].exists:
    #         #         for i in range(4):
    #         #             self.generator[g].channel[i].onoff_status_checkbutton.configure(
    #         #                 state=tkinter.DISABLED
    #         #             )
    #         #             self.generator[g].channel[i].current_status_entry.configure(
    #         #                 state=tkinter.DISABLED
    #         #             )
    #         #             self.generator[g].channel[i].phase_status_entry.configure(
    #         #                 state=tkinter.DISABLED
    #         #             )
    #         #             self.generator[g].channel[i].choose_checkbutton.configure(
    #         #                 state=tkinter.DISABLED
    #         #             )


if __name__ == "__main__":
    pass
