from typing import Callable, List, Annotated
from dataclasses import dataclass
import tkinter

"""class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator

Author: Daniel Mohr
Date: 2012-08-27
"""


@dataclass
class ValueRange:
    lo: int
    hi: int


class class_rf_generator:
    """class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator

    Author: Daniel Mohr
    Date: 2012-08-21
    """

    class class_channel:
        """class for one channel of the generator

        Author: Daniel Mohr
        Date: 2012-08-21
        """

        def __init__(self) -> None:
            self.onoff: bool = False  # True or False
            self.current: Annotated[int, ValueRange(0, 4095)] = 0  # 0 <= current <= 4095
            self.phase: Annotated[int, ValueRange(0, 255)] = 0  # 0 <= phase <= 255
            # for the gui
            self.onoff_status: tkinter.IntVar = None  # type: ignore
            self.onoff_status_checkbutton: tkinter.Checkbutton = None  # type: ignore
            self.current_status: tkinter.IntVar = None  # type: ignore
            self.current_status_entry: tkinter.Entry = None  # type: ignore
            self.phase_status: tkinter.IntVar = None  # type: ignore
            self.phase_status_entry: tkinter.Entry = None  # type: ignore
            self.choose: tkinter.IntVar = None  # type: ignore
            self.choose_checkbutton: tkinter.Checkbutton = None  # type: ignore

    def __init__(
        self,
    ) -> None:
        """init of class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator

        Author: Daniel Mohr
        Date: 2012-09-06
        """
        self.exists = False
        self.power_controller: str = None  # type: ignore
        self.power_port: str = None  # type: ignore
        self.power_channel: str = None  # type: ignore
        self.power_status: tkinter.IntVar = None  # type: ignore
        self.power_status_checkbutton: tkinter.Checkbutton = None  # type: ignore
        self.power_cmd: Callable[[], None] = lambda: None
        self.channel: List[class_rf_generator.class_channel] = []
        for i in range(4):
            self.channel.append(self.class_channel())
        self.setpoint_rf_onoff = None
        self.setpoint_ignite_plasma = None
        self.setpoint_channel: List[class_rf_generator.class_channel] = []
        for i in range(4):
            self.setpoint_channel.append(self.class_channel())
        self.actualvalue_pattern = None
        self.actualvalue_rf_onoff = None
        self.actualvalue_channel: List[class_rf_generator.class_channel] = []
        for i in range(4):
            self.actualvalue_channel.append(self.class_channel())
            self.actualvalue_channel[i].current = 0
            self.actualvalue_channel[i].phase = 0
        self.update_intervall = None
        self.device = None
        self.rf_onoff = None
        self.gen_device = None
        self.dc_device = None
        self.boudrate = None
        self.databits = None
        self.parity = None
        self.stopbits = None
        self.readtimeout = None
        self.writetimeout = None

    def set_status(self):
        """set the status of all elements

        at the moment ADC is not available; therefore set everything to 0
        """
        for i in range(4):
            self.channel[i].onoff = False
            self.channel[i].current = 0
            self.channel[i].phase = 0
        self.rf_onoff = False
