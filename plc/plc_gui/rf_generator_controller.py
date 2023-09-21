"""class for rf-generator controller

Author: Daniel Mohr
Date: 2013-01-26
"""

import logging
import logging.handlers
import serial
import sys
import time
import tkinter

from .class_rf_generator import *


log = logging.getLogger("plc.rf_gen_ctrl")
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())


class rf_generator_controller:
    """class for rf-generator controller (trinamix_tmcm_351)

    Author: Daniel Mohr
    Date: 2012-09-06
    """

    def __init__(self, config=None, pw=None, debugprint=None):
        log.info("init")
        self.readbytes = 4096  # read this number of bytes at a time
        self.readbytes = 16384  # read this number of bytes at a time
        self.debug = True
        self.config = config
        self.padx = self.config.values.get("gui", "padx")
        self.pady = self.config.values.get("gui", "pady")
        self.pw = pw
        self.debugprint = debugprint
        self.lastupdate = time.time()
        self.maxcurrent = self.config.values.getint("RF-Generator", "maxcurrent")
        self.maxphase = self.config.values.getint("RF-Generator", "maxphase")
        self.maxcurrent_tmp = self.config.values.getint("RF-Generator", "maxcurrent_tmp")

        self.generator = [None, None, None]
        for g in range(3):
            # ['RF-Generator 1','RF-Generator 2','RF-Generator 3']
            self.generator[g] = class_rf_generator()
            if self.config.values.get("RF-Generator %d" % (g + 1), "power_controller") == "-1":
                self.generator[g].exists = False
            else:
                self.generator[g].exists = True
                self.generator[g].gen_device = self.config.values.get("RF-Generator %d" % (g + 1), "gen_device")
                log.info("rf %d gen_device: %s" % (g, self.generator[g].gen_device))
                self.generator[g].dc_device = self.config.values.get("RF-Generator %d" % (g + 1), "dc_device")
                log.info("rf %d dc_device: %s" % (g, self.generator[g].dc_device))
                self.generator[g].boudrate = self.config.values.get("RF-Generator %d" % (g + 1), "boudrate")
                log.info("rf %d boudrate: %s" % (g, self.generator[g].boudrate))
                databits = [None, None, None, None, None, serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS]
                self.generator[g].databits = databits[int(self.config.values.get("RF-Generator %d" % (g + 1), "databits"))]
                log.info("rf %d databits: %s" % (g, self.generator[g].databits))
                self.generator[g].parity = serial.PARITY_NONE
                log.info("rf %d parity: %s" % (g, self.generator[g].parity))
                if self.config.values.get("RF-Generator %d" % (g + 1), "stopbits") == "1":
                    self.generator[g].stopbits = serial.STOPBITS_ONE
                elif self.config.values.get("RF-Generator %d" % (g + 1), "stopbits") == "1.5":
                    self.generator[g].stopbits = serial.STOPBITS_ONE_POINT_FIVE
                elif self.config.values.get("RF-Generator %d" % (g + 1), "stopbits") == "2":
                    self.generator[g].stopbits = serial.STOPBITS_TWO
                log.info("rf %d stopbits: %s" % (g, self.generator[g].stopbits))
                self.generator[g].readtimeout = float(self.config.values.get("RF-Generator %d" % (g + 1), "readtimeout"))
                log.info("rf %d readtimeout: %s" % (g, self.generator[g].readtimeout))
                self.generator[g].writetimeout = float(self.config.values.get("RF-Generator %d" % (g + 1), "writetimeout"))
                log.info("rf %d writetimeout: %s" % (g, self.generator[g].writetimeout))
                self.generator[g].dev_gen = serial.Serial(
                    port=None,
                    baudrate=self.generator[g].boudrate,
                    bytesize=self.generator[g].databits,
                    parity=self.generator[g].parity,
                    stopbits=self.generator[g].stopbits,
                    timeout=self.generator[g].readtimeout,
                    writeTimeout=self.generator[g].writetimeout,
                )
                self.generator[g].dev_gen.port = self.generator[g].gen_device
                self.generator[g].dev_dc = serial.Serial(
                    port=None,
                    baudrate=self.generator[g].boudrate,
                    bytesize=self.generator[g].databits,
                    parity=self.generator[g].parity,
                    stopbits=self.generator[g].stopbits,
                    timeout=self.generator[g].readtimeout,
                    writeTimeout=self.generator[g].writetimeout,
                )
                self.generator[g].dev_dc.port = self.generator[g].dc_device
                self.generator[g].update_intervall = self.config.values.get("RF-Generator %d" % (g + 1), "update_intervall")
                log.info("rf %d update_intervall: %s" % (g, self.generator[g].update_intervall))
        self.setpoint = dict()
        self.setpoint["connect"] = False
        self.setpoint["run_pattern"] = False
        self.setpoint["write_pattern"] = False
        self.setpoint["pattern_controller"] = None
        self.setpoint["pattern_number_of_generators"] = None
        self.setpoint["pattern_length"] = None
        self.setpoint["pattern_intervall_length"] = None
        self.setpoint["pattern"] = None
        self.actualvalue = dict()
        self.actualvalue["connect"] = False
        self.actualvalue["run_pattern"] = False
        self.actualvalue["pattern_controller"] = None
        self.actualvalue["pattern_number_of_generators"] = None
        self.actualvalue["pattern_length"] = None
        self.actualvalue["pattern_intervall_length"] = None
        self.actualvalue["pattern"] = None
        self.write = self.defaultprint
        # values for the gui
        self.isgui = False
        self.start_button = None
        self.stop_button = None
        self.updateid = None
        self.running_pattern_position = None

    def debugprint(self, s):
        if self.debug:
            print(s)

    def defaultprint(self, s):
        if False:
            print(s)

    def set_default_values(self):
        """set default values

        set setpoint[...] to None
        set actualvalue[...] to None

        Author: Daniel Mohr
        Date: 2012-08-27
        """
        pass

    def update(self, restart=True):
        """if necessary write values self.setpoint to device
        and read them from device to self.actualvalue

        Author: Daniel Mohr
        Date: 2012-09-07
        """
        T_start_update = time.time()
        selfrestart = False
        write2dev = False
        ignite_plasma = False
        if self.actualvalue["connect"]:
            selfrestart = True
            if self.setpoint["write_pattern"]:
                # log.debug("prepare write_pattern")
                write2dev = True
            if (self.setpoint["run_pattern"] != self.actualvalue["run_pattern"]) and (self.setpoint["pattern_controller"] == "microcontroller"):
                # log.debug("prepare run_pattern on microcontroller")
                write2dev = True
            if self.setpoint["run_pattern"] and (self.setpoint["pattern_controller"] == "computer"):
                # running pattern by the computer
                # log.debug("prepare run_pattern on computer: intervall_length = %f sec" % (int(self.setpoint['pattern_intervall_length'] / 1000.0)/1000.0))
                self.generator[0].update_intervall = int(self.setpoint["pattern_intervall_length"] / 1000.0)
                if self.running_pattern_position == None:
                    self.running_pattern_position = 0
                else:
                    self.running_pattern_position = self.running_pattern_position + 1
                    if self.running_pattern_position >= self.setpoint["pattern_length"]:
                        self.running_pattern_position = 0
                write2dev = True
            else:
                self.generator[0].update_intervall = self.config.values.get("RF-Generator 1", "update_intervall")
            for g in range(3):
                if self.generator[g].exists:
                    if self.generator[g].setpoint_ignite_plasma == True:
                        self.generator[g].setpoint_ignite_plasma = False
                        ignite_plasma = True
                        write2dev = True
                    for i in range(4):
                        if self.generator[g].setpoint_channel[i].onoff != self.generator[g].actualvalue_channel[i].onoff:
                            write2dev = True
                            self.generator[g].actualvalue_channel[i].onoff = self.generator[g].setpoint_channel[i].onoff
                        if self.generator[g].setpoint_channel[i].current != self.generator[g].actualvalue_channel[i].current:
                            write2dev = True
                            self.generator[g].actualvalue_channel[i].current = self.generator[g].setpoint_channel[i].current
                        if self.generator[g].setpoint_channel[i].phase != self.generator[g].actualvalue_channel[i].phase:
                            write2dev = True
                            self.generator[g].actualvalue_channel[i].phase = self.generator[g].setpoint_channel[i].phase
                    if self.generator[g].setpoint_rf_onoff != self.generator[g].actualvalue_rf_onoff:
                        write2dev = True
                        self.generator[g].actualvalue_rf_onoff = self.generator[g].setpoint_rf_onoff
            for g in range(3):
                if self.generator[g].exists:
                    l = None
                    try:
                        l = self.generator[g].dev_gen.read(self.readbytes)
                    except:
                        pass
                    if l:
                        log.info("from rf-gen %d: %s" % (g, l))
                    l = None
                    try:
                        l = self.generator[g].dev_dc.read(self.readbytes)
                    except:
                        pass
                    if l:
                        log.info("from rf-dc %d: %s" % (g, l))
        if self.setpoint["connect"] != self.actualvalue["connect"]:
            log.debug("connect/disconnect")
            if self.setpoint["connect"]:
                self.actualvalue["connect"] = True
                self.start()
                self.selfrestart = True
            elif self.setpoint["connect"] == False:
                self.actualvalue["connect"] = False
                self.stop()
                self.selfrestart = False
        elif write2dev:
            if ignite_plasma:
                log.warning("!!!!!!ignite plasma now!!!!!!")
                for g in range(3):
                    if self.generator[g].exists:
                        s = "@D"
                        log.info("to rf-gen %d: %s" % (g, s))
                        self.generator[g].dev_gen.write(s)
                # set maxcurrent_tmp
                for g in range(3):
                    if self.generator[g].exists:
                        c = [0, 0, 0, 0]
                        for i in range(4):
                            c[i] = hex(self.maxcurrent_tmp)[2:].upper()
                            while len(c[i]) < 4:
                                c[i] = "0%s" % c[i]
                            c[i] = "%s%s" % (c[i][2:4], c[i][0:2])
                        si = "#D%s%s%s%s" % (c[2], c[3], c[0], c[1])
                        log.info("to rf-dc %d: %s" % (g, si))
                        self.generator[g].dev_dc.write(si)
                time.sleep(0.01)
                for g in range(3):
                    if self.generator[g].exists:
                        if self.generator[g].actualvalue_rf_onoff:
                            s = "@E"
                            log.info("to rf-gen %d: %s" % (g, s))
                            self.generator[g].dev_gen.write(s)
                time.sleep(0.1)
                # set maxcurrent
                for g in range(3):
                    if self.generator[g].exists:
                        c = [0, 0, 0, 0]
                        for i in range(4):
                            c[i] = hex(self.maxcurrent)[2:].upper()
                            while len(c[i]) < 4:
                                c[i] = "0%s" % c[i]
                            c[i] = "%s%s" % (c[i][2:4], c[i][0:2])
                        si = "#D%s%s%s%s" % (c[2], c[3], c[0], c[1])
                        log.info("to rf-dc %d: %s" % (g, si))
                        self.generator[g].dev_dc.write(si)
                time.sleep(1)
                # set maxcurrent_tmp
                for g in range(3):
                    if self.generator[g].exists:
                        c = [0, 0, 0, 0]
                        for i in range(4):
                            c[i] = hex(self.maxcurrent_tmp)[2:].upper()
                            while len(c[i]) < 4:
                                c[i] = "0%s" % c[i]
                            c[i] = "%s%s" % (c[i][2:4], c[i][0:2])
                        si = "#D%s%s%s%s" % (c[2], c[3], c[0], c[1])
                        log.info("to rf-dc %d: %s" % (g, si))
                        self.generator[g].dev_dc.write(si)
                time.sleep(0.1)
                # max. normal power -> user defined power
                nsteps = 10
                for step in range(nsteps):
                    for g in range(3):
                        if self.generator[g].exists:
                            c = [0, 0, 0, 0]
                            for i in range(4):
                                a = self.generator[g].actualvalue_channel[i].current
                                b = self.maxcurrent
                                ac = int(a + (1.0 - (float(step) / float(nsteps))) * (b - a))
                                log.debug("set pwr to %d" % ac)
                                c[i] = hex(ac)[2:].upper()
                                while len(c[i]) < 4:
                                    c[i] = "0%s" % c[i]
                                c[i] = "%s%s" % (c[i][2:4], c[i][0:2])
                            si = "#D%s%s%s%s" % (c[2], c[3], c[0], c[1])
                            log.info("to rf-dc %d: %s" % (g, si))
                            self.generator[g].dev_dc.write(si)
                    time.sleep(0.1)
                for g in range(3):
                    if self.generator[g].exists:
                        c = [0, 0, 0, 0]
                        for i in range(4):
                            c[i] = hex(self.generator[g].actualvalue_channel[i].current)[2:].upper()
                            while len(c[i]) < 4:
                                c[i] = "0%s" % c[i]
                            c[i] = "%s%s" % (c[i][2:4], c[i][0:2])
                        s = "#D%s%s%s%s" % (c[2], c[3], c[0], c[1])
                        log.info("to rf-dc %d: %s" % (g, s))
                        self.generator[g].dev_dc.write(s)
                log.info("ignited???")
            # output
            write2dev_gen = ["", "", ""]
            write2dev_dc = ["", "", ""]
            # write pattern on the microcontroller
            if self.setpoint["write_pattern"]:
                log.debug("create pattern structure from %s" % self.setpoint["pattern"])
                for g in range(3):
                    if self.generator[g].exists:
                        self.generator[g].actualvalue_pattern = ""
                        for p in range(self.setpoint["pattern_length"]):
                            o = self.setpoint["pattern_number_of_generators"] * 4 * p + g * 4
                            v = 0
                            for c in range(4):
                                if self.setpoint["pattern"][o + c] == "1":
                                    v = v + 2 ** (3 - c)
                            self.generator[g].actualvalue_pattern = "%s0%s" % (self.generator[g].actualvalue_pattern, hex(v)[2].upper())
                            log.debug("pattern for generator %d: %s" % (g, self.generator[g].actualvalue_pattern))
                        if self.setpoint["pattern_controller"] == "microcontroller":
                            log.debug("write pattern to microcontroller")
                            log.debug("val: %d" % int(self.setpoint["pattern_intervall_length"]))
                            l = hex(self.setpoint["pattern_length"])[2:].upper()
                            l = "%02X" % self.setpoint["pattern_length"]
                            il = "%04X" % int(
                                round(
                                    float(self.setpoint["pattern_intervall_length"])
                                    / float(self.config.values.get("RF-Generator", "pattern_microcontroller_intervall_length_factor"))
                                )
                            )
                            il = il[2:4] + il[0:2]
                            write2dev_gen[g] = "%s@G%s%s@I%s" % (write2dev_gen[g], l, self.generator[g].actualvalue_pattern, il)
                            # write2dev_gen[g] = "%s@G%02x%s@I%04x" % (write2dev_gen[g],self.setpoint['pattern_length'],self.generator[g].actualvalue_pattern,int(round(float(self.setpoint['pattern_intervall_length'])/float(self.config.values.get('RF-Generator','pattern_microcontroller_intervall_length_factor')))))
                self.setpoint["write_pattern"] = False
                self.actualvalue["pattern_controller"] = self.setpoint["pattern_controller"]
                self.actualvalue["pattern_number_of_generators"] = self.setpoint["pattern_number_of_generators"]
                self.actualvalue["pattern_length"] = self.setpoint["pattern_length"]
                self.actualvalue["pattern_intervall_length"] = self.setpoint["pattern_intervall_length"]
                self.actualvalue["pattern"] = self.setpoint["pattern"]
            for g in range(3):
                if self.generator[g].exists:
                    if (self.setpoint["run_pattern"] != self.actualvalue["run_pattern"]) and (self.setpoint["pattern_controller"] == "microcontroller"):
                        if self.setpoint["run_pattern"]:
                            log.debug("start pattern on microcontroller")
                            write2dev_gen[g] = "%s@S" % write2dev_gen[g]
                        else:
                            log.debug("stop pattern on microcontroller")
                            write2dev_gen[g] = "%s@T" % write2dev_gen[g]
                        self.actualvalue["run_pattern"] = self.setpoint["run_pattern"]
                    # on/off
                    onoff = 0  # all off
                    if self.setpoint["run_pattern"] and self.setpoint["pattern_controller"] == "computer":
                        # run pattern by the computer
                        log.debug("run pattern on computer ( %d / %d )" % ((self.running_pattern_position + 1), self.actualvalue["pattern_length"]))
                        write2dev_gen[g] = "%s@X%s" % (
                            write2dev_gen[g],
                            self.generator[g].actualvalue_pattern[2 * self.running_pattern_position : 2 * self.running_pattern_position + 2],
                        )
                    else:
                        # normal procedure
                        for i in range(4):
                            if self.generator[g].actualvalue_channel[i].onoff:
                                onoff = onoff + 2 ** (3 - i)
                        onoff = hex(onoff)
                        onoff = "0%s" % onoff[2].upper()
                        write2dev_gen[g] = "%s@X%s" % (write2dev_gen[g], onoff)
                        # current
                        c = [0, 0, 0, 0]
                        for i in range(4):
                            c[i] = hex(self.generator[g].actualvalue_channel[i].current)[2:].upper()
                            while len(c[i]) < 4:
                                c[i] = "0%s" % c[i]
                            c[i] = "%s%s" % (c[i][2:4], c[i][0:2])
                        write2dev_dc[g] = "%s#O#D%s%s%s%s" % (write2dev_dc[g], c[2], c[3], c[0], c[1])
                        # phase
                        p = [0, 0, 0, 0]
                        for i in range(4):
                            p[i] = hex(self.generator[g].actualvalue_channel[i].phase)[2:].upper()
                            while len(p[i]) < 2:
                                p[i] = "0%s" % p[i]
                            p[i] = "%s%s" % (p[i][2:4], p[i][0:2])
                        write2dev_gen[g] = "%s@P%s%s%s%s" % (write2dev_gen[g], p[0], p[1], p[2], p[3])
                        # rf_onoff
                        # enable/disable 13 MHz
                        if self.generator[g].actualvalue_rf_onoff:
                            write2dev_gen[g] = "%s@E" % (write2dev_gen[g])
                        else:
                            write2dev_gen[g] = "%s@D" % (write2dev_gen[g])
            for g in range(3):
                if self.generator[g].exists:
                    if len(write2dev_gen[g]) > 0:
                        log.info("to rf-gen %d: %s" % (g, write2dev_gen[g]))
                        self.generator[g].dev_gen.write(write2dev_gen[g])
                    if len(write2dev_dc[g]) > 0:
                        log.info("to rf-dc %d: %s" % (g, write2dev_dc[g]))
                        self.generator[g].dev_dc.write(write2dev_dc[g])
        T_stop_update = time.time()
        if restart and selfrestart and self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.start_button.after(int(self.generator[0].update_intervall), func=self.update)  # call after ... milliseconds

    def gui(self):
        self.isgui = True
        self.start_button = tkinter.Button(self.pw, text="open", command=self.start_request, padx=self.padx, pady=self.pady)
        self.start_button.grid(row=0, column=0)
        self.stop_button = tkinter.Button(self.pw, text="close", command=self.stop_request, state=tkinter.DISABLED, padx=self.padx, pady=self.pady)
        self.stop_button.grid(row=0, column=1)
        self.set_default_values()

    def start_request(self):
        self.setpoint["connect"] = True
        if self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.update()

    def start(self):
        for g in range(3):
            if self.generator[g].exists:
                log.info("start rf-generator gen %s" % g)
                try:
                    self.generator[g].dev_gen.open()
                    log.debug("connected to generator gen %d" % (g + 1))
                    if self.generator[g].dev_gen.isOpen():
                        self.actualvalue["connect"] = True
                except:
                    self.generator[g].exists = False
                    log.warning("ERROR: cannot open generator gen %d" % (g + 1))
            if self.generator[g].exists:
                log.info("start rf-generator dc %s" % g)
                try:
                    self.generator[g].dev_dc.open()
                    log.debug("connected to generator dc %d" % (g + 1))
                    if self.generator[g].dev_dc.isOpen():
                        self.actualvalue["connect"] = True
                        log.info("to rf-dc %d: #O" % g)
                        self.generator[g].dev_dc.write("#O")
                except:
                    self.generator[g].exists = False
                    log.warning("ERROR: cannot open generator dc %d" % (g + 1))
        if self.isgui and self.actualvalue["connect"]:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.update()
            self.start_button.configure(state=tkinter.DISABLED)
            self.stop_button.configure(state=tkinter.NORMAL)
        else:
            self.setpoint["connect"] = False

    def check_buttons(self):
        if self.isgui:
            if self.actualvalue["connect"]:
                self.start_button.configure(state=tkinter.DISABLED)
                self.stop_button.configure(state=tkinter.NORMAL)
            else:
                self.start_button.configure(state=tkinter.NORMAL)
                self.stop_button.configure(state=tkinter.DISABLED)

    def stop_request(self):
        self.setpoint["connect"] = False
        if self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.updateid = self.update()

    def stop(self):
        for g in range(3):
            if self.generator[g].exists and self.generator[g].dev_gen.isOpen():
                log.info("stop rf-generator gen %s" % g)
                try:
                    self.generator[g].dev_gen.close()
                    log.debug("closed generator gen %d" % (g + 1))
                except:
                    self.generator[g].exists = False
                    self.debugprint("ERROR: cannot close generator gen %d" % (g + 1))
            if self.generator[g].exists and self.generator[g].dev_dc.isOpen():
                self.debugprint("stop rf-generator dc %s" % g)
                try:
                    self.generator[g].dev_dc.write("#o")
                except:
                    pass
                try:
                    self.generator[g].dev_dc.close()
                    self.debugprint("closed generator dc %d" % (g + 1))
                except:
                    self.generator[g].exists = False
                    self.debugprint("ERROR: cannot close generator dc %d" % (g + 1))
        if self.isgui:
            if self.updateid:
                self.start_button.after_cancel(self.updateid)
            self.start_button.configure(state=tkinter.NORMAL)
            self.stop_button.configure(state=tkinter.DISABLED)
            self.actualvalue["connect"] = False
            self.setpoint["connect"] = False
