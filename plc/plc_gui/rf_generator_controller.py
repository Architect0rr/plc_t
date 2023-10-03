"""class for rf-generator controller

Author: Daniel Mohr
Date: 2013-01-26
"""

import logging
import logging.handlers
import time
import tkinter
import tkinter.ttk
from typing import Dict, List, Any

from .class_rf_generator import class_rf_generator
from .read_config_file import read_config_file


class rf_generator_controller:
    """class for rf-generator controller (trinamix_tmcm_351)

    Author: Daniel Mohr
    Date: 2012-09-06
    """

    def __init__(self, config: read_config_file, _log: logging.Logger) -> None:
        self.log = _log
        self.log.info("init")
        self.readbytes = 4096  # read this number of bytes at a time
        self.readbytes = 16384  # read this number of bytes at a time
        self.debug = True
        self.config = config
        self.padx = self.config.values.get("gui", "padx")
        self.pady = self.config.values.get("gui", "pady")
        # self.pw = pw
        self.generators_count = self.config.values.getint("RF-Generator", "count")
        # self.debugprint = debugprint
        self.lastupdate = time.time()
        self.maxcurrent = self.config.values.getint("RF-Generator", "maxcurrent")
        self.maxphase = self.config.values.getint("RF-Generator", "maxphase")
        self.maxcurrent_tmp = self.config.values.getint("RF-Generator", "maxcurrent_tmp")

        self.generator: List[class_rf_generator] = []
        for g in range(3):
            # ['RF-Generator 1','RF-Generator 2','RF-Generator 3']
            exs = self.config.values.get(f"RF-Generator {g + 1}", "power_controller") != "-1"
            self.generator.append(class_rf_generator(exs, g, self.config, self.log.getChild("rf_gen")))
            if exs:
                self.log.info("rf %d gen_device: %s" % (g, self.generator[g].gen_device))
                self.log.info("rf %d dc_device: %s" % (g, self.generator[g].dc_device))
                self.log.info("rf %d boudrate: %s" % (g, self.generator[g].boudrate))
                self.log.info("rf %d databits: %s" % (g, self.generator[g].databits))
                self.log.info("rf %d parity: %s" % (g, self.generator[g].parity))
                self.log.info("rf %d stopbits: %s" % (g, self.generator[g].stopbits))
                self.log.info("rf %d readtimeout: %s" % (g, self.generator[g].readtimeout))
                self.log.info("rf %d writetimeout: %s" % (g, self.generator[g].writetimeout))
                self.log.info("rf %d update_intervall: %s" % (g, self.generator[g].update_intervall))
        self.setpoint: Dict[str, Any] = {}
        self.setpoint["connect"] = False
        self.setpoint["run_pattern"] = False
        self.setpoint["write_pattern"] = False
        self.setpoint["pattern_controller"] = None
        self.setpoint["pattern_number_of_generators"] = None
        self.setpoint["pattern_length"] = None
        self.setpoint["pattern_intervall_length"] = None
        self.setpoint["pattern"] = None
        self.actualvalue: Dict[str, Any] = {}
        self.actualvalue["connect"] = False
        self.actualvalue["run_pattern"] = False
        self.actualvalue["pattern_controller"] = None
        self.actualvalue["pattern_number_of_generators"] = None
        self.actualvalue["pattern_length"] = None
        self.actualvalue["pattern_intervall_length"] = None
        self.actualvalue["pattern"] = None
        # self.write = self.defaultprint
        # values for the gui
        # self.isgui = True

        self.updateid: str | None = None
        self.running_pattern_position = 0

    # def debugprint(self, s):
    #     if self.debug:
    #         print(s)

    # def defaultprint(self, s):
    #     if False:
    #         print(s)

    # def set_default_values(self):
    #     """set default values

    #     set setpoint[...] to None
    #     set actualvalue[...] to None

    #     Author: Daniel Mohr
    #     Date: 2012-08-27
    #     """
    #     pass

    def update(self, restart=True) -> None:
        """if necessary write values self.setpoint to device
        and read them from device to self.actualvalue

        Author: Daniel Mohr
        Date: 2012-09-07
        """
        write2dev = False
        ignite_plasma = False
        if self.actualvalue["connect"]:
            if self.setpoint["write_pattern"]:
                write2dev = True
            if (self.setpoint["run_pattern"] != self.actualvalue["run_pattern"]) and (
                self.setpoint["pattern_controller"] == "microcontroller"
            ):
                write2dev = True
            if self.setpoint["run_pattern"] and (self.setpoint["pattern_controller"] == "computer"):
                # running pattern by the computer
                self.generator[0].update_intervall = int(self.setpoint["pattern_intervall_length"] / 1000.0)
                self.running_pattern_position = self.running_pattern_position + 1
                if self.running_pattern_position >= self.setpoint["pattern_length"]:
                    self.running_pattern_position = 0
                write2dev = True
            else:
                self.generator[0].update_intervall = self.config.values.getfloat("RF-Generator 1", "update_intervall")
            for g in range(3):
                if self.generator[g].exists:
                    if self.generator[g].setpoint_ignite_plasma:
                        self.generator[g].setpoint_ignite_plasma = False
                        ignite_plasma = True
                        write2dev = True
                    for i in range(4):
                        if (
                            self.generator[g].setpoint_channel[i].onoff
                            != self.generator[g].actualvalue_channel[i].onoff
                        ):
                            write2dev = True
                            self.generator[g].actualvalue_channel[i].onoff = self.generator[g].setpoint_channel[i].onoff
                        if (
                            self.generator[g].setpoint_channel[i].current
                            != self.generator[g].actualvalue_channel[i].current
                        ):
                            write2dev = True
                            self.generator[g].actualvalue_channel[i].current = (
                                self.generator[g].setpoint_channel[i].current
                            )
                        if (
                            self.generator[g].setpoint_channel[i].phase
                            != self.generator[g].actualvalue_channel[i].phase
                        ):
                            write2dev = True
                            self.generator[g].actualvalue_channel[i].phase = self.generator[g].setpoint_channel[i].phase
                    if self.generator[g].setpoint_rf_onoff != self.generator[g].actualvalue_rf_onoff:
                        write2dev = True
                        self.generator[g].actualvalue_rf_onoff = self.generator[g].setpoint_rf_onoff
            for g in range(3):
                if self.generator[g].exists:
                    try:
                        self.log.info(f"From rf-gen {g}: {self.generator[g].dev_gen.read(self.readbytes)}")
                    except Exception:
                        pass
                    try:
                        self.log.info(f"From rf-dc {g}: {self.generator[g].dev_dc.read(self.readbytes)}")
                    except Exception:
                        pass
        if self.setpoint["connect"] != self.actualvalue["connect"]:
            self.log.debug("connect/disconnect")
            if self.setpoint["connect"]:
                self.actualvalue["connect"] = True
                self.start()
                self.selfrestart = True
            elif not self.setpoint["connect"]:
                self.actualvalue["connect"] = False
                self.stop()
                self.selfrestart = False
        elif write2dev:
            if ignite_plasma:
                self.log.warning("!!!!!!ignite plasma now!!!!!!")
                for g in range(3):
                    if self.generator[g].exists:
                        s = "@D"
                        self.log.info(f"To rf-gen {g}: {s}")
                        self.generator[g].dev_gen.write(s.encode("utf-8"))
                # set maxcurrent_tmp
                for g in range(3):
                    if self.generator[g].exists:
                        c: List[str] = []
                        for i in range(4):
                            c.append(hex(self.maxcurrent_tmp)[2:].upper())
                            while len(c[i]) < 4:
                                c[i] = f"0{c[i]}"
                            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
                        si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
                        self.log.info(f"To rf-dc {g}: {si}")
                        self.generator[g].dev_dc.write(si.encode("urf-8"))
                time.sleep(0.01)
                for g in range(3):
                    if self.generator[g].exists:
                        if self.generator[g].actualvalue_rf_onoff:
                            s = "@E"
                            self.log.info(f"To rf-gen {g}: {s}")
                            self.generator[g].dev_gen.write(s.encode("utf-8"))
                time.sleep(0.1)
                # set maxcurrent
                for g in range(3):
                    if self.generator[g].exists:
                        c: List[str] = []
                        for i in range(4):
                            c.append(hex(self.maxcurrent)[2:].upper())
                            while len(c[i]) < 4:
                                c[i] = f"0{c[i]}"
                            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
                        si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
                        self.log.info(f"To rf-dc {g}: {si}")
                        self.generator[g].dev_dc.write(si.encode("utf-8"))
                time.sleep(1)
                # set maxcurrent_tmp
                for g in range(3):
                    if self.generator[g].exists:
                        c: List[str] = []
                        for i in range(4):
                            c.append(hex(self.maxcurrent_tmp)[2:].upper())
                            while len(c[i]) < 4:
                                c[i] = f"0{c[i]}"
                            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
                        si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
                        self.log.info(f"To rf-dc {g}: {si}")
                        self.generator[g].dev_dc.write(si.encode("utf-8"))
                time.sleep(0.1)
                # max. normal power -> user defined power
                nsteps = 10
                for step in range(nsteps):
                    for g in range(3):
                        if self.generator[g].exists:
                            c: List[str] = []
                            for i in range(4):
                                a = self.generator[g].actualvalue_channel[i].current
                                b = self.maxcurrent
                                ac = int(a + (1.0 - (float(step) / float(nsteps))) * (b - a))
                                self.log.debug("set pwr to %d" % ac)
                                c.append(hex(ac)[2:].upper())
                                while len(c[i]) < 4:
                                    c[i] = f"0{c[i]}"
                                c[i] = f"{c[i][2:4]}{c[i][0:2]}"
                            si = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
                            self.log.info(f"To rf-dc {g}: {si}")
                            self.generator[g].dev_dc.write(si.encode("utf-8"))
                    time.sleep(0.1)
                for g in range(3):
                    if self.generator[g].exists:
                        c: List[str] = []
                        for i in range(4):
                            c.append(hex(self.generator[g].actualvalue_channel[i].current)[2:].upper())
                            while len(c[i]) < 4:
                                c[i] = f"0{c[i]}"
                            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
                        s = f"#D{c[2]}{c[3]}{c[0]}{c[1]}"
                        self.log.info(f"To rf-dc {g}: {s}")
                        self.generator[g].dev_dc.write(s.encode("utf-8"))
                self.log.info("ignited???")
            # output
            write2dev_gen = ["", "", ""]
            write2dev_dc = ["", "", ""]
            # write pattern on the microcontroller
            if self.setpoint["write_pattern"]:
                self.log.debug("create pattern structure from %s" % self.setpoint["pattern"])
                for g in range(3):
                    if self.generator[g].exists:
                        self.generator[g].actualvalue_pattern = ""
                        for ppp in range(self.setpoint["pattern_length"]):
                            o = self.setpoint["pattern_number_of_generators"] * 4 * ppp + g * 4
                            v = 0
                            for ck in range(4):
                                if self.setpoint["pattern"][o + ck] == "1":
                                    v = v + 2 ** (3 - ck)
                            self.generator[g].actualvalue_pattern = "%s0%s" % (
                                self.generator[g].actualvalue_pattern,
                                hex(v)[2].upper(),
                            )
                            self.log.debug("pattern for generator %d: %s" % (g, self.generator[g].actualvalue_pattern))
                        if self.setpoint["pattern_controller"] == "microcontroller":
                            self.log.debug("write pattern to microcontroller")
                            self.log.debug("val: %d" % int(self.setpoint["pattern_intervall_length"]))
                            # l = hex(self.setpoint["pattern_length"])[2:].upper()
                            lo = "%02X" % self.setpoint["pattern_length"]
                            il = "%04X" % int(
                                round(
                                    float(self.setpoint["pattern_intervall_length"])
                                    / float(
                                        self.config.values.get(
                                            "RF-Generator",
                                            "pattern_microcontroller_intervall_length_factor",
                                        )
                                    )
                                )
                            )
                            il = il[2:4] + il[0:2]
                            write2dev_gen[g] = "%s@G%s%s@I%s" % (
                                write2dev_gen[g],
                                lo,
                                self.generator[g].actualvalue_pattern,
                                il,
                            )
                            # write2dev_gen[g] = "%s@G%02x%s@I%04x" % (write2dev_gen[g],self.setpoint['pattern_length'],self.generator[g].actualvalue_pattern,int(round(float(self.setpoint['pattern_intervall_length'])/float(self.config.values.get('RF-Generator','pattern_microcontroller_intervall_length_factor')))))
                self.setpoint["write_pattern"] = False
                self.actualvalue["pattern_controller"] = self.setpoint["pattern_controller"]
                self.actualvalue["pattern_number_of_generators"] = self.setpoint["pattern_number_of_generators"]
                self.actualvalue["pattern_length"] = self.setpoint["pattern_length"]
                self.actualvalue["pattern_intervall_length"] = self.setpoint["pattern_intervall_length"]
                self.actualvalue["pattern"] = self.setpoint["pattern"]
            for g in range(3):
                if self.generator[g].exists:
                    if (self.setpoint["run_pattern"] != self.actualvalue["run_pattern"]) and (
                        self.setpoint["pattern_controller"] == "microcontroller"
                    ):
                        if self.setpoint["run_pattern"]:
                            self.log.debug("start pattern on microcontroller")
                            write2dev_gen[g] = "%s@S" % write2dev_gen[g]
                        else:
                            self.log.debug("stop pattern on microcontroller")
                            write2dev_gen[g] = "%s@T" % write2dev_gen[g]
                        self.actualvalue["run_pattern"] = self.setpoint["run_pattern"]
                    # on/off
                    onoff: int = 0  # all off
                    if self.setpoint["run_pattern"] and self.setpoint["pattern_controller"] == "computer":
                        # run pattern by the computer
                        self.log.debug(
                            "run pattern on computer ( %d / %d )"
                            % (
                                (self.running_pattern_position + 1),
                                self.actualvalue["pattern_length"],
                            )
                        )
                        write2dev_gen[g] = "%s@X%s" % (
                            write2dev_gen[g],
                            self.generator[g].actualvalue_pattern[
                                2 * self.running_pattern_position : 2 * self.running_pattern_position + 2
                            ],
                        )
                    else:
                        # normal procedure
                        for i in range(4):
                            if self.generator[g].actualvalue_channel[i].onoff:
                                onoff = onoff + 2 ** (3 - i)
                        onoff_s = hex(onoff)
                        onoff_s = "0%s" % onoff_s[2].upper()
                        write2dev_gen[g] = "%s@X%s" % (write2dev_gen[g], onoff_s)
                        # current
                        c = []
                        for i in range(4):
                            c.append(hex(self.generator[g].actualvalue_channel[i].current)[2:].upper())
                            while len(c[i]) < 4:
                                c[i] = f"0{c[i]}"
                            c[i] = f"{c[i][2:4]}{c[i][0:2]}"
                        write2dev_dc[g] = f"{write2dev_dc[g]}#O#D{c[2]}{c[3]}{c[0]}{c[1]}"
                        # phase
                        p: List[str] = []
                        for i in range(4):
                            p.append(hex(self.generator[g].actualvalue_channel[i].phase)[2:].upper())
                            while len(p[i]) < 2:
                                p[i] = f"0{p[i]}"
                            p[i] = f"{p[i][2:4]}{p[i][0:2]}"
                        write2dev_gen[g] = f"{write2dev_gen[g]}@P{p[0]}{p[1]}{p[2]}{p[3]}"
                        # rf_onoff
                        # enable/disable 13 MHz
                        if self.generator[g].actualvalue_rf_onoff:
                            write2dev_gen[g] = f"{write2dev_gen[g]}@E"
                        else:
                            write2dev_gen[g] = f"{write2dev_gen[g]}@D"
            for g in range(3):
                if self.generator[g].exists:
                    if len(write2dev_gen[g]) > 0:
                        self.log.info(f"To rf-gen {g}: {write2dev_gen[g]}")
                        self.generator[g].dev_gen.write(write2dev_gen[g].encode("utf-8"))
                    if len(write2dev_dc[g]) > 0:
                        self.log.info("to rf-dc %d: %s" % (g, write2dev_dc[g]))
                        self.generator[g].dev_dc.write(write2dev_dc[g].encode("utf-8"))
        # if restart and selfrestart and self.isgui:
        #     if self.updateid:
        #         self.start_button.after_cancel(self.updateid)
        #     self.updateid = self.start_button.after(
        #         int(self.generator[0].update_intervall), func=self.update
        #     )  # call after ... milliseconds

    # def gui(self):
    #     self.isgui = True
    #     self.start_button = tkinter.Button(self.pw, text="open", command=self.start_request, padx=self.padx, pady=self.pady)
    #     self.start_button.grid(row=0, column=0)
    #     self.stop_button = tkinter.Button(self.pw, text="close", command=self.stop_request, state=tkinter.DISABLED, padx=self.padx, pady=self.pady)
    #     self.stop_button.grid(row=0, column=1)
    #     self.set_default_values()

    def start_request(self):
        self.setpoint["connect"] = True
        self.actualvalue["connect"] = True
        self.start()

    def start(self):
        for g in range(self.generators_count):
            if self.generator[g].exists:
                self.generator[g].open_serial()

    # def check_buttons(self):
    #     if self.isgui:
    #         if self.actualvalue["connect"]:
    #             self.start_button.configure(state=tkinter.DISABLED)
    #             self.stop_button.configure(state=tkinter.NORMAL)
    #         else:
    #             self.start_button.configure(state=tkinter.NORMAL)
    #             self.stop_button.configure(state=tkinter.DISABLED)

    def stop_request(self):
        self.setpoint["connect"] = False
        # if self.isgui:
        #     if self.updateid:
        #         self.start_button.after_cancel(self.updateid)
        #     self.updateid = self.update()

    def stop(self):
        for g in range(self.generators_count):
            if self.generator[g].exists and self.generator[g].dev_gen.is_open:
                self.log.info(f"Stoping rf-generator gen {g}")
                try:
                    self.generator[g].dev_gen.close()
                    self.log.debug(f"Closed generator gen {g + 1}")
                except Exception:
                    self.generator[g].exists = False
                    self.log.debug(f"ERROR: cannot close generator gen {g + 1}")
            if self.generator[g].exists and self.generator[g].dev_dc.is_open:
                self.log.debug(f"Stoping rf-generator dc {g}")
                try:
                    self.generator[g].dev_dc.write(b"#o")
                except Exception:
                    pass
                try:
                    self.generator[g].dev_dc.close()
                    self.log.debug(f"Closed generator dc {g + 1}")
                except Exception:
                    self.generator[g].exists = False
                    self.log.debug(f"ERROR: cannot close generator dc {g + 1}")
        # if self.isgui:
        #     if self.updateid:
        #         self.start_button.after_cancel(self.updateid)
        #     self.start_button.configure(state=tkinter.NORMAL)
        #     self.stop_button.configure(state=tkinter.DISABLED)
        self.actualvalue["connect"] = False
        self.setpoint["connect"] = False


# class rfgc_gui(tkinter.ttk.Frame):
#     def __init__(self, _root: tkinter.LabelFrame, backend: rf_generator_controller) -> None:
#         super().__init__(_root)
#         self.root = _root
#         self.backend = backend
#         self.start_button = tkinter.Button(_root, text="open", command=self.start)
#         self.start_button.grid(row=0, column=0)
#         self.stop_button = tkinter.Button(
#             _root,
#             text="close",
#             command=self.stop,
#             state=tkinter.DISABLED,
#         )
#         self.stop_button.grid(row=0, column=1)
#         # backend.set_default_values()

#     def start(self) -> None:
#         self.start_button.configure(state=tkinter.DISABLED)
#         self.stop_button.configure(state=tkinter.NORMAL)
#         self.backend.start_request()

#     def stop(self) -> None:
#         self.stop_button.configure(state=tkinter.DISABLED)
#         self.start_button.configure(state=tkinter.NORMAL)
#         self.backend.stop_request()
