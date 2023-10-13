"""gui for controller

Author: Daniel Mohr
Date: 2012-08-27
"""

import threading
from typing import Dict, Any
from abc import abstractmethod

from .digital_controller import *
from .multi_purpose_controller import *
from .electrode_motion_controller import *
from .translation_stage_controller import *
from .rf_generator_controller import *


class controller:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.setpoint: Dict[str, Any] = {}
        self.actualvalue: Dict[str, Any] = {}
        self.connected = False

    @abstractmethod
    def start_request(self) -> None:
        ...

    @abstractmethod
    def stop_request(self) -> None:
        ...
