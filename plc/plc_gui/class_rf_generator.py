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
import logging
from enum import Enum
from dataclasses import dataclass
from .read_config_file import read_config_file
from typing import List, Dict, Annotated, Callable

import serial
import tkinter
import tkinter.ttk


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

    def __init__(self, cn: int, hndlr: Callable[[EVENTS], None]) -> None:
        self._onoff: bool = False  # True if on
        self._hndlr = hndlr
        self.n = cn
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
        self._onoff_write()

    def _current_write(self) -> None:
        self._hndlr(EVENTS.current)

    @property
    def current(self) -> int:
        return self._current

    @current.setter
    def current(self, value: int) -> None:
        self._current = value
        self._current_write()

    def _phase_write(self) -> None:
        self._hndlr(EVENTS.phase)

    @property
    def phase(self) -> int:
        return self._phase

    @phase.setter
    def phase(self, value: int) -> None:
        self._phase = value
        self._phase_write()


class cc_gui(tkinter.ttk.Frame):
    def __init__(self, _root: tkinter.ttk.LabelFrame, backend: class_channel) -> None:
        super().__init__(_root)
        self.current_bonds = (0, 4095)
        self.phase_bonds = (0, 255)
        self.backend = backend
        self.onoff_status: tkinter.IntVar = tkinter.IntVar()
        self.onoff_status_checkbutton: tkinter.Checkbutton = tkinter.Checkbutton(
            self,
            text=f"Pwr Channel {backend.n}",
            command=self.onoff,
            variable=self.onoff_status,
            state=tkinter.DISABLED,
        )
        self.onoff_status_checkbutton.grid(column=0, row=backend.n)

        vcmd = (self.register(self.validate), "%P", "%W")
        ivcmd = (self.register(self.on_invalid), "%W")
        self.current_status: tkinter.IntVar = tkinter.IntVar()
        self.current_status_entry: tkinter.Entry = tkinter.Entry(
            self,
            name="current",
            textvariable=self.current_status,
            width=5,
            validate="key",
            validatecommand=vcmd,
            invalidcommand=ivcmd,
        )
        self.current_status_entry.grid(column=2, row=backend.n)
        self.phase_status: tkinter.IntVar = tkinter.IntVar()
        self.phase_status_entry: tkinter.Entry = tkinter.Entry(
            self,
            name="phase",
            textvariable=self.phase_status,
            width=4,
            validate="key",
            validatecommand=vcmd,
            invalidcommand=ivcmd,
        )
        self.phase_status_entry.grid(column=4, row=backend.n)

        self.choose: tkinter.IntVar = tkinter.IntVar()
        self.choose_checkbutton: tkinter.Checkbutton = tkinter.Checkbutton(
            self, text=f"Channel {backend.n}", variable=self.choose
        )
        self.choose_checkbutton.grid(column=6, row=backend.n)
        self.choose_checkbutton.select()

    def onoff(self) -> None:
        self.backend.onoff = not self.backend.onoff

    def pwr_on(self) -> bool:
        if self.choose.get() == 1:
            self.onoff_status_checkbutton.select()
            return True
        return False

    def pwr_off(self) -> bool:
        if self.choose.get() == 1:
            self.onoff_status_checkbutton.deselect()
            return True
        return False

    def sc(self, current):
        if self.choose.get() == 1:
            self.current_status.set(max(self.current_bonds[0], min(current, self.current_bonds[1])))
            return True
        return False

    def validate(self, _value, widget):
        """
        Validat the email entry
        :param value:
        :return:
        """
        if widget == "current":
            try:
                current = int(_value)
            except Exception:
                return False
            if 0 <= current and current <= 4095:
                self.backend.current = current
                self.current_status_entry["backgroud"] = "green"
                return True
        elif widget == "phase":
            try:
                phase = int(_value)
            except Exception:
                return False
            if 0 <= phase and phase <= 255:
                self.backend.phase = phase
                self.phase_status_entry["backgroud"] = "green"
                return True

    def on_invalid(self, widget):
        """
        Show the error message if the data is not valid
        :return:
        """
        if widget == "current":
            self.current_status_entry["backgroud"] = "red"
        elif widget == "phase":
            self.phase_status_entry["backgroud"] = "red"


