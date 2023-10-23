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
gui for Electrode Motion
"""

import logging
import tkinter
from tkinter import ttk
from typing import Callable

from ..plc_tools.conversion import b2onoff
from .electrode_motion_controller import electrode_motion_controller


class sample_frame(ttk.LabelFrame):
    def __init__(self, _root: ttk.Frame, text: str, _move: Callable[[int], None]) -> None:
        super().__init__(_root, text=text)
        self.move = _move
        self.down_button_10 = tkinter.Button(self, command=lambda: self.move(-10), text="10 down")
        self.down_button_10.grid(column=0, row=0)
        self.down_button_1 = tkinter.Button(self, command=lambda: self.move(-1), text="1 down")
        self.down_button_1.grid(column=1, row=0)
        vcmd = (self.register(self.validate), "%P", "%W")
        ivcmd = (self.register(self.on_invalid), "%W")
        self.n_frame = tkinter.LabelFrame(self, text="n-steps (down: n<0)")
        self.n_frame.grid(column=2, row=0)
        self.n_val = tkinter.IntVar()
        self.n_entry = tkinter.Entry(
            self.n_frame,
            # name="lower_guard_ring",
            textvariable=self.n_val,
            width=6,
        )
        self.n_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
        self.n_entry.grid(column=0, row=0)
        self.n_button = tkinter.Button(
            self.n_frame,
            command=self.n_move,
            text="set",
            state=tkinter.DISABLED,
        )
        self.n_button.grid(column=1, row=0)
        self.up_button_1 = tkinter.Button(self, command=lambda: self.move(1), text="1 up")
        self.up_button_1.grid(column=3, row=0)
        self.up_botton_10 = tkinter.Button(self, command=lambda: self.move(10), text="10 up")
        self.up_botton_10.grid(column=4, row=0)

    def on_invalid(self, _widget: str) -> None:
        self.n_entry.configure(background="red")
        self.n_button.configure(state=tkinter.DISABLED)

    def validate(self, _value, _widget: str) -> bool:
        try:
            int(_value)
        except Exception:
            return False
        self.n_entry.configure(background="green")
        self.n_button.configure(state=tkinter.NORMAL)
        return True

    def n_move(self) -> None:
        self.n_button.configure(state=tkinter.DISABLED)
        steps = int(self.n_val.get())
        self.move(steps)


class electrode_motion(ttk.LabelFrame):
    """
    gui for Electrode Motion
    """

    def __init__(
        self,
        _root: ttk.Frame,
        _log: logging.Logger,
        controller: electrode_motion_controller,
    ) -> None:
        """__init__(self,config=None,pw=None,debugprint=None,controller=None)

        create gui for Electrode Motion

        Parameters:
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           debugprint : function
                        function to call for print debug information
        """
        super().__init__(_root, text="Electrode motion")
        self.log = _log
        self.controller = controller

        self.init_frame = tkinter.Frame(self)
        self.init_frame.grid(column=0, row=0)
        self.power_status = tkinter.IntVar()
        self.power_button = tkinter.Checkbutton(
            self.init_frame, text="Power", command=self.power, variable=self.power_status
        )
        self.power_button.pack()
        self.start_controller_button = tkinter.Button(self.init_frame, text="open RS232 (emc)", command=self.start)
        self.start_controller_button.pack()
        self.stop_controller_button = tkinter.Button(
            self.init_frame, text="close RS232 (emc)", command=self.stop, state=tkinter.DISABLED
        )
        self.stop_controller_button.pack()

        # control area
        self.control_frame = ttk.Frame(self)
        # self.control_frame.pack()
        self.guard_ring_frame = ttk.Frame(self.control_frame)
        self.guard_ring_frame.grid(column=1, row=0)
        self.upper_guard_ring_frame = sample_frame(
            self.guard_ring_frame,
            "Upper Guard Ring",
            self.upper_guard_ring_move,
        )
        self.upper_guard_ring_frame.pack()
        self.lower_guard_ring_frame = sample_frame(
            self.guard_ring_frame,
            "Lower Guard Ring",
            self.lower_guard_ring_move,
        )
        self.lower_guard_ring_frame.pack()

        self.electrode_frame = ttk.Frame(self.control_frame)
        self.electrode_frame.grid(column=2, row=0)
        self.upper_electrode_frame = sample_frame(
            self.electrode_frame,
            "Upper Electrode",
            self.upper_electrode_move,
        )
        self.upper_electrode_frame.pack()
        self.lower_electrode_frame = sample_frame(
            self.electrode_frame,
            "Lower Electrode",
            self.lower_electrode_move,
        )
        self.lower_electrode_frame.pack()

    def start(self) -> None:
        if self.controller.start_request():
            self.start_controller_button.configure(state=tkinter.DISABLED)
            self.stop_controller_button.configure(state=tkinter.NORMAL)
            self.control_frame.grid(column=1, row=0)

    def stop(self) -> None:
        if self.controller.stop_request():
            self.start_controller_button.configure(state=tkinter.NORMAL)
            self.stop_controller_button.configure(state=tkinter.DISABLED)
            self.control_frame.grid_forget()

    def power(self) -> None:
        s = self.power_status.get() == 0
        self.log.debug(f"Switching electrode motion to {b2onoff(s)}")
        self.controller.power_switch(s)

    def lower_guard_ring_move(self, steps: int = 0) -> None:
        self.controller.lower_guard_ring_move(steps)

    def upper_guard_ring_move(self, steps: int = 0) -> None:
        self.controller.upper_guard_ring_move(steps)

    def lower_electrode_move(self, steps: int = 0) -> None:
        self.controller.lower_electrode_move(steps)

    def upper_electrode_move(self, steps: int = 0) -> None:
        self.controller.upper_electrode_move(steps)


if __name__ == "__main__":
    pass
