"""gui for Translation Stage

Author: Daniel Mohr
Date: 2013-01-26
"""

import logging
import tkinter

from ..plc_tools.conversion import b2onoff
from .read_config_file import read_config_file
from tkinter import ttk
from typing import Dict, Any


class translation_stage:
    """gui for Translation Stage

    Author: Daniel Mohr
    Date: 2012-08-27
    """

    def __init__(self, config: read_config_file, pw: ttk.LabelFrame, _log: logging.Logger, controller: Dict) -> None:
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
        self.config = config
        self.pw = pw
        self.log = _log
        self.controller = controller
        self.padx = self.config.values.get("gui", "padx")
        self.pady = self.config.values.get("gui", "pady")
        # create gui
        self.init_frame = tkinter.Frame(pw)
        self.init_frame.grid(column=0, row=0)
        self.power_status = tkinter.IntVar()
        self.power_button = tkinter.Checkbutton(
            self.init_frame, text="Power", command=self.power, variable=self.power_status, state=tkinter.DISABLED
        )
        self.power_button.pack()
        self.start_controller_button = tkinter.Button(
            self.init_frame,
            text="open RS232 (tsc)",
            command=self.controller["tsc"].start_request,
            padx=self.padx,
            pady=self.pady,
        )
        self.start_controller_button.pack()
        self.stop_controller_button = tkinter.Button(
            self.init_frame,
            text="close RS232 (tsc)",
            command=self.controller["tsc"].stop_request,
            padx=self.padx,
            pady=self.pady,
        )
        self.stop_controller_button.pack()
        # control area
        self.x_frame = tkinter.LabelFrame(pw, text="x")
        self.x_frame.grid(column=1, row=0)
        self.y_frame = tkinter.LabelFrame(pw, text="y")
        self.y_frame.grid(column=2, row=0)
        self.z_frame = tkinter.LabelFrame(pw, text="z")
        self.z_frame.grid(column=3, row=0)
        # x
        f = self.x_frame
        self.x: Dict[str, Any] = {}
        self.x["10000 down cmd"] = self.x_10000_down
        self.x["1000 down cmd"] = self.x_1000_down
        self.x["n up/down cmd"] = self.x_n_up_down
        self.x["1000 up cmd"] = self.x_1000_up
        self.x["10000 up cmd"] = self.x_10000_up
        self.x["10000 down button"] = tkinter.Button(
            f, command=self.x["10000 down cmd"], text="x-10000", padx=self.padx, pady=self.pady
        )
        self.x["10000 down button"].grid(column=0, row=0)
        self.x["1000 down button"] = tkinter.Button(
            f, command=self.x["1000 down cmd"], text="x-1000", padx=self.padx, pady=self.pady
        )
        self.x["1000 down button"].grid(column=1, row=0)
        self.x["n up/down frame"] = tkinter.LabelFrame(f, text="n-steps")
        self.x["n up/down frame"].grid(column=2, row=0)
        self.x["n up/down val"] = tkinter.IntVar()
        self.x["n up/down entry"] = tkinter.Entry(
            self.x["n up/down frame"], textvariable=self.x["n up/down val"], width=6
        )
        self.x["n up/down entry"].grid(column=0, row=0)
        self.x["n up/down button"] = tkinter.Button(
            self.x["n up/down frame"], command=self.x["n up/down cmd"], text="do", padx=self.padx, pady=self.pady
        )
        self.x["n up/down button"].grid(column=1, row=0)
        self.x["1000 up button"] = tkinter.Button(
            f, command=self.x["1000 up cmd"], text="x+1000", padx=self.padx, pady=self.pady
        )
        self.x["1000 up button"].grid(column=3, row=0)
        self.x["10000 up button"] = tkinter.Button(
            f, command=self.x["10000 up cmd"], text="x+10000", padx=self.padx, pady=self.pady
        )
        self.x["10000 up button"].grid(column=4, row=0)
        # y
        f = self.y_frame
        self.y: Dict[str, Any] = {}
        self.y["10000 down cmd"] = self.y_10000_down
        self.y["1000 down cmd"] = self.y_1000_down
        self.y["n up/down cmd"] = self.y_n_up_down
        self.y["1000 up cmd"] = self.y_1000_up
        self.y["10000 up cmd"] = self.y_10000_up
        self.y["10000 down button"] = tkinter.Button(
            f, command=self.y["10000 down cmd"], text="y-10000", padx=self.padx, pady=self.pady
        )
        self.y["10000 down button"].grid(column=0, row=0)
        self.y["1000 down button"] = tkinter.Button(
            f, command=self.y["1000 down cmd"], text="y-1000", padx=self.padx, pady=self.pady
        )
        self.y["1000 down button"].grid(column=1, row=0)
        self.y["n up/down frame"] = tkinter.LabelFrame(f, text="n-steps")
        self.y["n up/down frame"].grid(column=2, row=0)
        self.y["n up/down val"] = tkinter.IntVar()
        self.y["n up/down entry"] = tkinter.Entry(
            self.y["n up/down frame"], textvariable=self.y["n up/down val"], width=6
        )
        self.y["n up/down entry"].grid(column=0, row=0)
        self.y["n up/down button"] = tkinter.Button(
            self.y["n up/down frame"], command=self.y["n up/down cmd"], text="do", padx=self.padx, pady=self.pady
        )
        self.y["n up/down button"].grid(column=1, row=0)
        self.y["1000 up button"] = tkinter.Button(
            f, command=self.y["1000 up cmd"], text="y+1000", padx=self.padx, pady=self.pady
        )
        self.y["1000 up button"].grid(column=3, row=0)
        self.y["10000 up button"] = tkinter.Button(
            f, command=self.y["10000 up cmd"], text="y+10000", padx=self.padx, pady=self.pady
        )
        self.y["10000 up button"].grid(column=4, row=0)
        # z
        f = self.z_frame
        self.z: Dict[str, Any] = {}
        self.z["10000 down cmd"] = self.z_10000_down
        self.z["1000 down cmd"] = self.z_1000_down
        self.z["n up/down cmd"] = self.z_n_up_down
        self.z["1000 up cmd"] = self.z_1000_up
        self.z["10000 up cmd"] = self.z_10000_up
        self.z["10000 down button"] = tkinter.Button(
            f, command=self.z["10000 down cmd"], text="z-10000", padx=self.padx, pady=self.pady
        )
        self.z["10000 down button"].grid(column=0, row=0)
        self.z["1000 down button"] = tkinter.Button(
            f, command=self.z["1000 down cmd"], text="z-1000", padx=self.padx, pady=self.pady
        )
        self.z["1000 down button"].grid(column=1, row=0)
        self.z["n up/down frame"] = tkinter.LabelFrame(f, text="n-steps")
        self.z["n up/down frame"].grid(column=2, row=0)
        self.z["n up/down val"] = tkinter.IntVar()
        self.z["n up/down entry"] = tkinter.Entry(
            self.z["n up/down frame"], textvariable=self.z["n up/down val"], width=6
        )
        self.z["n up/down entry"].grid(column=0, row=0)
        self.z["n up/down button"] = tkinter.Button(
            self.z["n up/down frame"], command=self.z["n up/down cmd"], text="do", padx=self.padx, pady=self.pady
        )
        self.z["n up/down button"].grid(column=1, row=0)
        self.z["1000 up button"] = tkinter.Button(
            f, command=self.z["1000 up cmd"], text="z+1000", padx=self.padx, pady=self.pady
        )
        self.z["1000 up button"].grid(column=3, row=0)
        self.z["10000 up button"] = tkinter.Button(
            f, command=self.z["10000 up cmd"], text="z+10000", padx=self.padx, pady=self.pady
        )
        self.z["10000 up button"].grid(column=4, row=0)

    def power(self):
        if self.power_status.get() == 0:
            s = False
        else:
            s = True
        self.log.debug("switch translation stage to %s" % b2onoff(s))
        self.controller[self.config.values.get("translation stage controller", "power_controller")].setpoint[
            self.config.values.get("translation stage controller", "power_port")
        ][int(self.config.values.get("translation stage controller", "power_channel"))] = s

    def x_10000_down(self):
        self.controller["tsc"].setpoint["x rel"] = -10000

    def x_1000_down(self):
        self.controller["tsc"].setpoint["x rel"] = -1000

    def x_n_up_down(self):
        steps = 0
        try:
            steps = int(self.x["n up/down val"].get())
        except Exception:
            self.x["n up/down val"].set("ERROR")
            return
        self.controller["tsc"].setpoint["x rel"] = steps

    def x_10000_up(self):
        self.controller["tsc"].setpoint["x rel"] = 10000

    def x_1000_up(self):
        self.controller["tsc"].setpoint["x rel"] = 1000

    def y_10000_down(self):
        self.controller["tsc"].setpoint["y rel"] = -10000

    def y_1000_down(self):
        self.controller["tsc"].setpoint["y rel"] = -1000

    def y_n_up_down(self):
        steps = 0
        try:
            steps = int(self.y["n up/down val"].get())
        except Exception:
            self.y["n up/down val"].set("ERROR")
            return
        self.controller["tsc"].setpoint["y rel"] = steps

    def y_10000_up(self):
        self.controller["tsc"].setpoint["y rel"] = 10000

    def y_1000_up(self):
        self.controller["tsc"].setpoint["y rel"] = 1000

    def z_10000_down(self):
        self.controller["tsc"].setpoint["z rel"] = -10000

    def z_1000_down(self):
        self.controller["tsc"].setpoint["z rel"] = -1000

    def z_n_up_down(self):
        steps = 0
        try:
            steps = int(self.z["n up/down val"].get())
        except Exception:
            self.z["n up/down val"].set("ERROR")
            return
        self.controller["tsc"].setpoint["z rel"] = steps

    def z_10000_up(self):
        self.controller["tsc"].setpoint["z rel"] = 10000

    def z_1000_up(self):
        self.controller["tsc"].setpoint["z rel"] = 1000

    def check_buttons(self):
        if self.controller["dc"].connected:
            self.power_button.configure(state=tkinter.NORMAL)
        else:
            self.power_button.configure(state=tkinter.DISABLED)
        if self.controller["tsc"].actualvalue["connect"]:
            self.start_controller_button.configure(state=tkinter.DISABLED)
            self.stop_controller_button.configure(state=tkinter.NORMAL)
            # x
            self.x["10000 down button"].configure(state=tkinter.NORMAL)
            self.x["1000 down button"].configure(state=tkinter.NORMAL)
            self.x["n up/down entry"].configure(state=tkinter.NORMAL)
            self.x["n up/down button"].configure(state=tkinter.NORMAL)
            self.x["1000 up button"].configure(state=tkinter.NORMAL)
            self.x["10000 up button"].configure(state=tkinter.NORMAL)
            # y
            self.y["10000 down button"].configure(state=tkinter.NORMAL)
            self.y["1000 down button"].configure(state=tkinter.NORMAL)
            self.y["n up/down entry"].configure(state=tkinter.NORMAL)
            self.y["n up/down button"].configure(state=tkinter.NORMAL)
            self.y["1000 up button"].configure(state=tkinter.NORMAL)
            self.y["10000 up button"].configure(state=tkinter.NORMAL)
            # z
            self.z["10000 down button"].configure(state=tkinter.NORMAL)
            self.z["1000 down button"].configure(state=tkinter.NORMAL)
            self.z["n up/down entry"].configure(state=tkinter.NORMAL)
            self.z["n up/down button"].configure(state=tkinter.NORMAL)
            self.z["1000 up button"].configure(state=tkinter.NORMAL)
            self.z["10000 up button"].configure(state=tkinter.NORMAL)
        else:
            self.start_controller_button.configure(state=tkinter.NORMAL)
            self.stop_controller_button.configure(state=tkinter.DISABLED)
            # x
            self.x["10000 down button"].configure(state=tkinter.DISABLED)
            self.x["1000 down button"].configure(state=tkinter.DISABLED)
            self.x["n up/down entry"].configure(state=tkinter.DISABLED)
            self.x["n up/down button"].configure(state=tkinter.DISABLED)
            self.x["1000 up button"].configure(state=tkinter.DISABLED)
            self.x["10000 up button"].configure(state=tkinter.DISABLED)
            # y
            self.y["10000 down button"].configure(state=tkinter.DISABLED)
            self.y["1000 down button"].configure(state=tkinter.DISABLED)
            self.y["n up/down entry"].configure(state=tkinter.DISABLED)
            self.y["n up/down button"].configure(state=tkinter.DISABLED)
            self.y["1000 up button"].configure(state=tkinter.DISABLED)
            self.y["10000 up button"].configure(state=tkinter.DISABLED)
            # z
            self.z["10000 down button"].configure(state=tkinter.DISABLED)
            self.z["1000 down button"].configure(state=tkinter.DISABLED)
            self.z["n up/down entry"].configure(state=tkinter.DISABLED)
            self.z["n up/down button"].configure(state=tkinter.DISABLED)
            self.z["1000 up button"].configure(state=tkinter.DISABLED)
            self.z["10000 up button"].configure(state=tkinter.DISABLED)