class class_rf_generator:
    """
    class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator
    """

    def __init__(self, exists: bool, number: int, config: read_config_file, _log: logging.Logger) -> None:
        """
        init of class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator
        """
        self.exists = exists
        self.log = _log
        if self.exists:
            self.number = number
            self.power_controller: str = config.values.get(f"RF-Generator {number + 1}", "power_controller")
            self.power_port: str = config.values.get(f"RF-Generator {number + 1}", "power_port")
            self.power_channel: str = config.values.get(f"RF-Generator {number + 1}", "power_channel")

            self.channel: List[class_channel] = []
            for i in range(4):
                self.channel.append(class_channel(self.number * 4 + i, self.channel_handler))
            # self.setpoint_channel: List[class_channel] = []
            # for i in range(4):
            #     self.setpoint_channel.append(class_channel(self.number * 4 + i, self.channel_handler))
            # self.actualvalue_channel: List[class_channel] = []
            # for i in range(4):
            #     self.actualvalue_channel.append(class_channel(self.number * 4 + i, self.channel_handler))

            self.setpoint_rf_onoff: bool = False
            self.actualvalue_rf_onoff: bool = False
            # self.setpoint_ignite_plasma: bool = False
            self.actualvalue_pattern: str = ""
            self.device = None
            self.rf_onoff = None
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
            self.dev_gen = serial.Serial(
                port=self.gen_device,
                baudrate=self.boudrate,
                bytesize=self.databits,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.readtimeout,
                write_timeout=self.writetimeout,
            )
            self.dev_dc = serial.Serial(
                port=self.dc_device,
                baudrate=self.boudrate,
                bytesize=self.databits,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.readtimeout,
                write_timeout=self.writetimeout,
            )

    def read_gen(self) -> None:
        self.log.info(f"From rf-gen {self.number}: {self.dev_gen.read(self.readbytes).decode('utf-8')}")

    def read_dc(self) -> None:
        self.log.info(f"From rf-dc {self.number}: {self.dev_dc.read(self.readbytes).decode('utf-8')}")

    def send_maxcurrent_tmp(self, maxcurrent_tmp: int) -> None:
        # set maxcurrent_tmp
        c: List[str] = []
        for i in range(4):
            c.append(hex(maxcurrent_tmp)[2:].upper())
            while len(c[i]) < 4:
                c[i] = f"0{c[i]}"
            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
        si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"

        self.log.info(f"To rf-dc {self.number}: {si}")
        self.dev_dc.write(si.encode("urf-8"))

    def send_maxcurrent(self, maxcurrent: int) -> None:
        # set maxcurrent
        c: List[str] = []
        for i in range(4):
            c.append(hex(maxcurrent)[2:].upper())
            while len(c[i]) < 4:
                c[i] = f"0{c[i]}"
            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
        si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"

        self.log.info(f"To rf-dc {self.number}: {si}")
        self.dev_dc.write(si.encode("utf-8"))

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
            self.log.info(f"To rf-dc {self.number}: {si}")
            self.dev_dc.write(si.encode("utf-8"))

    def ignition(self, maxcurrent: int, maxcurrent_tmp: int) -> None:
        s = "@D"
        self.log.info(f"To rf-gen {self.number}: {s}")
        self.dev_gen.write(s.encode("utf-8"))

        self.send_maxcurrent_tmp(maxcurrent_tmp)
        time.sleep(0.01)

        if self.actualvalue_rf_onoff:
            s = "@E"
            self.log.info(f"To rf-gen {self.number}: {s}")
            self.dev_gen.write(s.encode("utf-8"))
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
        self.log.info(f"To rf-dc {self.number}: {s}")
        self.dev_dc.write(s.encode("utf-8"))

    def open_serial(self):
        if not self.exists:
            self.log.error("Attempt to connect nonexistent rf-gen")
        self.log.info(f"Starting generator №{self.number}")
        if not self.dev_gen.is_open:
            self.dev_gen.open()
            self.log.debug(f"Connected to generator №{self.number}")
        self.log.info(f"Starting dc №{self.number}")
        if not self.dev_dc.is_open:
            self.dev_dc.open()
        self.log.info(f"To rf-dc №{self.number}: #O")
        self.dev_dc.write(b"#O")

    def set_status(self):
        """set the status of all elements

        at the moment ADC is not available; therefore set everything to 0
        """
        for i in range(4):
            self.channel[i].onoff = False
            self.channel[i].current = 0
            self.channel[i].phase = 0
        self.rf_onoff = False

    def __write_gen(self, data: str):
        self.log.info(f"To rf-gen №{self.number}: {data}")
        self.dev_gen.write(data.encode("utf-8"))

    def __write_dc(self, data: str):
        self.log.info(f"To rf-dc №{self.number}: {data}")
        self.dev_dc.write(data.encode("utf-8"))

    def __onoff_action(self) -> None:
        onoff: int = 0  # all off
        for i in range(4):
            if self.channel[i].onoff:
                onoff = onoff + 2 ** (3 - i)
        onoff_s = hex(onoff)
        onoff_s = "0%s" % onoff_s[2].upper()
        w2gen = f"@X{onoff_s}"
        self.__write_gen(w2gen)

    def __current_action(self) -> None:
        c: List[str] = []
        for i in range(4):
            c.append(hex(self.channel[i].current)[2:].upper())
            while len(c[i]) < 4:
                c[i] = f"0{c[i]}"
            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
        w2dc = f"#O#D{c[2]}{c[3]}{c[0]}{c[1]}"
        self.__write_dc(w2dc)

    def __phase_action(self) -> None:
        p: List[str] = []
        for i in range(4):
            p.append(hex(self.channel[i].phase)[2:].upper())
            while len(p[i]) < 2:
                p[i] = f"0{p[i]}"
            p[i] = f"{p[i][2:4]}{p[i][0:2]}"
        w2gen = f"@P{p[0]}{p[1]}{p[2]}{p[3]}"
        self.__write_gen(w2gen)

    def channel_handler(self, event: EVENTS):
        if event == EVENTS.ONOFF:
            self.__onoff_action()
        elif event == EVENTS.current:
            self.__current_action()
        elif event == EVENTS.phase:
            self.__phase_action()

    def update(self) -> None:
        if self.setpoint_rf_onoff != self.actualvalue_rf_onoff:
            self.actualvalue_rf_onoff = self.setpoint_rf_onoff
            w2gen = ""
            # rf_onoff
            # enable/disable 13 MHz
            if self.actualvalue_rf_onoff:
                w2gen = f"{w2gen}@E"
            else:
                w2gen = f"{w2gen}@D"
            self.log.info(f"To rf-gen {self.number}: {w2gen}")
            self.dev_gen.write(w2gen.encode("utf-8"))


