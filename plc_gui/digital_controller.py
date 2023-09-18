"""class for digital controller (red box)

Author: Daniel Mohr
Date: 2013-05-13
"""

import logging

from . import plcclientserverclass

class digital_controller(plcclientserverclass.socket_communication_class):
    """class for digital controller (red box)

    Author: Daniel Mohr
    Date: 2013-05-13
    """
    def myinit(self):
        self.myservername = "digital_controller_server"
        self.log = logging.getLogger('plc.plc_gui.digital_controller')
        self.cmd = self.config.values.get('dc','server_command')
        self.start_server = self.config.values.getboolean('dc','start_server')
        self.logfile = self.config.values.get('dc','server_logfile')
        self.datalogfile = self.config.values.get('dc','server_datalogfile')
        self.dev = self.config.values.get('dc','server_device')
        self.rf = self.config.values.get('dc','server_runfile')
        self.ip = self.config.values.get('dc','server_ip')
        self.sport = self.config.values.getint('dc','server_port')
        self.server_max_start_time = self.config.values.getfloat('dc','server_max_start_time')
        self.st = self.config.values.get('dc','server_timedelay')
        self.update_intervall = self.config.values.getint('dc','update_intervall')/1000.0
        self.trigger_out = self.config.values.getboolean('dc','trigger_out')
        self.padx = self.config.values.get('gui','padx')
        self.pady = self.config.values.get('gui','pady')
        # setpoint/actualvalue:
        self.setpoint = {'A': 8*[None], 'B': 8*[None], 'dispenser': {'n': None, 'ton': None, 'shake': False, 'port': None, 'channel': None, 'toff': None}, 'C': 8*[None], 'D': 8*[None]} # dict of requested values, which will be updated to device
        self.actualvalue = {'A': 8*[None], 'B': 8*[None], 'dispenser': {'n': None, 'ton': None, 'shake': False, 'port': None, 'channel': None, 'toff': None}, 'C': 8*[None], 'D': 8*[None]} # dict of values on device
        self.ports = ['A','B','C','D']

    def set_default_values(self):
        """set default values

        set setpoint[...] to 0 or False
        if connected to real device, get actualvalue[...] from it
        otherwise set actualvalue[...] to  0 or False
        
        Author: Daniel Mohr
        Date: 2012-11-27
        """
        self.lock.acquire() # lock
        for port in self.ports:
            for channel in range(8):
                self.setpoint[port][channel] = None
        if self.isconnect:
            self.socketlock.acquire() # lock
            self.get_actualvalues()
            self.socketlock.release() # release the lock
        else:
            for port in self.ports:
                for channel in range(8):
                    self.actualvalue[port][channel] = False
        self.lock.release() # release the lock

    def myextra_socket_communication_with_server(self):
        self.setpoint['dispenser']['shake'] = False

    def actualvalue2setpoint(self):
        for port in self.ports:
                for channel in range(8):
                    self.setpoint[port][channel] = self.actualvalue[port][channel]
