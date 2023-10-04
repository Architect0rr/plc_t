"""class for rf-generator controller

Author: Daniel Mohr
Date: 2013-01-26
"""

import logging
import logging.handlers
import time

# import tkinter
# import tkinter.ttk
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
            self.generator.append(class_rf_generator(exs, g, self.config, self.log.getChild(f"rf_gen{g}")))
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
        # self.setpoint["connect"] = False
        # self.setpoint["run_pattern"] = False
        # self.setpoint["write_pattern"] = False
        self.setpoint["pattern_controller"] = None
        self.setpoint["pattern_number_of_generators"] = None
        self.setpoint["pattern_length"] = None
        self.setpoint["pattern_intervall_length"] = None
        self.setpoint["pattern"] = None
        self.actualvalue: Dict[str, Any] = {}
        # self.actualvalue["connect"] = False
        self.connected = False
        self.actualvalue["run_pattern"] = False
        self.actualvalue["pattern_controller"] = None
        self.actualvalue["pattern_number_of_generators"] = None
        self.actualvalue["pattern_length"] = None
        self.actualvalue["pattern_intervall_length"] = None
        self.actualvalue["pattern"] = None

        self.updateid: str | None = None
        self.running_pattern_position = 0

    def ignite(self):
        self.log.warning("!!!!!!ignite plasma now!!!!!!")
        for g in range(3):
            if self.generator[g].exists:
                self.generator[g].ignition(self.maxcurrent, self.maxcurrent_tmp)
        self.log.info("ignited???")

    def write_pattern(self):
        self.log.debug(f'Creating pattern structure from {self.setpoint["pattern"]}')
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
                    self.log.debug("Write pattern to microcontroller")
                    self.log.debug(f'Val: {int(self.setpoint["pattern_intervall_length"])}')

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
                    avp = self.generator[g].actualvalue_pattern
                    tw = f"@G{lo}{avp}@I{il}"
                    self.log.info(f"To rf-gen {g}: {tw}")
                    self.generator[g].dev_gen.write(tw.encode("utf-8"))
        # self.setpoint["write_pattern"] = False
        self.actualvalue["pattern_controller"] = self.setpoint["pattern_controller"]
        self.actualvalue["pattern_number_of_generators"] = self.setpoint["pattern_number_of_generators"]
        self.actualvalue["pattern_length"] = self.setpoint["pattern_length"]
        self.actualvalue["pattern_intervall_length"] = self.setpoint["pattern_intervall_length"]
        self.actualvalue["pattern"] = self.setpoint["pattern"]

    def run_pattern(self):
        for g in range(3):
            if self.generator[g].exists:
                if self.setpoint["pattern_controller"] == "microcontroller":
                    self.generator[0].update_intervall = self.config.values.getfloat(
                        "RF-Generator 1", "update_intervall"
                    )
                    self.log.debug("start pattern on microcontroller")
                    wtg = "@S"

                elif self.setpoint["pattern_controller"] == "computer":
                    self.generator[0].update_intervall = int(self.setpoint["pattern_intervall_length"] / 1000.0)
                    self.running_pattern_position = self.running_pattern_position + 1
                    if self.running_pattern_position >= self.setpoint["pattern_length"]:
                        self.running_pattern_position = 0
                    # run pattern by the computer
                    self.log.debug(
                        f'Running pattern on computer ( {self.running_pattern_position + 1} / {self.actualvalue["pattern_length"]})'
                    )
                    vl = self.generator[g].actualvalue_pattern[
                        2 * self.running_pattern_position : 2 * self.running_pattern_position + 2
                    ]
                    wtg = f"@X{vl}"
                else:
                    raise Exception()
                self.log.info(f"To rf-gen {g}: {wtg}")
                self.generator[g].dev_gen.write(wtg.encode("utf-8"))

    def unrun_pattern(self):
        self.generator[0].update_intervall = self.config.values.getfloat("RF-Generator 1", "update_intervall")
        if self.setpoint["pattern_controller"] == "microcontroller":
            for g in range(3):
                if self.generator[g].exists:
                    self.log.debug("stop pattern on microcontroller")
                    wtg = "@T"
                    self.log.info(f"To rf-gen {g}: {wtg}")
                    self.generator[g].dev_gen.write(wtg.encode("utf-8"))

    # def update(self) -> None:
    #     """if necessary write values self.setpoint to device
    #     and read them from device to self.actualvalue

    #     Author: Daniel Mohr
    #     Date: 2012-09-07
    #     """
    #     if self.connected:
    #         for g in range(3):
    #             if self.generator[g].exists:
    #                 self.generator[g].update()

    def start_request(self) -> None:
        self.log.debug("Start request")
        self.start()

    def start(self):
        self.log.debug("Starting")
        self.connected = True
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

    def stop_request(self) -> None:
        self.log.debug("Stop request")
        self.stop()

    def stop(self) -> None:
        self.log.debug("Stopping")
        for g in range(self.generators_count):
            if self.generator[g].exists:
                self.generator[g].close_serial()
        self.connected = False
