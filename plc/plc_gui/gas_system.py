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
gui for controlling gas system
"""

import logging
import tkinter
import tkinter.ttk

from typing import Dict

from ..plc_tools.conversion import b2onoff, msccm2volt, volt2msccm
from .read_config_file import read_config_file
from .controller import controller


class gs:
    def __init__(self, config: read_config_file, _log: logging.Logger, _controller: Dict[str, controller]) -> None:
        self.log = _log
        self.config = config
        self.controller: Dict[str, controller] = _controller
        self.mpsc = self.config.values.get("gas system", "membran_pump_status_controller")
        self.mpsp = self.config.values.get("gas system", "membran_pump_status_port")
        self.mpsca = self.config.values.getint("gas system", "membran_pump_status_channel")

        self.tp1sc = self.config.values.get("gas system", "turbo_pump_1_status_controller")
        self.tp1sp = self.config.values.get("gas system", "turbo_pump_1_status_port")
        self.tp1sca = self.config.values.getint("gas system", "turbo_pump_1_status_channel")

        self.tp2sc = self.config.values.get("gas system", "turbo_pump_2_status_controller")
        self.tp2sp = self.config.values.get("gas system", "turbo_pump_2_status_port")
        self.tp2sca = self.config.values.getint("gas system", "turbo_pump_2_status_channel")

        self.mfcsc = self.config.values.get("gas system", "mass_flow_controller_status_controller")
        self.mfcsp = self.config.values.get("gas system", "mass_flow_controller_status_port")
        self.mfcsca = self.config.values.getint("gas system", "mass_flow_controller_status_channel")

        self.mfcsrc = self.config.values.get("gas system", "mass_flow_controller_set_rate_controller")
        self.mfcsrp = self.config.values.get("gas system", "mass_flow_controller_set_rate_port")
        self.mfcsrca = self.config.values.getint("gas system", "mass_flow_controller_set_rate_channel")

        self.tp1rc = self.config.values.get("gas system", "turbo_pump_1_rpm_controller")
        self.tp1rp = self.config.values.get("gas system", "turbo_pump_1_rpm_port")
        self.tp1rca = self.config.values.getint("gas system", "turbo_pump_1_rpm_channel")

        self.tp2rc = self.config.values.get("gas system", "turbo_pump_2_rpm_controller")
        self.tp2rp = self.config.values.get("gas system", "turbo_pump_2_rpm_port")
        self.tp2rca = self.config.values.getint("gas system", "turbo_pump_2_rpm_channel")

        self.tp1egc = self.config.values.get("gas system", "turbo_pump_1_error_general_controller")
        self.tp1egp = self.config.values.get("gas system", "turbo_pump_1_error_general_port")
        self.tp1egca = self.config.values.getint("gas system", "turbo_pump_1_error_general_channel")

        self.tp1erc = self.config.values.get("gas system", "turbo_pump_1_error_rotation_controller")
        self.tp1erp = self.config.values.get("gas system", "turbo_pump_1_error_rotation_port")
        self.tp1erca = self.config.values.getint("gas system", "turbo_pump_1_error_rotation_channel")

        self.tp2egc = self.config.values.get("gas system", "turbo_pump_2_error_general_controller")
        self.tp2egp = self.config.values.get("gas system", "turbo_pump_2_error_general_port")
        self.tp2egca = self.config.values.getint("gas system", "turbo_pump_2_error_general_channel")

        self.tp2erc = self.config.values.get("gas system", "turbo_pump_2_error_rotation_controller")
        self.tp2erp = self.config.values.get("gas system", "turbo_pump_2_error_rotation_port")
        self.tp2erca = self.config.values.getint("gas system", "turbo_pump_2_error_rotation_channel")

        self.mfcmrc = self.config.values.get("gas system", "mass_flow_controller_measure_rate_controller")
        self.mfcmrp = self.config.values.get("gas system", "mass_flow_controller_measure_rate_port")
        self.mfcmrca = self.config.values.getint("gas system", "mass_flow_controller_measure_rate_channel")

    def membran_pump(self, state: bool) -> None:
        self.log.debug(f"Switching membran pump to {b2onoff(state)}")

        self.controller[self.mpsc].lock.acquire()  # lock
        self.controller[self.mpsc].setpoint[self.mpsp][self.mpsca] = state
        self.controller[self.mpsc].lock.release()  # release the lock

    def mpc_connected(self) -> bool:
        return self.controller[self.mpsc].connected

    def turbo_pump_1(self, state: bool) -> None:
        self.log.debug(f"Switching turbo pump 1 to {b2onoff(state)}")

        self.controller[self.tp1sc].lock.acquire()  # lock
        self.controller[self.tp1sc].setpoint[self.tp1sp][self.tp1sca] = state
        self.controller[self.tp1sc].lock.release()  # release the lock

    def tp1c_connected(self) -> bool:
        return self.controller[self.tp1sc].connected

    def turbo_pump_2(self, state: bool) -> None:
        self.log.debug(f"Switching turbo pump 2 to {b2onoff(state)}")

        self.controller[self.tp2sc].lock.acquire()  # lock
        self.controller[self.tp2sc].setpoint[self.tp2sp][self.tp2sca] = state
        self.controller[self.tp2sc].lock.release()  # release the lock

    def tp2c_connected(self) -> bool:
        return self.controller[self.tp2sc].connected

    def mass_flow(self, state: bool) -> None:
        self.log.debug(f"Switching mass flow controller to {b2onoff(state)}")

        self.controller[self.mfcsc].lock.acquire()  # lock
        try:
            self.controller[self.mfcsc].setpoint[self.mfcsp][self.mfcsca] = state
        except Exception:
            try:
                self.controller[self.mfcsc].setpoint[self.mfcsp] = state
            except Exception:
                pass
        self.controller[self.mfcsc].lock.release()  # release the lock

    def mfc_connected(self) -> bool:
        return self.controller[self.mfcsc].connected

    def set_mass_flow_rate(self, v) -> str:
        # X = 0 ... 5 V = 0 ... 1 sccm (flow)
        nr = ""
        if len(v) > 0:
            v = float(v)  # msccm from user
            vo = min(max(0.0, msccm2volt(v)), 5.0)  # voltage
            self.log.debug(f"Seting flow rate to ({vo} V, {v} msccm)")
            self.controller[self.mfcsrc].lock.acquire()  # lock
            try:
                self.controller[self.mfcsrc].setpoint[self.mfcsrp][self.mfcsrca] = vo
                nr = "%.2f" % volt2msccm(vo)
            except Exception:
                try:
                    self.controller[self.mfcsrc].setpoint[self.mfcsrp][self.mfcsrca] = vo
                    nr = "%f" % volt2msccm(vo)
                except Exception:
                    nr = "ERROR"
            self.controller[self.mfcsrc].lock.release()  # release the lock
        return nr

    def membran_pump_state(self) -> bool:
        return self.controller[self.mpsc].actualvalue[self.mpsp][self.mpsca]

    def turbo_pump_1_status(self) -> bool:
        return self.controller[self.tp1sc].actualvalue[self.tp1sp][self.tp1sca]

    def turbo_pump_2_status(self) -> bool:
        return self.controller[self.tp2sc].actualvalue[self.tp2sp][self.tp2sca]

    def turbo_pump_1_rpm(self) -> int:
        return round(self.controller[self.tp1rc].actualvalue[self.tp1rp][self.tp1rca] * 10)

    def turbo_pump_2_rpm(self) -> int:
        return round(self.controller[self.tp2rc].actualvalue[self.tp2rp][self.tp2rca] * 10)

    def turbo_pump_1_error_general(self) -> bool:
        return not (self.controller[self.tp1egc].actualvalue[self.tp1egp][self.tp1egca])

    def turbo_pump_1_error_rotation(self) -> bool:
        return not (self.controller[self.tp1erc].actualvalue[self.tp1erp][self.tp1erca])

    def turbo_pump_2_error_general(self) -> bool:
        return not (self.controller[self.tp2egc].actualvalue[self.tp2egp][self.tp2egca])

    def turbo_pump_2_error_rotation(self) -> bool:
        return not (self.controller[self.tp2erc].actualvalue[self.tp2erp][self.tp2erca])

    def mass_flow_controller_measure_rate(self) -> float:
        return self.controller[self.mfcmrc].actualvalue[self.mfcmrp][self.mfcmrca]

    def mass_flow_controller_status(self) -> bool:
        try:
            return self.controller[self.mfcsc].actualvalue[self.mfcsp][self.mfcsca]
        except Exception:
            return self.controller[self.mfcsc].actualvalue[self.mfcsp]


class gas_system(tkinter.ttk.LabelFrame):
    """
    gui for gas system control
    """

    def __init__(
        self,
        _root: tkinter.ttk.Frame,
        _backend: gs,
        _log: logging.Logger,
    ) -> None:
        """__init__(self,config=None,pw=None,debugprint=None)

        create gui for gas system control

        Parameters:
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           debugprint : function
                        function to call for print debug information
        """
        super().__init__(master=_root, text="GAS SYS")
        self.backend = _backend
        self.root = _root
        # create gui
        self.pumps_frame = tkinter.Frame(self)
        self.pumps_frame.pack()
        self.mass_flow_frame = tkinter.LabelFrame(self, text="Mass Flow Controller")
        self.mass_flow_frame.pack()
        # membran pump
        self.membran_pump_status = tkinter.IntVar()
        self.membran_pump_checkbutton = tkinter.Checkbutton(
            self.pumps_frame,
            text="Mem. Pump",
            command=self.membran_pump,
            variable=self.membran_pump_status,
            state=tkinter.DISABLED,
        )
        self.membran_pump_checkbutton.grid(row=2, column=0)
        self.membran_pump_status_val = tkinter.StringVar()
        self.membran_pump_status_val_label = tkinter.Label(
            self.pumps_frame, textvariable=self.membran_pump_status_val, height=1, width=3
        )
        self.membran_pump_status_val.set("val")
        self.membran_pump_status_val_label.grid(row=2, column=1)
        # self.membran_pump_checkbutton.deselect()
        # self.membran_pump_checkbutton.select()
        # turbo pump 1
        self.turbo_pump_1_status = tkinter.IntVar()
        self.turbo_pump_1_checkbutton = tkinter.Checkbutton(
            self.pumps_frame,
            text="Turbo Pump 1",
            command=self.turbo_pump_1,
            variable=self.turbo_pump_1_status,
            state=tkinter.DISABLED,
        )
        self.turbo_pump_1_checkbutton.grid(row=2, column=2)
        self.turbo_pump_1_status_val = tkinter.StringVar()
        self.turbo_pump_1_status_label = tkinter.Label(
            self.pumps_frame, textvariable=self.turbo_pump_1_status_val, height=1, width=5
        )
        self.turbo_pump_1_status_val.set("val")
        self.turbo_pump_1_status_label.grid(row=2, column=3)
        self.turbo_pump_1_rpm_val = tkinter.StringVar()
        self.turbo_pump_1_rpm_label = tkinter.Label(
            self.pumps_frame, textvariable=self.turbo_pump_1_rpm_val, height=1, width=5
        )
        self.turbo_pump_1_rpm_val.set("val")
        self.turbo_pump_1_rpm_label.grid(row=2, column=4)
        self.turbo_pump_1_error_val = tkinter.StringVar()
        self.turbo_pump_1_error_label = tkinter.Label(
            self.pumps_frame, textvariable=self.turbo_pump_1_error_val, height=1, width=25
        )
        self.turbo_pump_1_error_val.set("val")
        self.turbo_pump_1_error_label.grid(row=2, column=5)
        # turbo pump 2
        self.turbo_pump_2_status = tkinter.IntVar()
        self.turbo_pump_2_checkbutton = tkinter.Checkbutton(
            self.pumps_frame,
            text="Turbo Pump 2",
            command=self.turbo_pump_2,
            variable=self.turbo_pump_2_status,
            state=tkinter.DISABLED,
            offvalue=False,
            onvalue=True,
        )
        self.turbo_pump_2_checkbutton.grid(row=3, column=2)
        self.turbo_pump_2_status_val = tkinter.StringVar()
        self.turbo_pump_2_status_label = tkinter.Label(
            self.pumps_frame, textvariable=self.turbo_pump_2_status_val, height=1, width=5
        )
        self.turbo_pump_2_status_val.set("val")
        self.turbo_pump_2_status_label.grid(row=3, column=3)
        self.turbo_pump_2_rpm_val = tkinter.StringVar()
        self.turbo_pump_2_rpm_label = tkinter.Label(
            self.pumps_frame, textvariable=self.turbo_pump_2_rpm_val, height=1, width=5
        )
        self.turbo_pump_2_rpm_val.set("val")
        self.turbo_pump_2_rpm_label.grid(row=3, column=4)
        self.turbo_pump_2_error_val = tkinter.StringVar()
        self.turbo_pump_2_error_label = tkinter.Label(
            self.pumps_frame, textvariable=self.turbo_pump_2_error_val, height=1, width=25
        )
        self.turbo_pump_2_error_val.set("val")
        self.turbo_pump_2_error_label.grid(row=3, column=5)
        # Mass Flow Controller
        self.mass_flow_status = tkinter.IntVar()
        self.mass_flow_checkbutton = tkinter.Checkbutton(
            self.mass_flow_frame,
            text="ON/OFF",
            command=self.mass_flow,
            variable=self.mass_flow_status,
            state=tkinter.DISABLED,
            offvalue=False,
            onvalue=True,
        )
        self.mass_flow_checkbutton.grid(column=0, row=0)
        self.mass_flow_status_val = tkinter.StringVar()
        self.mass_flow_status_label = tkinter.Label(
            self.mass_flow_frame, textvariable=self.mass_flow_status_val, height=1, width=5
        )
        self.mass_flow_status_val.set("val")
        self.mass_flow_status_label.grid(column=1, row=0)
        self.mass_flow_set_flow_rate_val = tkinter.StringVar()
        self.mass_flow_set_flow_rate_entry = tkinter.Entry(
            self.mass_flow_frame, textvariable=self.mass_flow_set_flow_rate_val, width=8, state=tkinter.DISABLED
        )
        self.mass_flow_set_flow_rate_entry.grid(column=2, row=0)
        self.mass_flow_set_flow_rate_button = tkinter.Button(
            self.mass_flow_frame, command=self.set_mass_flow_rate, text="set", state=tkinter.DISABLED
        )
        self.mass_flow_set_flow_rate_button.grid(column=3, row=0)
        self.mass_flow_flow_rate_val = tkinter.StringVar()
        self.mass_flow_flow_rate_label = tkinter.Label(
            self.mass_flow_frame, textvariable=self.mass_flow_flow_rate_val, height=1, width=14
        )
        self.mass_flow_flow_rate_val.set("val")
        self.mass_flow_flow_rate_label.grid(column=4, row=0)

    def membran_pump(self) -> None:
        self.backend.membran_pump(self.membran_pump_status.get() == 0)

    def turbo_pump_1(self) -> None:
        self.backend.turbo_pump_1(self.turbo_pump_1_status.get() == 0)

    def turbo_pump_2(self) -> None:
        self.backend.turbo_pump_2(self.turbo_pump_2_status.get() == 0)

    def mass_flow(self) -> None:
        self.backend.mass_flow(self.mass_flow_status.get() == 0)

    def set_mass_flow_rate(self) -> None:
        v = self.mass_flow_set_flow_rate_val.get()
        nr = self.backend.set_mass_flow_rate(v)
        self.mass_flow_set_flow_rate_val.set(nr)

    def erm(self, err1: bool, err2: bool) -> str:
        err = ""
        if err1:
            if err2:
                err = "ERROR: general + rotation"
            else:
                err = "ERROR: rotation"
        elif err2:
            err = "ERROR: general"
        return err

    def update(self) -> None:
        """update every dynamic read values"""
        self.membran_pump_status_val.set(b2onoff(self.backend.membran_pump_state()))
        self.turbo_pump_1_status_val.set(b2onoff(self.backend.turbo_pump_1_status()))
        self.turbo_pump_2_status_val.set(b2onoff(self.backend.turbo_pump_2_status()))

        # RPM
        self.turbo_pump_1_rpm_val.set("%d %%" % self.backend.turbo_pump_1_rpm())
        self.turbo_pump_2_rpm_val.set("%d %%" % self.backend.turbo_pump_2_rpm())

        # ERROR
        err1 = self.backend.turbo_pump_1_error_rotation()
        err2 = self.backend.turbo_pump_1_error_general()
        self.turbo_pump_1_error_val.set(self.erm(err1, err2))

        err1 = self.backend.turbo_pump_2_error_rotation()
        err2 = self.backend.turbo_pump_2_error_general()
        self.turbo_pump_2_error_val.set(self.erm(err1, err2))

        # measured flow rate
        self.mass_flow_status_val.set(b2onoff(self.backend.mass_flow_controller_status()))
        self.mass_flow_flow_rate_val.set("%.2f msccm" % volt2msccm(self.backend.mass_flow_controller_measure_rate()))

        if self.backend.mpc_connected():
            self.membran_pump_checkbutton.configure(state=tkinter.NORMAL)
        else:
            self.membran_pump_checkbutton.configure(state=tkinter.DISABLED)

        if self.backend.tp1c_connected():
            self.turbo_pump_1_checkbutton.configure(state=tkinter.NORMAL)
        else:
            self.turbo_pump_1_checkbutton.configure(state=tkinter.DISABLED)

        if self.backend.tp2c_connected():
            self.turbo_pump_2_checkbutton.configure(state=tkinter.NORMAL)
        else:
            self.turbo_pump_2_checkbutton.configure(state=tkinter.DISABLED)

        if self.backend.mfc_connected():
            self.mass_flow_checkbutton.configure(state=tkinter.NORMAL)
            self.mass_flow_set_flow_rate_entry.configure(state=tkinter.NORMAL)
            self.mass_flow_set_flow_rate_button.configure(state=tkinter.NORMAL)
        else:
            self.mass_flow_checkbutton.configure(state=tkinter.DISABLED)
            self.mass_flow_set_flow_rate_entry.configure(state=tkinter.DISABLED)
            self.mass_flow_set_flow_rate_button.configure(state=tkinter.DISABLED)


if __name__ == "__main__":
    pass
