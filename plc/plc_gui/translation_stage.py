"""gui for Translation Stage

Author: Daniel Mohr
Date: 2013-01-26
"""

import re
from enum import Enum
from typing import Dict
import tkinter as tk
from tkinter import ttk

from ..plc_tools.conversion import b2onoff
from .utils import Master
from .translation_stage_controller import TSC
from .misc import except_notify


class Direction(Enum):
    X = 1
    Y = 2
    Z = 3


class group(ttk.LabelFrame, Master):
    def __init__(self, _root: ttk.LabelFrame, direction: Direction, backend: TSC, master: Master) -> None:
        if direction == Direction.X:
            txt_dir = "x"
        elif direction == Direction.Y:
            txt_dir = "y"
        elif direction == Direction.Z:
            txt_dir = "z"
        else:
            raise RuntimeError(f"Direction '{direction}' does not exists")

        ttk.LabelFrame.__init__(self, _root, text=txt_dir)
        Master.__init__(self, master)

        self.direction = direction
        self.backend = backend

        vcmd = (self.register(self.validate), "%P", "%W")
        ivcmd = (self.register(self.on_invalid), "%W")

        self.btn_10000_down = ttk.Button(
            self,
            command=lambda: self.move(-10000),
            text="-10000",
        )
        self.btn_10000_down.grid(column=0, row=0)
        self.btn_1000_down = ttk.Button(
            self,
            command=lambda: self.move(-1000),
            text="-1000",
        )
        self.btn_1000_down.grid(column=1, row=0)

        self.n_frame = ttk.LabelFrame(self, text="n-steps")
        self.n_frame.grid(column=2, row=0)
        self.n_val = tk.IntVar()
        self.n_entry = tk.Entry(self.n_frame, textvariable=self.n_val, width=6)
        self.n_entry.grid(column=0, row=0)
        self.n_entry.configure(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
        self.n_btn = ttk.Button(self.n_frame, command=self.n_set, text="do", state=tk.DISABLED)
        self.n_btn.grid(column=1, row=0)
        self.btn_1000_up = ttk.Button(
            self,
            command=lambda: self.move(1000),
            text="1000",
        )
        self.btn_1000_up.grid(column=3, row=0)
        self.btn_10000_up = ttk.Button(
            self,
            command=lambda: self.move(10000),
            text="10000",
        )
        self.btn_10000_up.grid(column=4, row=0)

    def move(self, n: int) -> None:
        if self.direction == Direction.X:
            self.backend.x = n
        elif self.direction == Direction.Y:
            self.backend.y = n
        elif self.direction == Direction.Z:
            self.backend.z = n

    def n_set(self) -> None:
        try:
            steps = int(self.n_val.get())
        except Exception:
            self.log.exception("Error in getting n value")
            raise
        self.move(steps)
        self.n_btn.configure(state=tk.DISABLED)

    def upd(self) -> None:
        if self.backend.connected:
            self.btn_10000_down.configure(state=tk.NORMAL)
            self.btn_1000_down.configure(state=tk.NORMAL)
            self.btn_10000_up.configure(state=tk.NORMAL)
            self.btn_1000_up.configure(state=tk.NORMAL)
            self.n_entry.configure(state=tk.NORMAL)
        else:
            self.btn_10000_down.configure(state=tk.DISABLED)
            self.btn_1000_down.configure(state=tk.DISABLED)
            self.btn_10000_up.configure(state=tk.DISABLED)
            self.btn_1000_up.configure(state=tk.DISABLED)
            self.n_entry.configure(state=tk.DISABLED)
            self.n_btn.configure(state=tk.DISABLED)

    def validate(self, _value, _widget) -> bool:
        widget_name = _widget.split(".")[-1].strip()
        try:
            try:
                value = int(_value)
            except Exception:
                return False
            if re.match(r"\-\d+", _value) or re.match(r"\d+", _value):
                self.n_btn.configure(state=tk.NORMAL)
                self.n_entry.configure(background="green")
                return True
            else:
                self.n_btn.configure(state=tk.DISABLED)
                self.n_entry.configure(background="red")
                return False
        except RuntimeError as e:
            except_notify.show(e, f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            self.log.exception(f"widget: '{_widget}' aka '{widget_name}', value: '{_value}'")
            raise

    def on_invalid(self, widget) -> None:
        widget_name = widget.split(".")[-1].strip()
        self.n_btn.configure(state=tk.DISABLED)
        self.n_entry.configure(background="red")


class translation_stage(ttk.LabelFrame, Master):
    """gui for Translation Stage

    Author: Daniel Mohr
    Date: 2012-08-27
    """

    # def __init__(self, config: read_config_file, pw: ttk.LabelFrame, _log: logging.Logger, controller: Dict) -> None:
    def __init__(self, _root: ttk.Frame, backend: TSC, controller: Dict, master: Master) -> None:
        """__init__(self,config=None,pw=None,debugprint=None,controller=None)

        create gui for Translation Stage

        Parameters:
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           debugprint : function
                        function to call for print debug information

        Author: Daniel Mohr
        Date: 2012-09-05
        """
        ttk.LabelFrame.__init__(self, _root, text="Translation stage controller")
        self.backend = backend
        Master.__init__(self, master)

        self.controller = controller
        # create gui
        self.init_frame = ttk.Frame(self)
        self.init_frame.grid(column=0, row=0)
        self.power_status = tk.IntVar()
        self.power_button = ttk.Checkbutton(
            self.init_frame, text="Power", command=self.power, variable=self.power_status, state=tk.DISABLED
        )
        self.power_button.pack()
        self.start_controller_button = ttk.Button(self.init_frame, text="open RS232 (tsc)", command=self.start)
        self.start_controller_button.pack()
        self.stop_controller_button = ttk.Button(
            self.init_frame, text="close RS232 (tsc)", command=self.stop, state=tk.DISABLED
        )
        self.stop_controller_button.pack()
        # control area
        self.x_frame = group(self, Direction.X, self.backend, self)
        self.x_frame.grid(column=1, row=0)
        self.y_frame = group(self, Direction.Y, self.backend, self)
        self.y_frame.grid(column=2, row=0)
        self.z_frame = group(self, Direction.Z, self.backend, self)
        self.z_frame.grid(column=3, row=0)

    def power(self) -> None:
        s = self.power_status.get() != 0
        self.log.debug("switch translation stage to %s" % b2onoff(s))
        self.backend.power(s)

    def upd(self) -> None:
        Master.upd(self)
        if self.backend.pc.connected:
            self.power_button.configure(state=tk.NORMAL)
        else:
            self.power_button.configure(state=tk.DISABLED)

    def exit(self) -> None:
        self.stop()

    def start(self) -> None:
        if self.backend.start_request():
            self.start_controller_button.configure(state=tk.DISABLED)
            self.stop_controller_button.configure(state=tk.NORMAL)
        else:
            self.start_controller_button.configure(state=tk.NORMAL)
            self.stop_controller_button.configure(state=tk.DISABLED)

    def stop(self) -> None:
        if self.backend.stop_request():
            self.start_controller_button.configure(state=tk.NORMAL)
            self.stop_controller_button.configure(state=tk.DISABLED)
        else:
            self.start_controller_button.configure(state=tk.DISABLED)
            self.stop_controller_button.configure(state=tk.NORMAL)
