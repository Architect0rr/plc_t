import threading
from typing import Dict, Any
from abc import abstractmethod


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
