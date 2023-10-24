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
class for rf-generator controller
"""

import logging
import logging.handlers
from typing import Dict, List, Any

from .class_rf_generator import class_rf_generator
from .read_config_file import read_config_file
from .controller import controller


class rf_generator_controller(controller):
    """
    class for rf-generator controller (trinamix_tmcm_351)
    """

    def __init__(self, config: read_config_file, _log: logging.Logger, controllers: Dict[str, controller]) -> None:
        self.log = _log
        self.log.info("init")
        self.readbytes = 4096  # read this number of bytes at a time
        self.readbytes = 16384  # read this number of bytes at a time
        self.debug = True
        self.config = config
        self.generators_count = self.config.values.getint("RF-Generator", "count")
        self.maxcurrent = self.config.values.getint("RF-Generator", "maxcurrent")
        self.maxphase = self.config.values.getint("RF-Generator", "maxphase")
        self.maxcurrent_tmp = self.config.values.getint("RF-Generator", "maxcurrent_tmp")

        self.generator: List[class_rf_generator] = []
        for g in range(3):
            # ['RF-Generator 1','RF-Generator 2','RF-Generator 3']
            pwc = self.config.values.get(f"RF-Generator {g + 1}", "power_controller")
            exs = pwc != "-1"
            self.generator.append(
                class_rf_generator(
                    exs, g, self.config, self.log.getChild(f"rf_gen{g}"), controllers[pwc] if exs else controllers["dc"]
                )
            )
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

        self.connected = False
        self.setpoint: Dict[str, Any] = {}
        self.setpoint["pattern_controller"] = None
        self.setpoint["pattern_number_of_generators"] = None
        self.setpoint["pattern_length"] = None
        self.setpoint["pattern_intervall_length"] = None
        self.setpoint["pattern"] = None
        self.actualvalue: Dict[str, Any] = {}
        self.actualvalue["run_pattern"] = False
        self.actualvalue["pattern_controller"] = None
        self.actualvalue["pattern_number_of_generators"] = None
        self.actualvalue["pattern_length"] = None
        self.actualvalue["pattern_intervall_length"] = None
        self.actualvalue["pattern"] = None

        self.running_pattern_position = 0

    def ignite(self) -> None:
        self.log.warning("!!!!!!ignite plasma now!!!!!!")
        for g in range(3):
            if self.generator[g].exists:
                self.generator[g].ignition(self.maxcurrent, self.maxcurrent_tmp)
        self.log.info("ignited???")

    def write_pattern(self) -> None:
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

    def run_pattern(self) -> None:
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

    def unrun_pattern(self) -> None:
        self.generator[0].update_intervall = self.config.values.getfloat("RF-Generator 1", "update_intervall")
        if self.setpoint["pattern_controller"] == "microcontroller":
            for g in range(3):
                if self.generator[g].exists:
                    self.log.debug("stop pattern on microcontroller")
                    wtg = "@T"
                    self.log.info(f"To rf-gen {g}: {wtg}")
                    self.generator[g].dev_gen.write(wtg.encode("utf-8"))

    def start_request(self) -> None:
        self.log.debug("Start request")
        self.start()

    def start(self) -> None:
        self.log.debug("Starting")
        self.connected = True
        for g in range(self.generators_count):
            if self.generator[g].exists:
                self.generator[g].open_serial()

    def stop_request(self) -> None:
        self.log.debug("Stop request")
        self.stop()

    def stop(self) -> None:
        self.log.debug("Stopping")
        for g in range(self.generators_count):
            if self.generator[g].exists:
                self.generator[g].close_serial()
        self.connected = False


if __name__ == "__main__":
    pass
