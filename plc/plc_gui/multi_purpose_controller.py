"""class for multi purpose controller (blue box)

Author: Daniel Mohr
Date: 2013-05-13
"""

import logging
from typing import Dict, List, Any

from . import plcclientserverclass
from .read_config_file import read_config_file


class multi_purpose_controller(plcclientserverclass.socket_communication_class):
    """class for multi purpose controller (blue box)

    Author: Daniel Mohr
    Date: 2013-05-13
    """

    def __init__(self, log: logging.Logger, config: read_config_file, bufsize: int = 4096):
        super().__init__(log, config, "mpc", bufsize)

        self.myservername = "multi_purpose_controller_server"
        # self.log = logging.getLogger("plc.plc_gui.multi_purpose_controller")
        # self.cmd = self.config.values.get("mpc", "server_command")
        # self.start_server = self.config.values.getboolean("mpc", "start_server")
        # self.logfile = self.config.values.get("mpc", "server_logfile")
        # self.datalogfile = self.config.values.get("mpc", "server_datalogfile")
        # self.dev = self.config.values.get("mpc", "server_device")
        # self.rf = self.config.values.get("mpc", "server_runfile")
        # self.ip = self.config.values.get("mpc", "server_ip")
        # self.sport = self.config.values.getint("mpc", "server_port")
        # self.server_max_start_time = self.config.values.getfloat("mpc", "server_max_start_time")
        # self.st = self.config.values.getfloat("mpc", "server_timedelay")
        # self.update_intervall = self.config.values.getint("mpc", "update_intervall") / 1000.0
        # self.trigger_out = self.config.values.getboolean("mpc", "trigger_out")
        # self.padx = self.config.values.get("gui", "padx")
        # self.pady = self.config.values.get("gui", "pady")
        # setpoint/actualvalue:
        self.actualvalue: Dict[str, Any] = {
            "DO": 4 * [None],
            "R": 2 * [None],
            "U05": None,
            "U15": None,
            "U24": None,
            "DAC": 4 * [0.0],
            "DI": 4 * [None],
            "ADC": 8 * [0],
        }  # dict of values on device
        self.setpoint: Dict[str, Any] = {
            "DO": 4 * [None],
            "R": 2 * [None],
            "U05": None,
            "U15": None,
            "U24": None,
            "DAC": 4 * [0.0],
        }  # dict of requested values, which will be updated to device
        self.ports: List[str] = ["DO", "R", "U05", "U15", "U24", "DAC", "DI", "ADC"]
        self.ports_without_channel: List[str] = ["U05", "U15", "U24"]
        self.setpoint_port: List[str] = ["DO", "R", "U05", "U15", "U24", "DAC"]
        self.actualvalue_port: List[str] = ["DO", "R", "U05", "U15", "U24", "DAC", "DI", "ADC"]

    def set_default_values(self) -> None:
        """set default values

        set setpoint[...] to 0 or False
        if connected to real device, get actualvalue[...] from it
        otherwise set actualvalue[...] to  0 or False

        Author: Daniel Mohr
        Date: 2012-11-27
        """
        self.lock.acquire()  # lock
        port = "DO"
        for channel in range(4):
            self.setpoint[port][channel] = None
        port = "R"
        for channel in range(2):
            self.setpoint[port][channel] = None
        for port in ["U05", "U15", "U24"]:
            self.setpoint[port] = None
        port = "DAC"
        for channel in range(4):
            self.setpoint[port][channel] = None
        if self.socket is not None:
            self.socketlock.acquire()  # lock
            self.get_actualvalues()
            self.socketlock.release()  # release the lock
        else:
            # self.actualvalue[port][channel] = False
            port = "DO"
            for channel in range(4):
                self.actualvalue[port][channel] = False
            port = "R"
            for channel in range(2):
                self.actualvalue[port][channel] = False
            for port in ["U05", "U15", "U24"]:
                self.actualvalue[port] = False
            port = "DAC"
            for channel in range(4):
                self.actualvalue[port][channel] = 0
            port = "DI"
            for channel in range(4):
                self.actualvalue[port][channel] = False
            port = "ADC"
            for channel in range(8):
                self.actualvalue[port][channel] = 0
        self.lock.release()  # release the lock

    def actualvalue2setpoint(self) -> None:
        port = "DO"
        for channel in range(4):
            self.setpoint[port][channel] = self.actualvalue[port][channel]
        port = "DAC"
        for channel in range(4):
            self.setpoint[port][channel] = self.actualvalue[port][channel]
        for port in ["U05", "U15", "U24"]:
            self.setpoint[port] = self.actualvalue[port]
        port = "DAC"
        for channel in range(4):
            self.setpoint[port][channel] = self.actualvalue[port][channel]
