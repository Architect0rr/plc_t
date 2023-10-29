#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Daniel Mohr and PlasmaLab (FKZ 50WP0700 and FKZ 50WM1401)
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
class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator
"""

import time
import serial
import logging
import functools
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Annotated, Callable, TypeVar
import tkinter as tk
from tkinter import ttk

from .read_config_file import read_config_file
from .controller import controller
from .misc import except_notify
from .utils import Master


T = TypeVar("T")


@dataclass
class ValueRange:
    lo: int
    hi: int


d_bits: Dict[int, int] = {
    5: serial.FIVEBITS,
    6: serial.SIXBITS,
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS,
}
s_bits: Dict[str, float] = {
    "1": serial.STOPBITS_ONE,
    "1.5": serial.STOPBITS_ONE_POINT_FIVE,
    "2": serial.STOPBITS_TWO,
}


class EVENTS(Enum):
    ONOFF = 1
    current = 2
    phase = 3


class class_channel:
    """
    class for one channel of the generator
    """

    def __init__(self, cn: int, hndlr: Callable[[EVENTS], None], _log: logging.Logger) -> None:
        self.log = _log
        self._onoff: bool = False  # True if on
        self._hndlr = hndlr
        self.n = cn
        # self.log.info(f"Chan{self.n} init")
        self._current: Annotated[int, ValueRange(0, 4095)] = 0  # 0 <= current <= 4095
        self._phase: Annotated[int, ValueRange(0, 255)] = 0  # 0 <= phase <= 255'

    def _onoff_write(self) -> None:
        self._hndlr(EVENTS.ONOFF)

    @property
    def onoff(self) -> bool:
        return self._onoff

    @onoff.setter
    def onoff(self, value: bool) -> None:
        self._onoff = value
        self.log.debug(f"Chan{self.n} onoff changed to {value}, writting to device")
        self._onoff_write()

    def _current_write(self) -> None:
        self._hndlr(EVENTS.current)

    @property
    def current(self) -> int:
        return self._current

    @current.setter
    def current(self, value: int) -> None:
        self._current = value
        self.log.debug(f"Chan{self.n} current changed to {value}, writting to device")
        self._current_write()

    def _phase_write(self) -> None:
        self._hndlr(EVENTS.phase)

    @property
    def phase(self) -> int:
        return self._phase

    @phase.setter
    def phase(self, value: int) -> None:
        self._phase = value
        self.log.debug(f"Chan{self.n} phase changed to {value}, writting to device")
        self._phase_write()


class cc_gui(ttk.Frame):
    def __init__(self, _root: ttk.LabelFrame, backend: class_channel, _log: logging.Logger) -> None:
        super().__init__(_root)
        self.log = _log
        self.current_bonds = (0, 4095)
        self.phase_bonds = (0, 255)
        self.backend = backend
        self.onoff_status: tk.IntVar = tk.IntVar()
        self.onoff_status_checkbutton: tk.Checkbutton = tk.Checkbutton(
            self,
            text=f"Pwr Channel {backend.n}",
            command=self.btn_onoff,
            variable=self.onoff_status,
            state=tk.DISABLED,
        )
        self.onoff_status_checkbutton.grid(column=0, row=backend.n)

        vcmd = (self.register(self.validate), "%P", "%W")
        ivcmd = (self.register(self.on_invalid), "%W")
        self.current_status: tk.IntVar = tk.IntVar()
        self.current_status_entry: tk.Entry = tk.Entry(
            self, name="current", textvariable=self.current_status, width=5, state=tk.DISABLED
        )
        self.current_status_entry.grid(column=2, row=backend.n)
        self.current_status_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)

        self.phase_status: tk.IntVar = tk.IntVar()
        self.phase_status_entry: tk.Entry = tk.Entry(
            self, name="phase", textvariable=self.phase_status, width=4, state=tk.DISABLED
        )
        self.phase_status_entry.grid(column=4, row=backend.n)
        self.phase_status_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)

        self.choose: tk.IntVar = tk.IntVar()
        self.choose_checkbutton: tk.Checkbutton = tk.Checkbutton(
            self, text=f"Channel {backend.n}", variable=self.choose
        )
        self.choose_checkbutton.grid(column=6, row=backend.n)
        self.choose_checkbutton.select()
        self.button_set: ttk.Button = ttk.Button(self, text="Set", command=self.__set, state=tk.DISABLED)
        self.button_set.grid(column=7, row=backend.n)

    def __set(self) -> None:
        self.button_set.configure(state=tk.DISABLED)
        self.backend.current = int(self.current_status_entry.get())
        self.backend.phase = int(self.phase_status_entry.get())

    def btn_onoff(self) -> None:
        self.log.debug("On/off button")
        self.backend.onoff = not self.backend.onoff

    def pwr_on(self) -> bool:
        self.log.debug("Checking for power on")
        if self.choose.get() == 1:
            self.log.debug("Powered on")
            self.onoff_status_checkbutton.select()
            return True
        else:
            self.log.debug("Channel not selected")
            return False

    def pwr_off(self) -> bool:
        self.log.debug("Checking for power off")
        if self.choose.get() == 1:
            self.log.debug("Powered off")
            self.onoff_status_checkbutton.deselect()
            return True
        else:
            self.log.debug("Channel not selected")
            return False

    def sc(self, current) -> bool:
        if self.choose.get() == 1:
            self.current_status.set(max(self.current_bonds[0], min(current, self.current_bonds[1])))
            return True
        return False

    def validate(self, _value, _widget) -> bool:
        widget_name = _widget.split(".")[-1].strip()
        try:
            if widget_name == "current":
                try:
                    current = int(_value)
                except Exception:
                    return False
                if 0 <= current and current <= 4095:
                    # self.backend.current = current
                    self.button_set.configure(state=tk.NORMAL)
                    self.current_status_entry.configure(background="green")
                    return True
                else:
                    self.button_set.configure(state=tk.DISABLED)
                    self.current_status_entry.configure(background="red")
                    return False
            elif widget_name == "phase":
                try:
                    phase = int(_value)
                except Exception:
                    return False
                if 0 <= phase and phase <= 255:
                    # self.backend.phase = phase
                    self.button_set.configure(state=tk.NORMAL)
                    self.phase_status_entry.configure(background="green")
                    return True
                else:
                    self.button_set.configure(state=tk.DISABLED)
                    self.phase_status_entry.configure(background="red")
                    return False
            else:
                raise RuntimeError("Software bug in validate channel entries, widget not found")
        except RuntimeError as e:
            except_notify.show(e, f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            self.log.exception(f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            raise

    def on_invalid(self, widget):
        if widget == "current":
            self.current_status_entry["backgroud"] = "red"
        elif widget == "phase":
            self.phase_status_entry["backgroud"] = "red"


def if_exists(fn: Callable[..., bool]):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> bool:
        self: class_rf_generator = args[0]
        if self.exists:
            return fn(*args, **kwargs)
        else:
            self.log.warning("Attempt to deal with non-existent rf-gen")
            return False

    return wrapper


def if_exists_non(fn: Callable[..., T]):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T | None:
        self: class_rf_generator = args[0]
        if self.exists:
            return fn(*args, **kwargs)
        else:
            self.log.warning("Attempt to deal with non-existent rf-gen")
            return None

    return wrapper


def if_gen_enabled(fn: Callable[..., bool]):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> bool:
        self: class_rf_generator = args[0]
        if self.gen_enabled:
            return fn(*args, **kwargs)
        else:
            self.log.warning("Attempt to deal with non-existent rf-gen")
            return False

    return wrapper


def if_gen_enabled_non(fn: Callable[..., T]):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T | None:
        self: class_rf_generator = args[0]
        if self.gen_enabled:
            return fn(*args, **kwargs)
        else:
            self.log.warning("Attempt to deal with non-existent rf-gen")
            return None

    return wrapper


def if_dc_enabled(fn: Callable[..., bool]):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> bool:
        self: class_rf_generator = args[0]
        if self.dc_enabled:
            return fn(*args, **kwargs)
        else:
            self.log.warning("Attempt to deal with non-existent rf-gen")
            return False

    return wrapper


def if_dc_enabled_non(fn: Callable[..., T]):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T | None:
        self: class_rf_generator = args[0]
        if self.dc_enabled:
            return fn(*args, **kwargs)
        else:
            self.log.warning("Attempt to deal with non-existent rf-gen")
            return None

    return wrapper


class class_rf_generator:
    """
    class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator
    """

    def __init__(
        self, exists: bool, number: int, config: read_config_file, _log: logging.Logger, pwc: controller
    ) -> None:
        """
        init of class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator
        """
        self.exists = exists
        self.log = _log
        if self.exists:
            self.number = number
            self.pwc = pwc
            self.power_controller: str = config.values.get(f"RF-Generator {number + 1}", "power_controller")
            self.power_port: str = config.values.get(f"RF-Generator {number + 1}", "power_port")
            self.power_channel: int = config.values.getint(f"RF-Generator {number + 1}", "power_channel")

            self.channel: List[class_channel] = []
            for i in range(4):
                cn = self.number * 4 + i
                self.channel.append(class_channel(cn, self.channel_handler, self.log.getChild(f"chan{cn}")))

            self.actualvalue_pattern: str = ""
            self.device = None
            self.gen_enabled: bool = False  # connected and on
            self.dc_enabled: bool = False  # connected and on
            self.update_intervall = config.values.getfloat(f"RF-Generator {number + 1}", "update_intervall")
            self.gen_device: str = config.values.get(f"RF-Generator {number + 1}", "gen_device")
            self.dc_device: str = config.values.get(f"RF-Generator {number + 1}", "dc_device")
            self.boudrate: int = config.values.getint(f"RF-Generator {number + 1}", "boudrate")
            self.databits: int = d_bits[config.values.getint(f"RF-Generator {number + 1}", "databits")]
            self.parity = serial.PARITY_NONE
            self.stopbits: float = s_bits[config.values.get(f"RF-Generator {number + 1}", "stopbits")]
            self.readtimeout: float = config.values.getfloat(f"RF-Generator {number + 1}", "readtimeout")
            self.writetimeout: float = config.values.getfloat(f"RF-Generator {number + 1}", "writetimeout")
            # return
            self.readbytes = 4096
            # self.dev_gen = serial.Serial(
            #     port=self.gen_device,
            #     baudrate=self.boudrate,
            #     bytesize=self.databits,
            #     parity=self.parity,
            #     stopbits=self.stopbits,
            #     timeout=self.readtimeout,
            #     write_timeout=self.writetimeout,
            # )
            # self.dev_dc = serial.Serial(
            #     port=self.dc_device,
            #     baudrate=self.boudrate,
            #     bytesize=self.databits,
            #     parity=self.parity,
            #     stopbits=self.stopbits,
            #     timeout=self.readtimeout,
            #     write_timeout=self.writetimeout,
            # )

    @if_exists_non
    @if_gen_enabled_non
    def read_gen(self) -> None:
        self.log.info(f"From rf-gen {self.number}: {self.dev_gen.read(self.readbytes).decode('utf-8')}")

    @if_exists_non
    @if_dc_enabled_non
    def read_dc(self) -> None:
        self.log.info(f"From rf-dc {self.number}: {self.dev_dc.read(self.readbytes).decode('utf-8')}")

    @if_exists_non
    @if_gen_enabled_non
    def __write_gen(self, data: str):
        self.log.info(f"To rf-gen №{self.number}: {data}")
        self.dev_gen.write(data.encode("utf-8"))

    @if_exists_non
    @if_dc_enabled_non
    def __write_dc(self, data: str):
        self.log.info(f"To rf-dc №{self.number}: {data}")
        self.dev_dc.write(data.encode("utf-8"))

    @if_exists_non
    @if_dc_enabled_non
    def send_maxcurrent_tmp(self, maxcurrent_tmp: int) -> None:
        # set maxcurrent_tmp
        c: List[str] = []
        for i in range(4):
            c.append(hex(maxcurrent_tmp)[2:].upper())
            while len(c[i]) < 4:
                c[i] = f"0{c[i]}"
            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
        si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
        self.__write_dc(si)

    @if_exists_non
    @if_dc_enabled_non
    def send_maxcurrent(self, maxcurrent: int) -> None:
        # set maxcurrent
        c: List[str] = []
        for i in range(4):
            c.append(hex(maxcurrent)[2:].upper())
            while len(c[i]) < 4:
                c[i] = f"0{c[i]}"
            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
        si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
        self.__write_dc(si)

    @if_exists_non
    @if_dc_enabled_non
    def change_power(self, maxcurrent: int) -> None:
        # max. normal power -> user defined power
        nsteps = 10
        for step in range(nsteps):
            c: List[str] = []
            for i in range(4):
                a = self.channel[i].current
                b = maxcurrent
                ac = int(a + (1.0 - (float(step) / float(nsteps))) * (b - a))
                self.log.debug("set pwr to %d" % ac)
                c.append(hex(ac)[2:].upper())
                while len(c[i]) < 4:
                    c[i] = f"0{c[i]}"
                c[i] = f"{c[i][2:4]}{c[i][0:2]}"
            si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
            self.__write_dc(si)

    @if_exists_non
    @if_dc_enabled_non
    @if_gen_enabled_non
    def ignition(self, maxcurrent: int, maxcurrent_tmp: int) -> None:
        self.rf_off()
        self.send_maxcurrent_tmp(maxcurrent_tmp)
        time.sleep(0.01)
        self.rf_on()
        time.sleep(0.1)
        self.send_maxcurrent(maxcurrent)
        time.sleep(1)
        self.send_maxcurrent_tmp(maxcurrent_tmp)
        time.sleep(0.1)
        self.change_power(maxcurrent)
        time.sleep(0.1)

        c: List[str] = []
        for i in range(4):
            c.append(hex(self.channel[i].current)[2:].upper())
            while len(c[i]) < 4:
                c[i] = f"0{c[i]}"
            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
        s = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
        self.__write_dc(s)

    def set_status(self):
        """set the status of all elements

        at the moment ADC is not available; therefore set everything to 0
        """
        for i in range(4):
            self.channel[i].onoff = False
            self.channel[i].current = 0
            self.channel[i].phase = 0
        self.rf_onoff = False

    @if_exists_non
    @if_gen_enabled_non
    def __onoff_action(self) -> None:
        self.log.debug("Channel on/off")
        onoff: int = 0  # all off
        for i in range(4):
            if self.channel[i].onoff:
                onoff = onoff + 2 ** (3 - i)
        onoff_s = hex(onoff)
        onoff_s = "0%s" % onoff_s[2].upper()
        w2gen = f"@X{onoff_s}"
        self.__write_gen(w2gen)

    @if_exists_non
    @if_dc_enabled_non
    def __current_action(self) -> None:
        self.log.debug("Channel current changed")
        c: List[str] = []
        for i in range(4):
            c.append(hex(self.channel[i].current)[2:].upper())
            while len(c[i]) < 4:
                c[i] = f"0{c[i]}"
            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
        w2dc = f"#O#D{c[2]}{c[3]}{c[0]}{c[1]}"
        self.__write_dc(w2dc)

    @if_exists_non
    @if_gen_enabled_non
    def __phase_action(self) -> None:
        self.log.debug("Channel current changed")
        p: List[str] = []
        for i in range(4):
            p.append(hex(self.channel[i].phase)[2:].upper())
            while len(p[i]) < 2:
                p[i] = f"0{p[i]}"
            p[i] = f"{p[i][2:4]}{p[i][0:2]}"
        w2gen = f"@P{p[0]}{p[1]}{p[2]}{p[3]}"
        self.__write_gen(w2gen)

    def channel_handler(self, event: EVENTS) -> None:
        self.log.debug(f"Channel event handler: {event}")
        if event == EVENTS.ONOFF:
            self.__onoff_action()
        elif event == EVENTS.current:
            self.__current_action()
        elif event == EVENTS.phase:
            self.__phase_action()

    @if_exists_non
    def rf_on(self) -> None:
        self.gen_enabled = True
        self.dev_gen = serial.Serial(
            port=self.gen_device,
            baudrate=self.boudrate,
            bytesize=self.databits,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.readtimeout,
            write_timeout=self.writetimeout,
        )
        if not self.dev_gen.is_open:
            self.dev_gen.open()
        self.__write_gen("@E")

    @if_exists_non
    def rf_off(self) -> None:
        self.__write_gen("@D")
        if self.dev_gen.is_open:
            self.dev_gen.close()
        self.gen_enabled = False

    @if_exists_non
    def dc_on(self) -> None:
        self.dc_enabled = True
        self.dev_dc = serial.Serial(
            port=self.dc_device,
            baudrate=self.boudrate,
            bytesize=self.databits,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.readtimeout,
            write_timeout=self.writetimeout,
        )
        if not self.dev_dc.is_open:
            self.dev_dc.open()
        self.__write_dc("#O")

    @if_exists_non
    def dc_off(self) -> None:
        self.__write_dc("#o")
        if self.dev_dc.is_open:
            self.dev_dc.close()
        self.dc_enabled = False

    @if_exists_non
    def open_serial(self) -> None:
        self.log.info(f"Starting generator №{self.number}")
        self.rf_on()
        self.log.info(f"Starting dc №{self.number}")
        self.dc_on()

    @if_exists_non
    def close_serial(self) -> None:
        self.log.info(f"Stopping generator №{self.number}")
        self.rf_off()
        self.log.info(f"Stopping dc №{self.number}")
        self.dc_off()

    @if_exists_non
    def power(self, state: bool) -> None:
        self.pwc.setpoint[self.power_port][self.power_channel] = state


class rfg_gui(ttk.LabelFrame, Master):
    def __init__(self, _root: ttk.LabelFrame, master: Master, _backend: class_rf_generator) -> None:
        ttk.LabelFrame.__init__(self, _root, text="GEN_" + str(_backend.number + 1) if _backend.exists else "NE")
        Master.__init__(self, master, custom_name="RFG")
        self.backend = _backend

        self.exists = self.backend.exists
        if self.exists:
            self.power_status: tk.IntVar = tk.IntVar()
            self.power_status_checkbutton: tk.Checkbutton = tk.Checkbutton(
                self,
                text=f"Power RF-Generator {self.backend.number + 1}",
                command=self.btn_power,
                variable=self.power_status,
                state=tk.DISABLED,
            )
            self.power_status_checkbutton.pack()
            self.channels_frame = ttk.LabelFrame(self, text="Channels")
            self.channels_frame.pack()
            self.channels: List[cc_gui] = [
                cc_gui(self.channels_frame, _backend, self.log.getChild(f"gui_chan{_backend.n}"))
                for _backend in self.backend.channel
            ]
            [c.pack() for c in self.channels]

            # self.setpoint_channels_frame = tk.ttk.LabelFrame(self, text="Setpoint channels")
            # self.setpoint_channels_frame.pack()
            # self.setpoint_channels: List[cc_gui] = [
            #     cc_gui(self.setpoint_channels_frame, _backend) for _backend in self.backend.setpoint_channel
            # ]
            # [c.pack() for c in self.setpoint_channels]

            # self.actualvalue_channels_frame = tk.ttk.LabelFrame(self, text="AV channels")
            # self.actualvalue_channels_frame.pack()
            # self.actualvalue_channels: List[cc_gui] = [
            #     cc_gui(self.actualvalue_channels_frame, _backend) for _backend in self.backend.actualvalue_channel
            # ]
            # [c.pack() for c in self.actualvalue_channels]

    def btn_power(self) -> None:
        self.log.debug("btn_power")
        s = self.power_status.get() != 0
        self.backend.power(s)

    def pwr_on(self) -> None:
        self.log.debug("Power on")
        [chan.pwr_on() for chan in self.channels]

    def pwr_off(self) -> None:
        self.log.debug("Power off")
        [chan.pwr_off() for chan in self.channels]

    def sc(self, current) -> None:
        for i, chan in enumerate(self.channels):
            if chan.sc(current):
                self.channels[i].sc(current)

    def upd(self) -> None:
        if self.exists:
            if self.backend.pwc.connected:
                self.power_status_checkbutton.configure(state=tk.NORMAL)
            else:
                self.power_status_checkbutton.configure(state=tk.DISABLED)


if __name__ == "__main__":
    pass
