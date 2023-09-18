"""class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator

Author: Daniel Mohr
Date: 2012-08-27
"""

class class_rf_generator():
    """class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator

    Author: Daniel Mohr
    Date: 2012-08-21
    """
    class class_channel():
        """class for one channel of the generator
        
        Author: Daniel Mohr
        Date: 2012-08-21
        """
        def __init__(self):
            self.onoff = None # True or False
            self.current = 0 # 0 <= current <= 4095
            self.phase = 0 # 0 <= phase <= 255
            # for the gui
            self.onoff_status = None
            self.onoff_status_checkbutton = None
            self.current_status = None
            self.current_status_entry = None
            self.phase_status = None
            self.phase_status_entry = None
            self.choose = None
            self.choose_checkbutton = None

    def __init__(self):
        """init of class for one 'Euro_4x_RF-DC_and_RF-gen'-Generator
        
        Author: Daniel Mohr
        Date: 2012-09-06
        """
        self.exists = False
        self.power_controller = None
        self.power_port = None
        self.power_channel = None
        self.power_status = None
        self.power_status_checkbutton = None
        self.power_cmd = None
        self.channel = [0,1,2,3]
        self.channel[0] = self.class_channel()
        self.channel[1] = self.class_channel()
        self.channel[2] = self.class_channel()
        self.channel[3] = self.class_channel()
        self.setpoint_rf_onoff = None
        self.setpoint_ignite_plasma = None
        self.setpoint_channel = [0,1,2,3]
        self.setpoint_channel[0] = self.class_channel()
        self.setpoint_channel[1] = self.class_channel()
        self.setpoint_channel[2] = self.class_channel()
        self.setpoint_channel[3] = self.class_channel()
        self.actualvalue_pattern = None
        self.actualvalue_rf_onoff = None
        self.actualvalue_channel = [0,1,2,3]
        for i in range(4):
            self.actualvalue_channel[i] = self.class_channel()
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
