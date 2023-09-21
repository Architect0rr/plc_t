"""read config file

Author: Daniel Mohr
Date: 2013-05-14
"""

import configparser
from pathlib import Path


class read_config_file:
    """read config file

    Author: Daniel Mohr
    Date: 2013-05-14
    """

    def __init__(self, system_wide_ini_file: str, user_ini_file: str) -> None:
        self.values = configparser.ConfigParser()
        # set default sections and variables
        self.set_default(self.values, system_wide_ini_file=system_wide_ini_file, user_ini_file=user_ini_file)

        # read ini-files
        self.values.read(Path(self.values.get("ini", "system_wide_ini_file")))
        self.values.read(Path(self.values.get("ini", "user_ini_file")))
        # check camera sections
        self.number_of_cameras = self.values.getint("cameras", "n")
        n = 0
        for i in range(self.number_of_cameras):
            if self.values.has_section("camera%d" % (i + 1)) and self.values.has_option("camera%d" % (i + 1), "guid") and (self.values.get("camera%d" % (i + 1), "guid") != "-2"):
                n += 1
            else:
                break
        self.number_of_cameras = n
        # check acceleration sensor sections
        self.number_of_acceleration_sensor = self.values.getint("acceleration_sensors", "n")
        n = 0
        for i in range(self.number_of_acceleration_sensor):
            if (
                self.values.has_section("acceleration_sensor%d" % (i + 1))
                and self.values.has_option("acceleration_sensor%d" % (i + 1), "SerialNumber")
                and (self.values.get("acceleration_sensor%d" % (i + 1), "SerialNumber") != "-2")
            ):
                n += 1
            else:
                break
        self.number_of_acceleration_sensor = n

    def set_default(self, c: configparser.ConfigParser, system_wide_ini_file: str = "/etc/plc.cfg", user_ini_file = "~/.plc.cfg") -> None:
        # ini
        c.add_section("ini")
        c.set("ini", "system_wide_ini_file", system_wide_ini_file)
        c.set("ini", "user_ini_file", user_ini_file)
        c.set("ini", "log_file", "/tmp/plc.log")
        c.set("ini", "default_setpoints_file", "-1")  # -1 sets no file
        c.set("ini", "key_binding_setpoints_previous", "<KeyPress-F7>")
        c.set("ini", "key_binding_setpoints_next", "<KeyPress-F8>")
        c.set("ini", "key_binding_setpoints_set", "<KeyPress-F9>")
        c.set("ini", "extern_program_camera_client", "camera_client.py")
        c.set("ini", "extern_program_digital_controller_client", "digital_controller_client.py")
        c.set("ini", "extern_program_multi_purpose_controller_client", "multi_purpose_controller_client.py")
        c.set("ini", "extern_program_debug_controller", "debug_controller.py")
        c.set("ini", "extern_program_plc_viewer", "plc_viewer.py")
        c.set("ini", "extern_program_rawmovieviewer", "rawmovieviewer.py")
        # gui
        c.add_section("gui")
        c.set("gui", "update_intervall", "300")  # milliseconds; should be >= 10
        c.set("gui", "check_buttons_intervall", "666")  # milliseconds; should be >= 10
        c.set("gui", "padx", "0p")
        c.set("gui", "pady", "0p")
        c.set("gui", "debug_area_height", "5")
        c.set("gui", "debug_area_width", "100")
        # controller
        # digital controller (red box)
        c.add_section("dc")  # digital controller (red box)
        c.set("dc", "server_command", "digital_controller_server.py")
        c.set("dc", "start_server", "1")  # start program/cammand
        c.set("dc", "connect_server", "0")  # connect on startup of plc.py
        c.set("dc", "server_logfile", "/tmp/digital_controller.log")
        c.set("dc", "server_datalogfile", "/tmp/digital_controller.data")
        c.set("dc", "server_device", "/dev/digital_controller")  # -1 to disable for; for test only! no real communication is possible!
        c.set("dc", "server_runfile", "/tmp/digital_controller.pids")
        c.set("dc", "server_ip", "localhost")
        c.set("dc", "server_port", "15112")
        c.set("dc", "server_max_start_time", "5.0")  # seconds
        c.set("dc", "server_timedelay", "0.05")
        c.set("dc", "update_intervall", "300")  # milliseconds; should be >= 10
        c.set("dc", "complete_update_intervall", "6")  # seconds; should be >= 1
        c.set("dc", "trigger_out", "1")  # trigger output to device, default: True
        # multi purpose controller (blue box)
        c.add_section("mpc")  # multi purpose controller (blue box)
        c.set("mpc", "server_command", "multi_purpose_controller_server.py")
        c.set("mpc", "start_server", "1")  # start program/cammand
        c.set("mpc", "connect_server", "0")  # connect on startup of plc.py
        c.set("mpc", "server_logfile", "/tmp/multi_purpose_controller.log")
        c.set("mpc", "server_datalogfile", "/tmp/multi_purpose_controller.data")
        c.set("mpc", "server_device", "/dev/multi_purpose_controller")  # -1 to disable for; for test only! no real communication is possible!
        c.set("mpc", "server_runfile", "/tmp/multi_purpose_controller.pids")
        c.set("mpc", "server_ip", "localhost")
        c.set("mpc", "server_port", "15113")
        c.set("mpc", "server_max_start_time", "5.0")  # seconds
        c.set("mpc", "server_timedelay", "0.05")
        c.set("mpc", "update_intervall", "300")  # milliseconds; should be >= 10; no data will be send or received from the server.
        c.set("mpc", "complete_update_intervall", "6")  # seconds; should be >= 1
        c.set("mpc", "trigger_out", "0")  # trigger output to device, default: False
        # RF-Generator
        c.add_section("RF-Generator")
        c.set("RF-Generator", "maxcurrent", "2500")  # for Zyflex; for Dodec only 2000
        c.set("RF-Generator", "maxcurrent_tmp", "3000")  # for Zyflex; for Dodec only 2500
        c.set("RF-Generator", "maxphase", "255")
        c.set("RF-Generator", "RF_only_master", "1")
        c.set("RF-Generator", "pattern_file", "-1")
        c.set("RF-Generator", "pattern_microcontroller_intervall_length_factor", "4")
        c.set("RF-Generator", "pattern_microcontroller_min_intervall_length", "200")  # 50 * 4 * 10^-6 sec
        c.set("RF-Generator", "pattern_microcontroller_max_intervall_length", "131068")  # 32767 * 4 * 10^-6 sec
        c.add_section("RF-Generator 1")
        c.set("RF-Generator 1", "power_controller", "dc")  # -1 sets not activ
        c.set("RF-Generator 1", "power_port", "A")
        c.set("RF-Generator 1", "power_channel", "4")
        c.set("RF-Generator 1", "gen_device", "/dev/RF_GEN_01")
        c.set("RF-Generator 1", "dc_device", "/dev/RF_DC_01")
        c.set("RF-Generator 1", "boudrate", "9600")
        c.set("RF-Generator 1", "databits", "8")
        c.set("RF-Generator 1", "stopbits", "1")
        c.set("RF-Generator 1", "readtimeout", "0")
        c.set("RF-Generator 1", "writetimeout", "0")
        c.set("RF-Generator 1", "update_intervall", "222")
        c.add_section("RF-Generator 2")
        c.set("RF-Generator 2", "power_controller", "dc")  # -1 sets not activ
        c.set("RF-Generator 2", "power_port", "A")
        c.set("RF-Generator 2", "power_channel", "5")
        c.set("RF-Generator 2", "gen_device", "/dev/RF_GEN_02")
        c.set("RF-Generator 2", "dc_device", "/dev/RF_DC_02")
        c.set("RF-Generator 2", "boudrate", "9600")
        c.set("RF-Generator 2", "databits", "8")
        c.set("RF-Generator 2", "stopbits", "1")
        c.set("RF-Generator 2", "readtimeout", "0")
        c.set("RF-Generator 2", "writetimeout", "0")
        c.set("RF-Generator 2", "update_intervall", "222")
        c.add_section("RF-Generator 3")
        c.set("RF-Generator 3", "power_controller", "dc")  # -1 sets not activ
        c.set("RF-Generator 3", "power_port", "A")
        c.set("RF-Generator 3", "power_channel", "6")
        c.set("RF-Generator 3", "gen_device", "/dev/RF_GEN_03")
        c.set("RF-Generator 3", "dc_device", "/dev/RF_DC_03")
        c.set("RF-Generator 3", "boudrate", "9600")
        c.set("RF-Generator 3", "databits", "8")
        c.set("RF-Generator 3", "stopbits", "1")
        c.set("RF-Generator 3", "readtimeout", "0")
        c.set("RF-Generator 3", "writetimeout", "0")
        c.set("RF-Generator 3", "update_intervall", "222")
        # electrode motion controller
        c.add_section("electrode motion controller")
        c.set("electrode motion controller", "devicename", "/dev/zero")  # -1 sets not activ
        c.set("electrode motion controller", "boudrate", "9600")
        c.set("electrode motion controller", "databits", "8")
        c.set("electrode motion controller", "stopbits", "1")
        c.set("electrode motion controller", "readtimeout", "0")  # seconds
        c.set("electrode motion controller", "writetimeout", "0")  # seconds
        c.set("electrode motion controller", "power_controller", "dc")
        c.set("electrode motion controller", "power_port", "B")
        c.set("electrode motion controller", "power_channel", "5")
        c.set("electrode motion controller", "update_intervall", "333")  # milliseconds
        c.set("electrode motion controller", "T_off", "50")  # milliseconds; time between 2 steps
        c.set("electrode motion controller", "disable_lower_guard_ring", "1")
        # translation stage controller
        c.add_section("translation stage controller")
        c.set("translation stage controller", "devicename", "/dev/null")  # -1 sets not activ
        c.set("translation stage controller", "boudrate", "9600")
        c.set("translation stage controller", "databits", "8")
        c.set("translation stage controller", "stopbits", "1")
        c.set("translation stage controller", "readtimeout", "0")  # seconds
        c.set("translation stage controller", "writetimeout", "0")  # seconds
        c.set("translation stage controller", "power_controller", "dc")
        c.set("translation stage controller", "power_port", "B")
        c.set("translation stage controller", "power_channel", "4")
        c.set("translation stage controller", "update_intervall", "333")  # milliseconds
        # camera
        c.add_section("cameras")
        c.set("cameras", "n", "5")  # maximal number of cameras
        c.set("cameras", "key_binding_view_all", "<KeyPress-F5>")  # view and no record
        c.set("cameras", "key_binding_record_all", "<KeyPress-F6>")  # view and record
        c.set("cameras", "additionally_command_for_view_all", "-1")  # e. g. 'ssh plexp2 \"killall -USR1 vd_grab_univ\"'
        c.set("cameras", "additionally_command_for_record_all", "-1")  # e. g. 'ssh plexp2 \"killall -USR2 vd_grab_univ\"'
        c.set("cameras", "stop_camera_servers_on_exit", "1")
        c.set("cameras", "width_in_main_tab", "300")
        c.add_section("camera1")
        c.set("camera1", "control_frame_width", "500")
        c.set("camera1", "server_command", "camera_server.py")
        c.set("camera1", "start_server", "1")
        c.set("camera1", "server_logfile", "/tmp/camera1.log")
        c.set("camera1", "server_runfile", "/tmp/camera1.pids")
        c.set("camera1", "ip", "localhost")
        c.set("camera1", "port", "15114")
        c.set("camera1", "server_max_start_time", "5.0")  # seconds
        c.set("camera1", "recv_bufsize", "4096")
        c.set("camera1", "update_img_delay", "6")  # milliseconds
        # c.set('camera1','guid','0x000a47010f07b1ec') # -1 to disable guid; -2 to disable complete camera
        c.set("camera1", "guid", "2892819639808492")  # -1 to disable guid and some other settings; -2 to disable complete camera
        c.set("camera1", "vendor", "AVT")
        c.set("camera1", "model", "Guppy F080B")
        c.set("camera1", "mode", "FORMAT7_0")  # -1 to disable
        c.set("camera1", "color_coding", "Y8")  # -1 to disable
        c.set("camera1", "framerate", "30")  # -1 to disable
        c.set("camera1", "unit_position x", "2")
        c.set("camera1", "unit_position y", "2")
        c.set("camera1", "max x-image", "1032")
        c.set("camera1", "max y-image", "778")
        c.set("camera1", "x-image size", "default")
        c.set("camera1", "y-image size", "default")
        c.set("camera1", "x-image position", "default")
        c.set("camera1", "y-image position", "default")
        c.set("camera1", "brightness", "default")
        c.set("camera1", "trigger_delay", "default")
        c.set("camera1", "shutter", "default")
        c.set("camera1", "trigger", "default")
        c.set("camera1", "gain", "default")
        c.set("camera1", "gamma", "default")
        c.set("camera1", "exposure", "default")
        c.set("camera1", "camera_file_prefix1", "/tmp/cam_$guid_$date")
        c.set("camera1", "camera_file_prefix2", "/tmp/cam_$guid_$date")  # and more or less prefixes are possible
        c.add_section("camera2")
        c.set("camera2", "control_frame_width", "500")
        c.set("camera2", "server_command", "camera_server.py")
        c.set("camera2", "start_server", "1")
        c.set("camera2", "server_logfile", "/tmp/camera2.log")
        c.set("camera2", "server_runfile", "/tmp/camera2.pids")
        c.set("camera2", "ip", "localhost")
        c.set("camera2", "port", "15115")
        c.set("camera2", "server_max_start_time", "5.0")  # seconds
        c.set("camera2", "recv_bufsize", "4096")
        c.set("camera2", "update_img_delay", "6")  # milliseconds
        c.set("camera2", "guid", "-1")  # -1 to disable guid and some other settings; -2 to disable complete camera
        c.set("camera2", "vendor", "")
        c.set("camera2", "model", "")
        c.set("camera2", "mode", "FORMAT7_0")
        c.set("camera2", "color_coding", "Y8")
        c.set("camera2", "framerate", "30")
        c.set("camera2", "unit_position x", "2")
        c.set("camera2", "unit_position y", "2")
        c.set("camera2", "max x-image", "1032")
        c.set("camera2", "max y-image", "778")
        c.set("camera2", "x-image size", "default")
        c.set("camera2", "y-image size", "default")
        c.set("camera2", "x-image position", "default")
        c.set("camera2", "y-image position", "default")
        c.set("camera2", "brightness", "default")
        c.set("camera2", "trigger_delay", "default")
        c.set("camera2", "shutter", "default")
        c.set("camera2", "trigger", "default")
        c.set("camera2", "gain", "default")
        c.set("camera2", "gamma", "default")
        c.set("camera2", "exposure", "default")
        c.set("camera2", "camera_file_prefix1", "/tmp/cam_$guid_$date")
        c.set("camera2", "camera_file_prefix2", "")  # and more or less prefixes are possible
        c.add_section("camera3")
        c.set("camera3", "control_frame_width", "500")
        c.set("camera3", "server_command", "camera_server.py")
        c.set("camera3", "start_server", "1")
        c.set("camera3", "server_logfile", "/tmp/camera3.log")
        c.set("camera3", "server_runfile", "/tmp/camera3.pids")
        c.set("camera3", "ip", "localhost")
        c.set("camera3", "port", "15116")
        c.set("camera3", "server_max_start_time", "5.0")  # seconds
        c.set("camera3", "recv_bufsize", "4096")
        c.set("camera3", "update_img_delay", "6")  # milliseconds
        c.set("camera3", "guid", "-2")  # -1 to disable guid and some other settings; -2 to disable complete camera
        c.set("camera3", "vendor", "")
        c.set("camera3", "model", "")
        c.set("camera3", "mode", "FORMAT7_0")
        c.set("camera3", "color_coding", "Y8")
        c.set("camera3", "framerate", "30")
        c.set("camera3", "unit_position x", "2")
        c.set("camera3", "unit_position y", "2")
        c.set("camera3", "max x-image", "1032")
        c.set("camera3", "max y-image", "778")
        c.set("camera3", "x-image size", "default")
        c.set("camera3", "y-image size", "default")
        c.set("camera3", "x-image position", "default")
        c.set("camera3", "y-image position", "default")
        c.set("camera3", "brightness", "default")
        c.set("camera3", "trigger_delay", "default")
        c.set("camera3", "shutter", "default")
        c.set("camera3", "trigger", "default")
        c.set("camera3", "gain", "default")
        c.set("camera3", "gamma", "default")
        c.set("camera3", "exposure", "default")
        c.set("camera3", "camera_file_prefix1", "")  # and more or less prefixes are possible
        # acceleration sensor
        c.add_section("acceleration_sensors")
        c.set("acceleration_sensors", "n", "4")  # maximal number of acceleration sensors
        c.set("acceleration_sensors", "stop_acceleration_sensors_servers_on_exit", "0")
        c.add_section("acceleration_sensor1")
        c.set("acceleration_sensor1", "server_max_start_time", "5.0")  # seconds
        c.set("acceleration_sensor1", "server_command", "acceleration_sensor_server.py")
        c.set("acceleration_sensor1", "connect_server", "1")
        c.set("acceleration_sensor1", "start_server", "1")
        c.set("acceleration_sensor1", "server_logfile", "/tmp/acceleration_sensor1.log")
        c.set("acceleration_sensor1", "server_datalogfile", "/tmp/acceleration_sensor1.data")
        c.set("acceleration_sensor1", "datalogformat", "2")
        c.set("acceleration_sensor1", "server_runfile", "/tmp/acceleration_sensor1.pids")
        c.set("acceleration_sensor1", "ip", "localhost")
        c.set("acceleration_sensor1", "port", "15123")
        c.set("acceleration_sensor1", "server_max_start_time", "5.0")  # seconds
        c.set("acceleration_sensor1", "recv_bufsize", "4096")
        c.set("acceleration_sensor1", "update_extern_delay", "6")  # milliseconds
        c.set("acceleration_sensor1", "SerialNumber", "00000850")  # -1 to disable SerialNumber and use the first one found; -2 to disable complete sensor
        c.set("acceleration_sensor1", "bwgraphics", "0")
        c.set("acceleration_sensor1", "colorgraphics", "0")
        c.set("acceleration_sensor1", "diagramgraphics", "1")
        c.set("acceleration_sensor1", "maxg", "2.0")
        c.set("acceleration_sensor1", "sleep", "0.1")  # sec
        c.set("acceleration_sensor1", "shadowlength", "16")
        c.set("acceleration_sensor1", "diagramlength", "480")
        c.set("acceleration_sensor1", "resolution", "600")
        c.set("acceleration_sensor1", "update_display_delay", "100")  # ms
        # environment_sensor_5
        c.add_section("environment_sensor_5")
        c.set("environment_sensor_5", "command", "environment_sensor_5_logger.py")
        c.set("environment_sensor_5", "start_sensor", "0")
        c.set("environment_sensor_5", "stop_sensor_on_exit", "0")
        c.set("environment_sensor_5", "logfile", "/tmp/environment_sensor_5.log")
        c.set("environment_sensor_5", "datalogfile", "/tmp/environment_sensor_5.data")
        c.set("environment_sensor_5", "devicename", "/dev/ESFTGAB745")
        c.set("environment_sensor_5", "sleep", "6.0")
        c.set("environment_sensor_5", "baudrate", "9600")
        c.set("environment_sensor_5", "runfile", "/tmp/environment_sensor_5.pids")
        # gas system
        c.add_section("gas system")
        c.set("gas system", "membran_pump_status_controller", "dc")
        c.set("gas system", "membran_pump_status_port", "B")
        c.set("gas system", "membran_pump_status_channel", "6")
        c.set("gas system", "turbo_pump_1_status_controller", "mpc")
        c.set("gas system", "turbo_pump_1_status_port", "DO")
        c.set("gas system", "turbo_pump_1_status_channel", "2")
        c.set("gas system", "turbo_pump_1_rpm_controller", "mpc")
        c.set("gas system", "turbo_pump_1_rpm_port", "ADC")
        c.set("gas system", "turbo_pump_1_rpm_channel", "1")
        c.set("gas system", "turbo_pump_1_error_rotation_controller", "mpc")
        c.set("gas system", "turbo_pump_1_error_rotation_port", "DI")
        c.set("gas system", "turbo_pump_1_error_rotation_channel", "0")
        c.set("gas system", "turbo_pump_1_error_general_controller", "mpc")
        c.set("gas system", "turbo_pump_1_error_general_port", "DI")
        c.set("gas system", "turbo_pump_1_error_general_channel", "1")
        c.set("gas system", "turbo_pump_2_status_controller", "mpc")
        c.set("gas system", "turbo_pump_2_status_port", "DO")
        c.set("gas system", "turbo_pump_2_status_channel", "3")
        c.set("gas system", "turbo_pump_2_rpm_controller", "mpc")
        c.set("gas system", "turbo_pump_2_rpm_port", "ADC")
        c.set("gas system", "turbo_pump_2_rpm_channel", "2")
        c.set("gas system", "turbo_pump_2_error_rotation_controller", "mpc")
        c.set("gas system", "turbo_pump_2_error_rotation_port", "DI")
        c.set("gas system", "turbo_pump_2_error_rotation_channel", "2")
        c.set("gas system", "turbo_pump_2_error_general_controller", "mpc")
        c.set("gas system", "turbo_pump_2_error_general_port", "DI")
        c.set("gas system", "turbo_pump_2_error_general_channel", "3")
        c.set("gas system", "mass_flow_controller_status_controller", "mpc")
        c.set("gas system", "mass_flow_controller_status_port", "U15")
        c.set("gas system", "mass_flow_controller_status_channel", "-1")
        c.set("gas system", "mass_flow_controller_set_rate_controller", "mpc")
        c.set("gas system", "mass_flow_controller_set_rate_port", "DAC")
        c.set("gas system", "mass_flow_controller_set_rate_channel", "0")
        c.set("gas system", "mass_flow_controller_measure_rate_controller", "mpc")
        c.set("gas system", "mass_flow_controller_measure_rate_port", "ADC")
        c.set("gas system", "mass_flow_controller_measure_rate_channel", "0")
        # laser
        c.add_section("laser")
        c.set("laser", "laser_power_status_controller", "dc")
        c.set("laser", "laser_power_status_port", "A")
        c.set("laser", "laser_power_status_channel", "0")
        c.set("laser", "R", "0.5")  # Laser Current Measure resistor value (Ohm)
        c.set("laser", "I_offset", "0.5")  # Laser Power P = (I-I_offset) * I_scale
        c.set("laser", "I_scale", "0.5")  # Laser Power P = (I-I_offset) * I_scale (W/A)
        c.set("laser", "laser1_power_status_controller", "mpc")
        c.set("laser", "laser1_power_status_port", "DO")
        c.set("laser", "laser1_power_status_channel", "1")
        c.set("laser", "laser1_diode_voltage_controller", "mpc")
        c.set("laser", "laser1_diode_voltage_port", "DAC")
        c.set("laser", "laser1_diode_voltage_channel", "2")
        c.set("laser", "laser1_diode_current_controller", "mpc")
        c.set("laser", "laser1_diode_current_port", "ADC")
        c.set("laser", "laser1_diode_current_channel", "5")
        c.set("laser", "laser2_power_status_controller", "mpc")
        c.set("laser", "laser2_power_status_port", "DO")
        c.set("laser", "laser2_power_status_channel", "0")
        c.set("laser", "laser2_diode_voltage_controller", "mpc")
        c.set("laser", "laser2_diode_voltage_port", "DAC")
        c.set("laser", "laser2_diode_voltage_channel", "1")
        c.set("laser", "laser2_diode_current_controller", "mpc")
        c.set("laser", "laser2_diode_current_port", "ADC")
        c.set("laser", "laser2_diode_current_channel", "3")
        # dispenser
        c.add_section("dispensers")
        c.set("dispensers", "key_binding_dispenser1", "<KeyPress-F1>")
        c.set("dispensers", "key_binding_dispenser2", "<KeyPress-F2>")
        c.set("dispensers", "key_binding_dispenser3", "<KeyPress-F3>")
        c.set("dispensers", "key_binding_dispenser4", "-1")
        c.add_section("dispenser1")
        c.set("dispenser1", "controller", "dc")  # -1 sets not activ
        c.set("dispenser1", "port", "B")
        c.set("dispenser1", "channel", "0")
        c.set("dispenser1", "shakes", "1")
        c.set("dispenser1", "Toff", "50")  # ms
        c.set("dispenser1", "Ton", "25")  # ms
        c.add_section("dispenser2")
        c.set("dispenser2", "controller", "dc")  # -1 sets not activ
        c.set("dispenser2", "port", "B")
        c.set("dispenser2", "channel", "1")
        c.set("dispenser2", "shakes", "1")
        c.set("dispenser2", "Toff", "50")  # ms
        c.set("dispenser2", "Ton", "25")  # ms
        c.add_section("dispenser3")
        c.set("dispenser3", "controller", "dc")  # -1 sets not activ
        c.set("dispenser3", "port", "B")
        c.set("dispenser3", "channel", "2")
        c.set("dispenser3", "shakes", "1")
        c.set("dispenser3", "Toff", "50")  # ms
        c.set("dispenser3", "Ton", "25")  # ms
        c.add_section("dispenser4")
        c.set("dispenser4", "controller", "-1")  # -1 sets not activ
        c.set("dispenser4", "port", "B")
        c.set("dispenser4", "channel", "3")
        c.set("dispenser4", "shakes", "1")
        c.set("dispenser4", "Toff", "50")  # ms
        c.set("dispenser4", "Ton", "25")  # ms

    def write_default_config_file(self, file: str) -> None:
        c = configparser.SafeConfigParser()
        self.set_default(c)
        with Path(file).open("w") as configfile:
            c.write(configfile)
