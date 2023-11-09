#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 Daniel Mohr
#
# Copyright (C) 2023 Egor Perevoshchikov
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
gui for Diagnostics/Particles
"""

import re
import logging
import tkinter as tk
from tkinter import ttk
from turtle import back
from typing import Dict, Any

from .base_controller import CTRL
from .utils import Master
from .read_config_file import read_config_file
from ..plc_tools.conversion import b2onoff
from .misc import except_notify


class Laser:
    def __init__(self, configs: read_config_file, log: logging.Logger, controller: Dict[str, CTRL]) -> None:
        self.configs = configs
        self.log = log
        self.controller = controller
        self.lpc = self.controller[self.configs.values.get("laser", "laser_power_status_controller")]
        self.lpp = self.configs.values.get("laser", "laser_power_status_port")
        self.lpca = self.configs.values.getint("laser", "laser_power_status_channel")

        self.l1pc = self.controller[self.configs.values.get("laser", "laser1_power_status_controller")]
        self.l1pp = self.configs.values.get("laser", "laser1_power_status_port")
        self.l1pca = self.configs.values.getint("laser", "laser1_power_status_channel")

        self.l1dvc = self.controller[self.configs.values.get("laser", "laser1_diode_voltage_controller")]
        self.l1dvp = self.configs.values.get("laser", "laser1_diode_voltage_port")
        self.l1dvca = self.configs.values.getint("laser", "laser1_diode_voltage_channel")

        self.l1dcc = controller[self.configs.values.get("laser", "laser1_diode_current_controller")]
        self.l1dcp = self.configs.values.get("laser", "laser1_diode_current_port")
        self.l1dcca = self.configs.values.getint("laser", "laser1_diode_current_channel")

        self.l2pc = self.controller[self.configs.values.get("laser", "laser2_power_status_controller")]
        self.l2pp = self.configs.values.get("laser", "laser2_power_status_port")
        self.l2pca = self.configs.values.getint("laser", "laser2_power_status_channel")

        self.l2dvc = self.controller[self.configs.values.get("laser", "laser2_diode_voltage_controller")]
        self.l2dvp = self.configs.values.get("laser", "laser2_diode_voltage_port")
        self.l2dvca = self.configs.values.getint("laser", "laser2_diode_voltage_channel")

        self.l2dcc = controller[self.configs.values.get("laser", "laser2_diode_current_controller")]
        self.l2dcp = self.configs.values.get("laser", "laser2_diode_current_port")
        self.l2dcca = self.configs.values.getint("laser", "laser2_diode_current_channel")

        self.resistance = self.configs.values.getfloat("laser", "R")
        self.current_offset = self.configs.values.getfloat("laser", "I_offset")
        self.current_scale = self.configs.values.getfloat("laser", "I_scale")

    def laser(self, s: bool) -> None:
        self.log.debug("switch laser power to %s" % b2onoff(s))

        self.lpc.lock.acquire()
        self.lpc.setpoint[self.lpp][self.lpca] = s
        self.lpc.lock.release()

    def laser1(self, s: bool) -> None:
        self.log.debug("switch laser1 power to %s" % b2onoff(s))

        self.l1pc.lock.acquire()
        self.l1pc.setpoint[self.l1pp][self.l1pca] = s
        self.l1pc.lock.release()

    def laser1_set_diode_voltage(self, v: float) -> float:
        # X = 0 ... 10 V
        v = max(0.0, min(v, 10.0))
        self.l1dvc.lock.acquire()
        try:
            self.l1dvc.setpoint[self.l1dvp][self.l1dvca] = v
            self.log.debug("set diode voltage from laser 1 to %.2f" % v)
        except Exception:
            self.l1dvc.setpoint[self.l1dvp] = v
            self.log.debug("set diode voltage from laser 1 to %.2f" % v)
        self.l1dvc.lock.release()
        return v

    def laser2(self, s: bool) -> None:
        self.log.debug("switch laser2 power to %s" % b2onoff(s))

        self.l2pc.lock.acquire()
        self.l2pc.setpoint[self.l2pp][self.l2pca] = s
        self.l2pc.lock.release()

    def laser2_set_diode_voltage(self, v: float) -> float:
        # X = 0 ... 10 V
        v = max(0.0, min(v, 10.0))
        self.l2dvc.lock.acquire()
        try:
            self.l2dvc.setpoint[self.l2dvp][self.l2dvca] = v
            self.log.debug("set diode voltage from laser 2 to %.2f" % v)
        except Exception:
            self.l2dvc.setpoint[self.l2dvp] = v
            self.log.debug("set diode voltage from laser 2 to %.2f" % v)
        self.l2dvc.lock.release()
        return v

    def laser_status(self) -> bool:
        return self.lpc.actualvalue[self.lpp][self.lpca]

    def laser1_status(self) -> bool:
        return self.l1pc.actualvalue[self.l1pp][self.l1pca]

    def laser2_status(self) -> bool:
        return self.l2pc.actualvalue[self.l2pp][self.l2pca]

    def laser1_voltage(self) -> float:
        return self.l1dvc.actualvalue[self.l1dvp][self.l1dvca]

    def laser2_voltage(self) -> float:
        return self.l2dvc.actualvalue[self.l2dvp][self.l2dvca]

    def laser1_current(self) -> float:
        return self.l1dcc.actualvalue[self.l1dcp][self.l1dcca] / self.resistance

    def laser2_current(self) -> float:
        return self.l2dcc.actualvalue[self.l2dcp][self.l2dcca] / self.resistance

    def laser1_power(self) -> float:
        i = self.laser1_current()
        if i < self.current_offset:
            return 0
        else:
            return (i - self.current_offset) * self.current_scale

    def laser2_power(self) -> float:
        i = self.laser2_current()
        if i < self.current_offset:
            return 0
        else:
            return (i - self.current_offset) * self.current_scale


class laser_gui(ttk.LabelFrame, Master):
    def __init__(self, _root: ttk.LabelFrame, backend: Laser, master: Master) -> None:
        ttk.LabelFrame.__init__(self, _root, text="Laser")
        self.backend = backend
        Master.__init__(self, master, custom_name="laser")

        vcmd = (self.register(self.validate), "%P", "%W")
        ivcmd = (self.register(self.on_invalid), "%W")

        self.laser_frame_0 = ttk.Label(self)
        self.laser_frame_0.grid(column=0, row=0)
        self.laser1_frame = ttk.Label(self)
        self.laser1_frame.grid(column=1, row=0)
        self.laser2_frame = ttk.Label(self)
        self.laser2_frame.grid(column=1, row=1)
        self.laser_status = tk.IntVar()
        self.laser_checkbutton = ttk.Checkbutton(
            self.laser_frame_0,
            text="Laser Power",
            command=self.laser,
            variable=self.laser_status,
            state=tk.DISABLED,
        )
        self.laser_checkbutton.grid(row=1, column=0)
        self.laser_status_val = tk.StringVar()
        self.laser_status_val_label = ttk.Label(self.laser_frame_0, textvariable=self.laser_status_val, width=3)
        self.laser_status_val.set("val")
        self.laser_status_val_label.grid(row=1, column=1)
        # Laser 1
        self.laser1_status = tk.IntVar()
        self.laser1_checkbutton = ttk.Checkbutton(
            self.laser1_frame,
            text="Laser 1",
            command=self.laser1,
            variable=self.laser1_status,
            state=tk.DISABLED,
            offvalue=False,
            onvalue=True,
        )
        self.laser1_checkbutton.grid(column=0, row=0)
        self.laser1_status_val = tk.StringVar()
        self.laser1_status_label = ttk.Label(self.laser1_frame, textvariable=self.laser1_status_val, width=5)
        self.laser1_status_val.set("val")
        self.laser1_status_label.grid(column=1, row=0)
        self.laser1_set_diode_voltage_val = tk.DoubleVar()
        self.laser1_set_diode_voltage_entry = ttk.Entry(
            self.laser1_frame, textvariable=self.laser1_set_diode_voltage_val, width=6, name="l1dve", state=tk.DISABLED
        )
        self.laser1_set_diode_voltage_entry.grid(column=2, row=0)
        self.laser1_set_diode_voltage_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
        self.laser1_set_diode_voltage_button = ttk.Button(
            self.laser1_frame, command=self.laser1_set_diode_voltage, text="set V", state=tk.DISABLED
        )
        self.laser1_set_diode_voltage_button.grid(column=3, row=0)
        self.laser1_diode_voltage_label1 = ttk.Label(self.laser1_frame, text="Voltage: ")
        self.laser1_diode_voltage_label1.grid(column=4, row=0)
        self.laser1_diode_voltage_val = tk.StringVar()
        self.laser1_diode_voltage_label = ttk.Label(
            self.laser1_frame, textvariable=self.laser1_diode_voltage_val, width=8
        )
        self.laser1_diode_voltage_val.set("0")
        self.laser1_diode_voltage_label.grid(column=5, row=0)
        self.laser1_diode_current_label1 = ttk.Label(self.laser1_frame, text="Current: ")
        self.laser1_diode_current_label1.grid(column=6, row=0)
        self.laser1_diode_current_val = tk.StringVar()
        self.laser1_diode_current_label = ttk.Label(
            self.laser1_frame, textvariable=self.laser1_diode_current_val, width=11
        )
        self.laser1_diode_current_val.set("0")
        self.laser1_diode_current_label.grid(column=7, row=0)
        self.laser1_diode_power_label1 = ttk.Label(self.laser1_frame, text="Power: ")
        self.laser1_diode_power_label1.grid(column=8, row=0)
        self.laser1_diode_power_val = tk.StringVar()
        self.laser1_diode_power_label = ttk.Label(self.laser1_frame, textvariable=self.laser1_diode_power_val, width=9)
        self.laser1_diode_power_val.set("0")
        self.laser1_diode_power_label.grid(column=9, row=0)
        # Laser 2
        self.laser2_status = tk.IntVar()
        self.laser2_checkbutton = ttk.Checkbutton(
            self.laser2_frame,
            text="Laser 2",
            command=self.laser2,
            variable=self.laser2_status,
            state=tk.DISABLED,
            offvalue=False,
            onvalue=True,
        )
        self.laser2_checkbutton.grid(column=0, row=0)
        self.laser2_status_val = tk.StringVar()
        self.laser2_status_label = ttk.Label(self.laser2_frame, textvariable=self.laser2_status_val, width=5)
        self.laser2_status_val.set("val")
        self.laser2_status_label.grid(column=1, row=0)
        self.laser2_set_diode_voltage_val = tk.DoubleVar()
        self.laser2_set_diode_voltage_entry = ttk.Entry(
            self.laser2_frame, textvariable=self.laser2_set_diode_voltage_val, width=6, name="l2dve", state=tk.DISABLED
        )
        self.laser2_set_diode_voltage_entry.grid(column=2, row=0)
        self.laser2_set_diode_voltage_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
        self.laser2_set_diode_voltage_button = ttk.Button(
            self.laser2_frame, command=self.laser2_set_diode_voltage, text="set V", state=tk.DISABLED
        )
        self.laser2_set_diode_voltage_button.grid(column=3, row=0)
        self.laser2_diode_voltage_label1 = ttk.Label(self.laser2_frame, text="Voltage: ")
        self.laser2_diode_voltage_label1.grid(column=4, row=0)
        self.laser2_diode_voltage_val = tk.StringVar()
        self.laser2_diode_voltage_label = ttk.Label(
            self.laser2_frame, textvariable=self.laser2_diode_voltage_val, width=8
        )
        self.laser2_diode_voltage_val.set("0")
        self.laser2_diode_voltage_label.grid(column=5, row=0)
        self.laser2_diode_current_label1 = ttk.Label(self.laser2_frame, text="Current: ")
        self.laser2_diode_current_label1.grid(column=6, row=0)
        self.laser2_diode_current_val = tk.StringVar()
        self.laser2_diode_current_label = ttk.Label(
            self.laser2_frame, textvariable=self.laser2_diode_current_val, width=11
        )
        self.laser2_diode_current_val.set("0")
        self.laser2_diode_current_label.grid(column=7, row=0)
        self.laser2_diode_power_label1 = ttk.Label(self.laser2_frame, text="Power: ")
        self.laser2_diode_power_label1.grid(column=8, row=0)
        self.laser2_diode_power_val = tk.StringVar()
        self.laser2_diode_power_label = ttk.Label(self.laser2_frame, textvariable=self.laser2_diode_power_val, width=9)
        self.laser2_diode_power_val.set("0")
        self.laser2_diode_power_label.grid(column=9, row=0)

    def validate(self, _value, _widget) -> bool:
        widget_name = _widget.split(".")[-1].strip()
        try:
            try:
                volts = int(_value)
            except Exception:
                return False
            if 0 <= volts and volts <= 10:
                m, g, r = tk.NORMAL, "green", True
            else:
                m, g, r = tk.DISABLED, "red", False
            if widget_name == "l1dve":
                self.laser1_set_diode_voltage_button.configure(state=m)
                self.laser1_set_diode_voltage_entry.configure(background=g)
            elif widget_name == "l2dve":
                self.laser2_set_diode_voltage_button.configure(state=m)
                self.laser2_set_diode_voltage_entry.configure(background=g)
            else:
                raise RuntimeError("Software bug in validate channel entries, widget not found")
            return r
        except RuntimeError as e:
            except_notify.show(e, f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            self.log.exception(f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            raise

    def on_invalid(self, widget) -> None:
        widget_name = widget.split(".")[-1].strip()
        if widget_name == "l1dve":
            self.laser1_set_diode_voltage_button.configure(state=tk.DISABLED)
            self.laser1_set_diode_voltage_entry.configure(background="red")
        elif widget_name == "l2dve":
            self.laser2_set_diode_voltage_button.configure(state=tk.DISABLED)
            self.laser2_set_diode_voltage_entry.configure(background="red")

    def laser(self) -> None:
        if self.laser_status.get() == 0:
            s = False
        else:
            s = True
        self.backend.laser(s)

    def laser1(self) -> None:
        if self.laser1_status.get() == 0:
            s = False
        else:
            s = True
        self.backend.laser1(s)

    def laser2(self) -> None:
        if self.laser2_status.get() == 0:
            s = False
        else:
            s = True
        self.backend.laser2(s)

    def laser1_set_diode_voltage(self) -> None:
        v = float(self.laser1_set_diode_voltage_val.get())
        v = self.backend.laser1_set_diode_voltage(v)
        self.laser1_set_diode_voltage_val.set(round(v, 2))
        self.laser1_set_diode_voltage_button.configure(state=tk.DISABLED)

    def laser2_set_diode_voltage(self) -> None:
        v = float(self.laser2_set_diode_voltage_val.get())
        v = self.backend.laser2_set_diode_voltage(v)
        self.laser2_set_diode_voltage_val.set(round(v, 2))

    def upd(self) -> None:
        """update every dynamic read values"""
        self.laser_checkbutton.configure(state=tk.NORMAL if self.backend.lpc.connected else tk.DISABLED)
        self.laser_status_val.set(b2onoff(self.backend.laser_status()))

        self.laser1_checkbutton.configure(state=tk.NORMAL if self.backend.l1pc.connected else tk.DISABLED)
        self.laser1_set_diode_voltage_entry.configure(state=tk.NORMAL if self.backend.l1dvc.connected else tk.DISABLED)
        self.laser1_set_diode_voltage_button.configure(state=tk.NORMAL if self.backend.l1dvc.connected else tk.DISABLED)

        self.laser1_status_val.set(b2onoff(self.backend.laser1_status()))
        self.laser1_diode_voltage_val.set("%.2f V" % (self.backend.laser1_voltage()))
        self.laser1_diode_current_val.set("%.2f mA" % self.backend.laser1_current() * 1000)
        self.laser1_diode_power_val.set("%.2f mW" % self.backend.laser1_power() * 1000)

        self.laser2_checkbutton.configure(state=tk.NORMAL if self.backend.l2pc.connected else tk.DISABLED)
        self.laser2_set_diode_voltage_entry.configure(state=tk.NORMAL if self.backend.l2dvc.connected else tk.DISABLED)
        self.laser2_set_diode_voltage_button.configure(state=tk.NORMAL if self.backend.l2dvc.connected else tk.DISABLED)

        self.laser2_status_val.set(b2onoff(self.backend.laser2_status()))
        self.laser2_diode_voltage_val.set("%.2f V" % (self.backend.laser2_voltage()))
        self.laser2_diode_current_val.set("%.2f mA" % self.backend.laser2_current() * 1000)
        self.laser2_diode_power_val.set("%.2f mW" % self.backend.laser2_power() * 1000)


class dispenser:
    def __init__(self, configs: read_config_file, log: logging.Logger, num: int, controller: Dict[str, CTRL]) -> None:
        self.configs = configs
        self.name = f"dispenser{num}"
        self.n = num
        self.exists = self.configs.values.get(self.name, "controller") != "-1"
        if self.exists:
            self.controller = controller[self.configs.values.get(self.name, "controller")]
            self.port = self.configs.values.get(self.name, "port")
            self.channel = self.configs.values.getint(self.name, "channel")
            self.shakes = self.configs.values.getint(self.name, "shakes")
            self.Toff = self.configs.values.getfloat(self.name, "Toff")
            self.Ton = self.configs.values.getfloat(self.name, "Ton")

    def shake(self) -> None:
        self.controller.lock.acquire()
        self.controller.setpoint["dispenser"]["port"] = self.port
        self.controller.setpoint["dispenser"]["channel"] = self.channel
        self.controller.setpoint["dispenser"]["n"] = self.shakes
        self.controller.setpoint["dispenser"]["toff"] = self.Toff / 1000
        self.controller.setpoint["dispenser"]["ton"] = self.Ton / 1000.0
        self.controller.setpoint["dispenser"]["shake"] = True
        self.controller.lock.release()


class dispenser_gui(ttk.LabelFrame, Master):
    def __init__(self, _root: ttk.LabelFrame, backend: dispenser, master: Master) -> None:
        ttk.LabelFrame.__init__(self, _root, text=backend.name)
        self.backend = backend
        Master.__init__(self, master, custom_name=backend.name)

        vcmd = (self.register(self.validate), "%P", "%W")
        ivcmd = (self.register(self.on_invalid), "%W")
        self.valid_fields = 0

        if self.backend.exists:
            # self.label1 = ttk.Label(self, text="%s: " % self.backend.name)
            # self.label1.grid(column=0, row=0)
            self.shakes = tk.IntVar()
            self.shakes.set(int(self.backend.shakes))
            self.shakes_entry = ttk.Entry(self, textvariable=self.shakes, width=3, state=tk.DISABLED, name="shakes")
            self.shakes_entry.grid(column=0, row=0)
            self.shakes_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
            self.shakes_label = ttk.Label(self, text="shakes. ")
            self.shakes_label.grid(column=1, row=0)
            self.Ton = tk.IntVar()
            self.Ton.set(int(self.backend.Ton))
            self.Ton_label1 = ttk.Label(self, text="T_on: ")
            self.Ton_label1.grid(column=2, row=0)
            self.Ton_entry = ttk.Entry(self, textvariable=self.Ton, width=5, state=tk.DISABLED, name="ton")
            self.Ton_entry.grid(column=3, row=0)
            self.Ton_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
            self.Ton_label = ttk.Label(self, text="ms. ")
            self.Ton_label.grid(column=4, row=0)
            self.Toff = tk.IntVar()
            self.Toff.set(int(self.backend.Toff))
            self.Toff_label1 = ttk.Label(self, text="T_off: ")
            self.Toff_label1.grid(column=5, row=0)
            self.Toff_entry = ttk.Entry(self, textvariable=self.Toff, width=5, state=tk.DISABLED, name="toff")
            self.Toff_entry.grid(column=6, row=0)
            self.Toff_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
            self.Toff_label = ttk.Label(self, text="ms. ")
            self.Toff_label.grid(column=7, row=0)

            self.btn_shake = ttk.Button(
                self,
                command=self.shake,
                state=tk.DISABLED,
                text="do the shake",
            )
            self.btn_shake.grid(column=8, row=0)

        if self.configs.values.get("dispensers", f"key_binding_dispenser{self.backend.n}") != "-1":
            self.bind(self.configs.values.get("dispensers", f"key_binding_dispenser{self.backend.n}"), self.shake)

    def validate(self, _value, _widget) -> bool:
        widget_name = _widget.split(".")[-1].strip()
        try:
            if widget_name == "shakes":
                if not re.match(r"^\d+$", _value):
                    return False
                try:
                    value = int(_value)
                except Exception:
                    return False
                self.shakes_entry.configure(background="green")
            elif widget_name == "ton":
                if not (re.match(r"^\d+$", _value) or re.match(r"^\d+\.\d+$", _value)):
                    return False
                try:
                    value = float(_value)
                except Exception:
                    return False
                self.Ton_entry.configure(background="green")
            elif widget_name == "toff":
                if not (re.match(r"^\d+$", _value) or re.match(r"^\d+\.\d+$", _value)):
                    return False
                try:
                    value = float(_value)
                except Exception:
                    return False
                self.Toff_entry.configure(background="green")
            else:
                raise RuntimeError("Software bug in validate channel entries, widget not found")
            self.valid_fields += 1
            if self.valid_fields == 3:
                self.btn_shake.configure(state=tk.NORMAL)
            return True
        except RuntimeError as e:
            except_notify.show(e, f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            self.log.exception(f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            raise

    def on_invalid(self, widget) -> None:
        widget_name = widget.split(".")[-1].strip()
        self.valid_fields -= 1
        self.btn_shake.configure(state=tk.DISABLED)
        if widget_name == "shakes":
            self.shakes_entry.configure(background="red")
        elif widget_name == "ton":
            self.Ton_entry.configure(background="red")
        elif widget_name == "toff":
            self.Toff_entry.configure(background="red")

    def shake(self, ev=None) -> None:
        self.backend.shakes = self.shakes.get()
        self.backend.Toff = self.Toff.get()
        self.backend.Ton = self.Ton.get()

        self.backend.shake()

    def upd(self) -> None:
        if self.backend.exists:
            if self.backend.controller.connected:
                self.btn_shake.configure(state=tk.NORMAL)
                self.shakes_entry.configure(state=tk.NORMAL)
                self.Ton_entry.configure(state=tk.NORMAL)
                self.Toff_entry.configure(state=tk.NORMAL)
        else:
            if self.backend.controller.connected:
                self.btn_shake.configure(state=tk.DISABLED)
                self.shakes_entry.configure(state=tk.DISABLED)
                self.Ton_entry.configure(state=tk.DISABLED)
                self.Toff_entry.configure(state=tk.DISABLED)


class diagnostic_particles(ttk.LabelFrame, Master):
    """
    gui for Diagnostics/Particles
    """

    def __init__(self, _root: ttk.Frame, master: Master, controller: Dict[str, CTRL]) -> None:
        """
        create gui for Diagnostics/Particles
        """
        ttk.LabelFrame.__init__(self, _root, text="Diagnostics/Particles")
        Master.__init__(self, master, custom_name="DLP")

        self.laser = Laser(self.configs, self.log.getChild("Laser"), controller)
        self.laser_gui = laser_gui(self, self.laser, self)
        self.laser_gui.pack()

        self.disps = ttk.LabelFrame(self, text="Particles")
        self.disps.pack()
        dispensoren = ["dispenser1", "dispenser2", "dispenser3"]

        for i, d in enumerate(dispensoren):
            if self.configs.values.get(d, "controller") != "-1":
                disp = dispenser(self.configs, self.log.getChild(d), i + 1, controller)
                dsp = dispenser_gui(self.disps, disp, self)
                dsp.pack()