class rfg_gui(tkinter.ttk.LabelFrame):
    def __init__(self, _root: tkinter.ttk.LabelFrame, _backend: class_rf_generator, _log: logging.Logger) -> None:
        super().__init__(_root, text="GEN_" + str(_backend.number + 1) if _backend.exists else "NE")
        self.backend = _backend
        self.log = _log
        if self.backend.exists:
            self.power_status: tkinter.IntVar = tkinter.IntVar()
            self.power_status_checkbutton: tkinter.Checkbutton = tkinter.Checkbutton(
                self,
                text=f"Power RF-Generator {self.backend.number + 1}",
                command=self.power,
                variable=self.power_status,
                state=tkinter.DISABLED,
            )
            self.power_status_checkbutton.pack()
            self.channels_frame = tkinter.ttk.LabelFrame(self, text="Channels")
            self.channels_frame.pack()
            self.channels: List[cc_gui] = [cc_gui(self.channels_frame, _backend) for _backend in self.backend.channel]
            [c.pack() for c in self.channels]

            # self.setpoint_channels_frame = tkinter.ttk.LabelFrame(self, text="Setpoint channels")
            # self.setpoint_channels_frame.pack()
            # self.setpoint_channels: List[cc_gui] = [
            #     cc_gui(self.setpoint_channels_frame, _backend) for _backend in self.backend.setpoint_channel
            # ]
            # [c.pack() for c in self.setpoint_channels]

            # self.actualvalue_channels_frame = tkinter.ttk.LabelFrame(self, text="AV channels")
            # self.actualvalue_channels_frame.pack()
            # self.actualvalue_channels: List[cc_gui] = [
            #     cc_gui(self.actualvalue_channels_frame, _backend) for _backend in self.backend.actualvalue_channel
            # ]
            # [c.pack() for c in self.actualvalue_channels]

    def power(self):
        s = self.power_status.get() != 0
        self.log.error("Not implemented")
        # self.controller[self.power_controller].setpoint[
        #         self.power_port
        #     ][int(self.power_channel)] = s

    def pwr_on(self):
        for i, chan in enumerate(self.channels):
            if chan.pwr_on():
                self.channels[i].pwr_on()

    def pwr_off(self):
        for i, chan in enumerate(self.channels):
            if chan.pwr_off():
                self.channels[i].pwr_off()

    def sc(self, current):
        for i, chan in enumerate(self.channels):
            if chan.sc(current):
                self.channels[i].sc(current)
