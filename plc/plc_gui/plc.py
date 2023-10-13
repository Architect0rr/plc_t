#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013, 2017 Daniel Mohr
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
GUI for plc
"""

import os
import sys
import time
import logging
import threading
import subprocess
import configparser
from pathlib import Path
from typing import Dict, Any, List, NoReturn

import PIL.ImageTk  # type: ignore

import tkinter
import tkinter.messagebox
import tkinter.filedialog
from tkinter import ttk

from . import camera
from . import gas_system
from . import controller
from . import rf_generator
from . import read_config_file
from . import electrode_motion
from . import translation_stage
from . import acceleration_sensor
from . import diagnostic_particles
from .plcclientserverclass import scs_gui
from ..plc_tools import plclogclasses

# from .misc import except_notify


class PLC(tkinter.Frame):
    """
    class for the GUI for plc
    """

    @classmethod
    def main(cls, log: logging.Logger, system_conffile: Path, conffile: Path):
        # tkinter.NoDefaultRoot()
        root = tkinter.Tk()
        app = cls(root, log, system_conffile, conffile)
        # app.grid(sticky=tcs.NSEW)
        # root.grid_columnconfigure(0, weight=1)
        # root.grid_rowconfigure(0, weight=1)
        root.resizable(True, True)
        root.after(app.update_intervall, func=app.update)  # call update every ... milliseconds
        root.after(app.check_buttons_intervall, func=app.check_buttons)  # call update every ... milliseconds
        root.mainloop()
        app.exit()

    def __init__(self, root: tkinter.Tk, _log: logging.Logger, system_conffile: Path, conffile: Path) -> None:
        """
        GUI initialization
        """
        super().__init__(root)
        # set variables
        # set default values
        self.log = _log
        self.log.debug("Initializing GUI")
        self.conffile = conffile
        self.configs = read_config_file.read_config_file(
            system_wide_ini_file=system_conffile.as_posix(), user_ini_file=conffile.as_posix()
        )
        # Set up logging
        self.lh = plclogclasses.LabelLogHandler(n=self.configs.values.getint("gui", "debug_area_height"))
        self.lh.setLevel(logging.DEBUG)
        self.lh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S"))
        self.log.addHandler(self.lh)

        self.log.debug(f"Found {self.configs.number_of_cameras} cameras in config file")
        self.log.debug(f"Found {self.configs.number_of_acceleration_sensor} acceleration sensors in config file")
        # more variables
        self.update_intervall = int(self.configs.values.get("gui", "update_intervall"))  # milliseconds
        self.check_buttons_intervall = int(self.configs.values.get("gui", "check_buttons_intervall"))  # milliseconds
        self.padx = self.configs.values.get("gui", "padx")
        self.pady = self.configs.values.get("gui", "pady")
        # set other variables
        # self.args = args
        self.debug = 1  # self.args.debug

        # main code
        self.main_window = root  # tkinter.Tk()
        self.screenx = self.main_window.winfo_screenwidth()
        self.screeny = self.main_window.winfo_screenheight()
        # self.main_window.title(f"plc - PlasmaLabControl ({self.conffile.as_posix()})")
        self.main_window.title("plc - PlasmaLabControl (development 22261104)")

        # ########################
        # ####### M E N U ########
        # ########################

        self.menu = tkinter.Menu(self.main_window)
        # file menu
        self.filemenu = tkinter.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Read setpoints", command=self.read_setpoints)
        self.filemenu.add_command(label="Save default config", command=self.save_default_config)
        self.filemenu.add_command(label="Exit", command=self.exit_button)
        # Programs
        self.programmenu = tkinter.Menu(self.menu)
        self.menu.add_cascade(label="Programs", menu=self.programmenu)
        self.programmenu.add_command(label="camera_client.py", command=self.start_extern_program_camera_client)
        self.programmenu.add_command(
            label="digital_controller_client.py",
            command=self.start_extern_program_digital_controller_client,
        )
        self.programmenu.add_command(
            label="multi_purpose_controller_client.py",
            command=self.start_extern_program_multi_purpose_controller_client,
        )
        self.programmenu.add_command(label="debug_controller.py", command=self.start_extern_program_debug_controller)
        self.programmenu.add_separator()
        self.programmenu.add_command(label="plc_viewer.py", command=self.start_extern_program_plc_viewer)
        self.programmenu.add_command(label="rawmovieviewer.py", command=self.start_extern_program_rawmovieviewer)

        # debug
        self.debugmenu = tkinter.Menu(self.menu)
        self.menu.add_cascade(label="Debug", menu=self.debugmenu)
        self.debugmenu_status = tkinter.IntVar()
        self.debugmenu.add_checkbutton(
            label="debug infos on/off",
            command=self.switch_debug_infos_on_off,
            variable=self.debugmenu_status,
        )
        self.debugmenu_status.set(1 if self.debug == 1 else 0)

        # help menu
        self.helpmenu = tkinter.Menu(self.menu)
        self.menu.add_cascade(label="Help", menu=self.helpmenu)
        self.helpmenu.add_command(label="About...", command=self.about)

        self.main_window.config(menu=self.menu)
        # create toolbar
        self.toolbar = tkinter.Frame(self.main_window)
        self.toolbar.pack(expand=True, fill=tkinter.X)
        # create info area in toolbar
        self.info_area = tkinter.Frame(self.toolbar)
        self.info_area.pack(expand=True, fill=tkinter.X)
        self.info_area_load_val = tkinter.StringVar()
        self.info_area_load = tkinter.Label(
            self.info_area, textvariable=self.info_area_load_val, height=1, width=21, anchor="sw"
        )
        self.info_area_load_val.set("")
        self.info_area_load.pack(side=tkinter.RIGHT)
        # create acceleration sensor
        self.info_area_acceleration_sensor_vals = []
        self.info_area_acceleration_sensors = []
        for i in range(self.configs.number_of_acceleration_sensor):
            self.info_area_acceleration_sensor_vals += [tkinter.StringVar()]
            self.info_area_acceleration_sensors += [
                tkinter.Label(
                    self.info_area,
                    textvariable=self.info_area_acceleration_sensor_vals[i],
                    height=1,
                    width=21,
                    anchor="sw",
                )
            ]
            self.info_area_acceleration_sensor_vals[i].set("acc%d=(?.??,?.??,?.??)" % (i + 1))
            self.info_area_acceleration_sensors[i].pack(side=tkinter.RIGHT)

        # ########################
        # ####### T A B S ########
        # ########################

        # create tabs
        self.tabs = ttk.Notebook(self.main_window)
        self.maintab = tkinter.Frame(self.tabs)
        self.tabs.add(self.maintab, text="Main", sticky="NW")

        # create camera tabs
        self.camera_tabs = []
        self.camera_notebook_index = []

        index = 0
        for i in range(self.configs.number_of_cameras):
            index += 1
            self.camera_tabs += [tkinter.Frame(self.tabs)]
            self.camera_notebook_index += [index]
            self.tabs.add(self.camera_tabs[i], text="cam %d" % (i + 1), sticky="NW")

        # create acceleration sensor tabs
        self.acceleration_sensor_tabs = []
        self.acceleration_sensor_notebook_index = []
        for i in range(self.configs.number_of_acceleration_sensor):
            index += 1
            self.acceleration_sensor_tabs += [tkinter.Frame(self.tabs)]
            self.acceleration_sensor_notebook_index += [index]
            self.tabs.add(self.acceleration_sensor_tabs[i], text="acc. %d" % (i + 1), sticky="NW")
        #
        self.tabs.pack(expand=True, fill=tkinter.X)
        self.tabs.select(0)

        # ########################
        # ##### M A I N  TAB #####
        # ########################

        # ########################
        # ##### M A I N  TAB ##### : Cameras
        # ########################

        # create user_interface area
        self.user_interface = tkinter.Frame(self.maintab, relief="solid", borderwidth=1)
        self.user_interface.pack()
        self.master_paned_window = tkinter.PanedWindow(self.user_interface, orient=tkinter.HORIZONTAL)
        self.master_paned_window.pack()

        # create blocks with content
        # create block for camera
        self.cameras_window = tkinter.LabelFrame(self.user_interface, text="Cameras")
        # self.master_paned_window.add(self.cameras_window, width=7 + self.configs.values.getint("cameras", "width_in_main_tab"))
        self.master_paned_window.add(self.cameras_window)
        self.cameras_window_control = tkinter.Frame(self.cameras_window)
        self.cameras_window_control.pack()

        # cameras, record
        self.cameras_connect_button = tkinter.Button(
            self.cameras_window_control,
            text="connect",
            command=self.connect_cameras,
            padx=self.padx,
            pady=self.pady,
        )
        self.cameras_connect_button.grid(column=0, row=0)
        self.cameras_disconnect_button = tkinter.Button(
            self.cameras_window_control,
            text="disconnect",
            command=self.disconnect_cameras,
            padx=self.padx,
            pady=self.pady,
        )
        self.cameras_disconnect_button.grid(column=0, row=1)
        self.cameras_quit_button = tkinter.Button(
            self.cameras_window_control,
            text="quit cams",
            command=self.quit_cameras,
            padx=self.padx,
            pady=self.pady,
        )
        self.cameras_quit_button.grid(column=0, row=2)
        self.cameras_start_live_view_button = tkinter.Button(
            self.cameras_window_control,
            text="start view",
            command=self.start_live_view_cameras,
            padx=self.padx,
            pady=self.pady,
        )
        self.cameras_start_live_view_button.grid(column=0, row=3)
        self.cameras_stop_live_view_button = tkinter.Button(
            self.cameras_window_control,
            text="stop view",
            command=self.stop_live_view_cameras,
            padx=self.padx,
            pady=self.pady,
        )
        self.cameras_stop_live_view_button.grid(column=0, row=4)
        self.cameras_start_record_button = tkinter.Button(
            self.cameras_window_control,
            text="start record",
            command=self.start_record_cameras,
            padx=self.padx,
            pady=self.pady,
        )
        self.cameras_start_record_button.grid(column=0, row=5)
        self.cameras_stop_record_button = tkinter.Button(
            self.cameras_window_control,
            text="stop record",
            command=self.stop_record_cameras,
            padx=self.padx,
            pady=self.pady,
        )
        self.cameras_stop_record_button.grid(column=0, row=6)
        # camera pictures
        self.cameras_window_view = tkinter.Frame(self.cameras_window)
        self.cameras_window_view.pack()
        self.camera_picture_x = self.configs.values.getint("cameras", "width_in_main_tab")
        self.create_camera_movie_labels(self.cameras_window_view)
        # cameras
        self.cameras = []
        for i in range(self.configs.number_of_cameras):
            self.cameras += [
                camera.camera(
                    config=self.configs,
                    confsect="camera%d" % (i + 1),
                    pw=self.camera_tabs[i],
                    screenx=self.screenx,
                    screeny=self.screeny,
                    extern_img=self.cameras_imgs[i],
                    extern_x=self.camera_picture_x,
                    notebook=self.tabs,
                    notebookindex=self.camera_notebook_index[i],
                    notebookextern=0,
                )
            ]

        # ########################
        # ##### M A I N  TAB ##### : Acceleration sensors
        # ########################

        # create block for acceleration sensor
        self.acceleration_sensor: List[acceleration_sensor.acceleration_sensor] = []
        # for i in range(self.configs.number_of_acceleration_sensor):
        #     self.acceleration_sensor += [
        #         acceleration_sensor.acceleration_sensor(
        #             config=self.configs,
        #             confsect="acceleration_sensor%d" % (i + 1),
        #             pw=self.acceleration_sensor_tabs[i],
        #         )
        #     ]
        #     self.acceleration_sensor[i].extern_update_start(
        #         extern_stringvar=self.info_area_acceleration_sensor_vals[i],
        #         notebook=self.tabs,
        #         notebookindex=self.acceleration_sensor_notebook_index[i],
        #         notebookextern=0,
        #     )

        # ########################
        # ##### M A I N  TAB ##### : Control
        # ########################

        # create other blocks
        self.control_window = tkinter.Frame(self.user_interface, relief="solid", borderwidth=1)
        self.master_paned_window.add(self.control_window)

        self.control_window1 = tkinter.Frame(self.control_window, relief="solid", borderwidth=1)
        self.control_window1.pack()
        # create block for controller
        self.controller_window = tkinter.LabelFrame(self.control_window1, text="controller")
        self.controller_window.grid(column=0, row=0)

        # controller in a dict
        self.controller: Dict[str, controller.controller] = {}

        self.digital_controller_window = tkinter.LabelFrame(self.controller_window, text="digital", labelanchor="n")
        self.digital_controller_window.grid(column=0, row=0)
        self.digital_controller = controller.digital_controller(self.log.getChild("dc"), self.configs)
        self.controller["dc"] = self.digital_controller
        self.controller["dc"].set_default_values()
        scs_gui(self.digital_controller_window, self.digital_controller)

        self.multi_purpose_controller_window = tkinter.LabelFrame(
            self.controller_window, text="multi purpose", labelanchor="n"
        )
        self.multi_purpose_controller_window.grid(column=1, row=0)
        self.multi_purpose_controller = controller.multi_purpose_controller(self.log.getChild("mpc"), self.configs)
        self.controller["mpc"] = self.multi_purpose_controller
        self.controller["mpc"].set_default_values()
        scs_gui(self.multi_purpose_controller_window, self.multi_purpose_controller)

        # ----------------------------

        # electrode motion controller
        self.electrode_motion_controller_device = self.configs.values.get("electrode motion controller", "devicename")
        if self.electrode_motion_controller_device != "-1":
            self.electrode_motion_controller_window = tkinter.LabelFrame(
                self.controller_window, text="electrode motion", labelanchor="n"
            )
            self.electrode_motion_controller_window.grid(column=2, row=0)
            self.electrode_motion_controller = controller.electrode_motion_controller(
                config=self.configs,
                pw=self.electrode_motion_controller_window,
                debugprint=self.debugprint,
            )
            self.controller["emc"] = self.electrode_motion_controller
            self.controller["emc"].gui()
            self.controller["emc"].set_default_values()

        # translation stage controller
        self.translation_stage_device = self.configs.values.get("translation stage controller", "devicename")
        if self.translation_stage_device != "-1":
            self.translation_stage_controller_window = tkinter.LabelFrame(
                self.controller_window, text="translation stage", labelanchor="n"
            )
            self.translation_stage_controller_window.grid(column=3, row=0)
            self.translation_stage_controller = controller.translation_stage_controller(
                config=self.configs,
                pw=self.translation_stage_controller_window,
                debugprint=self.debugprint,
            )
            self.controller["tsc"] = self.translation_stage_controller
            self.controller["tsc"].gui()
            self.controller["tsc"].set_default_values()

        # create block for gas system
        self.gas_system_window = ttk.LabelFrame(self.control_window1, text="Gas System")
        self.gas_system_window.grid(column=1, row=0)
        self.gas_system = gas_system.gs(self.configs, self.log.getChild("GS"), self.controller)
        self.gs_gui = gas_system.gas_system(
            self.gas_system_window,
            self.gas_system,
            self.log.getChild("GS"),
        )

        # create block for RF-generator
        self.rf_generator_controller = controller.rf_generator_controller(
            config=self.configs, _log=self.log.getChild("rfgc")
        )
        self.controller["rfgc"] = self.rf_generator_controller
        self.rf_generator_window = tkinter.Frame(self.control_window, relief="solid")
        self.rf_generator_window.pack()
        self.rf_generator = rf_generator.rf_generator_gui(
            config=self.configs, pw=self.rf_generator_window, controller=self.controller, _log=self.log.getChild("rfgg")
        )

        # create block for diagnostic/particles
        self.diagnostic_particles_window = tkinter.LabelFrame(self.control_window, text="Diagnostics/Particles")
        self.diagnostic_particles_window.pack()
        self.diagnostic_particles = diagnostic_particles.diagnostic_particles(
            config=self.configs,
            pw=self.diagnostic_particles_window,
            debugprint=self.debugprint,
            controller=self.controller,
        )
        # create block for electrode motion
        if self.electrode_motion_controller_device != "-1":
            self.electrode_motion_window = ttk.LabelFrame(self.control_window, text="Electrode Motion")
            self.electrode_motion_window.pack()
            self.electrode_motion = electrode_motion.electrode_motion(
                config=self.configs,
                pw=self.electrode_motion_window,
                _log=self.log.getChild("emc"),
                controller=self.controller,
            )
        # create block for translation stage
        if self.translation_stage_device != "-1":
            self.translation_stage_window = ttk.LabelFrame(self.control_window, text="Translation Stage")
            self.translation_stage_window.pack()
            self.translation_stage = translation_stage.translation_stage(
                config=self.configs,
                pw=self.translation_stage_window,
                _log=self.log.getChild("tr_stage"),
                controller=self.controller,
            )

        # create debug area
        self.debugtext = tkinter.StringVar()
        self.create_debug_area()

        # setpoints
        self.setpoints_choose = None
        self.info_area_setpoints: Dict[str, Any] = dict()
        self.info_area_setpoints["frame"] = tkinter.Frame(self.info_area, relief="solid", borderwidth=1)
        # self.info_area_setpoints['frame'].grid(column=0,row=0)
        self.info_area_setpoints["frame"].pack(side=tkinter.LEFT)
        pw = self.info_area_setpoints["frame"]
        self.info_area_setpoints["previous setpoint"] = tkinter.Button(
            pw,
            text="previous",
            command=self.choose_previous_setpoint,
            padx=self.padx,
            pady=self.pady,
            state=tkinter.DISABLED,
        )
        self.info_area_setpoints["previous setpoint"].grid(column=0, row=0)
        self.info_area_setpoints["setpoint val"] = tkinter.StringVar()
        self.info_area_setpoints["setpoint"] = tkinter.Label(
            pw, textvariable=self.info_area_setpoints["setpoint val"], height=1, width=80
        )
        self.info_area_setpoints["setpoint"].grid(column=1, row=0)
        self.info_area_setpoints["setpoint val"].set("- none available -")
        self.info_area_setpoints["next setpoint"] = tkinter.Button(
            pw,
            text="next",
            command=self.choose_next_setpoint,
            padx=self.padx,
            pady=self.pady,
            state=tkinter.DISABLED,
        )
        self.info_area_setpoints["next setpoint"].grid(column=2, row=0)
        self.info_area_setpoints["set setpoint"] = tkinter.Button(
            pw,
            text="set",
            command=self.set_setpoints,
            padx=self.padx,
            pady=self.pady,
            state=tkinter.DISABLED,
        )
        self.info_area_setpoints["set setpoint"].grid(column=3, row=0)

        self.default_setpoints_file = self.configs.values.get("ini", "default_setpoints_file")
        if self.default_setpoints_file != "-1":
            self.log.debug("default_setpoints_file available")
            self.read_setpoints_file()
        else:
            self.log.debug("no default_setpoints_file available")

        # bind keys to functions
        self.main_window.bind(self.configs.values.get("cameras", "key_binding_view_all"), self.grabber_view)
        self.main_window.bind(self.configs.values.get("cameras", "key_binding_record_all"), self.grabber_record)
        if self.configs.values.get("dispensers", "key_binding_dispenser1") != "-1":
            self.main_window.bind(
                self.configs.values.get("dispensers", "key_binding_dispenser1"),
                self.shake_dispenser1,
            )
        if self.configs.values.get("dispensers", "key_binding_dispenser2") != "-1":
            self.main_window.bind(
                self.configs.values.get("dispensers", "key_binding_dispenser2"),
                self.shake_dispenser2,
            )
        if self.configs.values.get("dispensers", "key_binding_dispenser3") != "-1":
            self.main_window.bind(
                self.configs.values.get("dispensers", "key_binding_dispenser3"),
                self.shake_dispenser3,
            )
        if self.configs.values.get("dispensers", "key_binding_dispenser4") != "-1":
            self.main_window.bind(
                self.configs.values.get("dispensers", "key_binding_dispenser4"),
                self.shake_dispenser4,
            )
        if self.configs.values.get("ini", "key_binding_setpoints_previous") != "-1":
            self.main_window.bind(
                self.configs.values.get("ini", "key_binding_setpoints_previous"),
                self.choose_previous_setpoint,
            )
        if self.configs.values.get("ini", "key_binding_setpoints_next") != "-1":
            self.main_window.bind(
                self.configs.values.get("ini", "key_binding_setpoints_next"),
                self.choose_next_setpoint,
            )
        if self.configs.values.get("ini", "key_binding_setpoints_set") != "-1":
            self.main_window.bind(self.configs.values.get("ini", "key_binding_setpoints_set"), self.set_setpoints)
        # connect to digital controller on startup
        if self.configs.values.getboolean("dc", "connect_server"):
            self.controller["dc"].start_request()
        # connect to multi purpose controller on startup
        if self.configs.values.getboolean("mpc", "connect_server"):
            self.controller["mpc"].start_request()
        # connect to acceleration sensor controller on startup
        for i in range(self.configs.number_of_acceleration_sensor):
            if self.configs.values.getboolean("acceleration_sensor%d" % (i + 1), "connect_server"):
                self.acceleration_sensor[i].start_request()
        # start environment_sensor_5 on startup
        self.start_environment_sensor_5()

    def exit(self) -> NoReturn:
        self.log.debug("Exit called")
        try:
            self.stop_live_view_cameras()
        except Exception:
            pass
        if self.configs.values.getboolean("cameras", "stop_camera_servers_on_exit"):
            self.quit_cameras()
        else:
            self.disconnect_cameras()
        if self.configs.values.getboolean("acceleration_sensors", "stop_acceleration_sensors_servers_on_exit"):
            for i in range(self.configs.number_of_acceleration_sensor):
                try:
                    self.acceleration_sensor[i].quit_server_command()
                except Exception:
                    pass
        else:
            for i in range(self.configs.number_of_acceleration_sensor):
                try:
                    self.acceleration_sensor[i].stop()
                except Exception:
                    pass
        try:
            self.controller["dc"].stop_request()
        except Exception:
            pass
        try:
            self.controller["mpc"].stop_request()
        except Exception:
            pass
        if self.electrode_motion_controller_device != "-1":
            try:
                self.controller["emc"].stop_request()
            except Exception:
                pass
        if self.translation_stage_device != "-1":
            try:
                self.controller["tsc"].stop_request()
            except Exception:
                pass
        time.sleep(0.6)
        self.log.info("Good bye!")
        sys.exit(0)

    def start_environment_sensor_5(self):
        if self.configs.values.getboolean("environment_sensor_5", "start_sensor"):
            # start thread
            thread_id = threading.Thread(target=self._start_environment_sensor_5)
            thread_id.daemon = True  # exit thread when the main thread terminates
            thread_id.start()

    def _start_environment_sensor_5(self):
        if self.configs.values.getboolean("environment_sensor_5", "start_sensor"):
            c = [self.configs.values.get("environment_sensor_5", "command")]
            c += ["-logfile", self.configs.values.get("environment_sensor_5", "logfile")]
            c += ["-datalogfile", self.configs.values.get("environment_sensor_5", "datalogfile")]
            c += ["-devicename", self.configs.values.get("environment_sensor_5", "devicename")]
            c += ["-sleep", self.configs.values.get("environment_sensor_5", "sleep")]
            c += ["-baudrate", self.configs.values.get("environment_sensor_5", "baudrate")]
            c += ["-runfile", self.configs.values.get("environment_sensor_5", "runfile")]
            c += ["-debug", "0"]
            self.log.debug("start environment_sensor_5 '%s'" % (" ".join(c)))
            # prc_srv = subprocess.Popen(c)

    def create_debug_area(self):
        if int(self.debug) == 1:
            self.log.debug("create debug area")
            self.debug_infos = tkinter.Frame(self.main_window, relief="solid", borderwidth=1)
            self.debug = 1
            self.debug_infos_message = tkinter.Label(
                self.debug_infos,
                textvariable=self.debugtext,
                height=self.configs.values.getint("gui", "debug_area_height"),
                width=self.configs.values.getint("gui", "debug_area_width"),
                anchor="sw",
                justify=tkinter.LEFT,
            )
            # self.debugtext.set("")
            self.debug_infos_message.pack()
            self.debug_infos.pack()
            plclogclasses.LabelLogHandler.set_out(self.lh, self.debugtext)

    def debugprint(self, o: str):
        self.log.debug(o)

    def callback(self) -> None:
        self.log.warning("Called the default callback! no functionality.")

    def exit_button(self) -> None:
        self.log.debug("Exit button pressed, showing promt")
        if tkinter.messagebox.askyesno("Exit?", "Exit the Program?"):
            self.log.debug("Exiting...")
            self.log = self.log.getChild("exit")
            self.exit()

    def about(self) -> None:
        m = "About:\nplc - PlasmaLabControl\nAuthor: Daniel Mohr, mohr@mpe.mpg.de"
        self.log.info(m)
        tkinter.messagebox.showinfo("About", m)

    def save_default_config(self) -> None:
        f = tkinter.filedialog.asksaveasfilename(
            defaultextension=".cfg",
            initialdir="~",
            initialfile=".plc.cfg",
            title="Save default config to file",
        )
        try:
            self.configs.write_default_config_file(file=f)
            self.log.debug(f"Wrote config to '{f}'")
        except Exception:
            self.log.exception(f"Can not write config to '{f}'")

    # def start_extern_program_xxx(self, name: str, args: List[str]) -> None:
    #     self.log.getChild("exec").debug(f"Starting '{name}' in background")
    #     pid = subprocess.Popen(args).pid
    #     self.log.getChild("exec").debug(f"Started '{name}' with PID {pid}")

    def bexec(self, args: List[str]) -> None:
        self.log.getChild("bexec").debug(f"Starting '{args[0]}' in background")
        pid = subprocess.Popen(args).pid
        self.log.getChild("bexec").debug(f"Started '{args[0]}' with PID {pid}")

    # camera_client.py
    def start_extern_program_camera_client(self):
        c = self.configs.values.get("ini", "extern_program_camera_client")
        self.bexec([c])

    # digital_controller_client.py
    def start_extern_program_digital_controller_client(self):
        c = self.configs.values.get("ini", "extern_program_digital_controller_client")
        ip = self.configs.values.get("dc", "server_ip")
        port = self.configs.values.get("dc", "server_port")
        self.bexec([c, "-ip", ip, "-port", port])

    # multi_purpose_controller_client.py
    def start_extern_program_multi_purpose_controller_client(self):
        c = self.configs.values.get("ini", "extern_program_multi_purpose_controller_client")
        ip = self.configs.values.get("mpc", "server_ip")
        port = self.configs.values.get("mpc", "server_port")
        self.bexec([c, "-ip", ip, "-port", port])

    # debug_controller.py
    def start_extern_program_debug_controller(self):
        c = self.configs.values.get("ini", "extern_program_debug_controller")
        cc = [c, "-config", self.conffile.as_posix()]
        self.bexec(cc)

    # plc_viewer.py
    def start_extern_program_plc_viewer(self):
        c = self.configs.values.get("ini", "extern_program_plc_viewer")
        self.bexec([c])

    # rawmovieviewer.py
    def start_extern_program_rawmovieviewer(self):
        c = self.configs.values.get("ini", "extern_program_rawmovieviewer")
        self.bexec([c])

    def connect_cameras(self):
        for i in range(self.configs.number_of_cameras):
            self.cameras[i].open_connection_command()
            time.sleep(0.1)

    def disconnect_cameras(self):
        for i in range(self.configs.number_of_cameras):
            try:
                self.cameras[i].close_connection_command()
                time.sleep(0.05)
            except Exception:
                pass

    def quit_cameras(self):
        for i in range(self.configs.number_of_cameras):
            try:
                self.cameras[i].quit_server_command()
                time.sleep(0.05)
            except Exception:
                pass
        time.sleep(0.1)

    def start_live_view_cameras(self):
        for i in range(self.configs.number_of_cameras):
            t = threading.Thread(target=self.cameras[i].start_live_view)
            t.daemon = True
            t.start()

    def stop_live_view_cameras(self):
        for i in range(self.configs.number_of_cameras):
            self.cameras[i].stop_live_view()

    def start_record_cameras(self):
        for i in range(self.configs.number_of_cameras):
            self.cameras[i].start_recording()

    def stop_record_cameras(self):
        for i in range(self.configs.number_of_cameras):
            self.cameras[i].stop_recording()

    def create_camera_movie_labels(self, pw):
        self.cameras_imgs = []
        self.cameras_movie_labels = []
        for i in range(self.configs.number_of_cameras):
            self.cameras_imgs += [PIL.ImageTk.PhotoImage("L", (self.camera_picture_x, self.camera_picture_x))]
            self.cameras_movie_labels += [tkinter.Label(pw, image=self.cameras_imgs[i])]
            self.cameras_movie_labels[i].pack()

    def grabber_record(self, event=None):
        if event is not None:
            self.cameras_start_record_button.flash()
            self.cameras_start_live_view_button.flash()
        self.start_record_cameras()
        self.start_live_view_cameras()
        additionally_command_for_record_all = self.configs.values.get("cameras", "additionally_command_for_record_all")
        if additionally_command_for_record_all != "-1":
            self.log.debug(f"additionally command in background: {additionally_command_for_record_all}")
            os.system(f"{additionally_command_for_record_all} &")

    def grabber_view(self, event=None):
        if event is not None:
            self.cameras_stop_record_button.flash()
            self.cameras_start_live_view_button.flash()
        self.stop_record_cameras()
        self.start_live_view_cameras()
        additionally_command_for_view_all = self.configs.values.get("cameras", "additionally_command_for_view_all")
        if additionally_command_for_view_all != "-1":
            self.log.debug(f"Additionally command in background: {additionally_command_for_view_all}")
            os.system(f"{additionally_command_for_view_all} &")

    def shake_dispenser1(self, event=None):
        if event is not None:
            self.diagnostic_particles.shake_dispenser1()

    def shake_dispenser2(self, event=None):
        if event is not None:
            self.diagnostic_particles.shake_dispenser2()

    def shake_dispenser3(self, event=None):
        if event is not None:
            self.diagnostic_particles.shake_dispenser3()

    def shake_dispenser4(self, event=None):
        if event is not None:
            self.diagnostic_particles.shake_dispenser4()

    def sighandler(self, signum, frame):
        self.debugprint("signum = %d" % signum)
        # signal.alarm(1)

    def update(self):
        """update every dynamic read values"""
        self.gas_system.update()
        self.diagnostic_particles.update()
        # load
        (load1, load2, load3) = os.getloadavg()
        self.info_area_load_val.set("load=(%2.2f,%2.2f,%2.2f)" % (load1, load2, load3))
        # loop:
        self.main_window.after(self.update_intervall, func=self.update)  # call update every ... milliseconds

    def check_buttons(self):
        if self.electrode_motion_controller_device != "-1":
            self.electrode_motion_controller.check_buttons()
        if self.translation_stage_device != "-1":
            self.translation_stage_controller.check_buttons()
        # self.rf_generator_controller.check_buttons()
        # self.rf_generator.check_buttons()
        self.gas_system.check_buttons()
        # self.rf_generator.check_buttons()
        self.diagnostic_particles.check_buttons()
        if self.electrode_motion_controller_device != "-1":
            self.electrode_motion.check_buttons()
        if self.translation_stage_device != "-1":
            self.translation_stage.check_buttons()
        self.main_window.after(
            self.check_buttons_intervall, func=self.check_buttons
        )  # call update every ... milliseconds

    def switch_debug_infos_off(self):
        self.debugprint("debug infos off")
        self.debug = 0
        plclogclasses.LabelLogHandler.set_out(self.lh, None)
        # log.setLevel(logging.DEBUG)
        self.debug_infos.destroy()

    def switch_debug_infos_on(self):
        self.debugprint("debug infos on")
        self.debug = 1
        self.create_debug_area()
        # log.setLevel(logging.WARNING)

    def switch_debug_infos_on_off(self):
        self.debugprint("debug infos on/off")
        if self.debugmenu_status.get() == 0:
            self.switch_debug_infos_off()
        elif self.debugmenu_status.get() == 1:
            self.switch_debug_infos_on()

    def read_setpoints(self):
        self.log.debug("ask for file to read setpoints from")
        f = tkinter.filedialog.askopenfilename(
            defaultextension=".cfg", initialdir="~", title="read setpoints from file"
        )
        try:
            if len(f) > 0:
                self.default_setpoints_file = f
                self.read_setpoints_file()
        except Exception:
            pass

    def read_setpoints_file(self):
        # read setpoints file
        self.log.debug("read setpoints from file '%s'" % self.default_setpoints_file)
        self.setpoints = configparser.ConfigParser()
        self.setpoints.read(os.path.expanduser(self.default_setpoints_file))
        if len(self.setpoints.sections()) > 0:
            self.log.debug("found %d sections" % len(self.setpoints.sections()))
            self.choose_setpoint(i=0)
            self.load_setpoints()
            self.info_area_setpoints["previous setpoint"].configure(state=tkinter.NORMAL)
            self.info_area_setpoints["next setpoint"].configure(state=tkinter.NORMAL)
            self.info_area_setpoints["set setpoint"].configure(state=tkinter.NORMAL)

    def load_setpoints(self):
        if self.setpoints_choose is not None:
            i = self.setpoints_choose
            s = self.setpoints.sections()[i]
            self.log.debug("load setpoints %d: %s" % (i, s))
            if self.setpoints.has_option(s, "load_set") and self.setpoints.getboolean(s, "load_set"):
                self.set_setpoints()

    def set_setpoints(self, event=None):
        """set setpoints

        Author: Daniel Mohr
        Date: 2012-09-07
        """
        if self.setpoints_choose is not None:
            i = self.setpoints_choose
            s = self.setpoints.sections()[i]
            self.log.debug("set setpoints %d: %s" % (i, s))
            self.info_area_setpoints["set setpoint"].flash()
            if self.setpoints.has_option(s, "mass_flow_on_off"):
                if self.setpoints.getboolean(s, "mass_flow_on_off"):
                    self.gas_system.mass_flow_checkbutton.select()
                else:
                    self.gas_system.mass_flow_checkbutton.deselect()
                self.gas_system.mass_flow()
            if self.setpoints.has_option(s, "mass_flow"):
                self.gas_system.mass_flow_set_flow_rate_val.set(self.setpoints.get(s, "mass_flow"))
                self.gas_system.set_mass_flow_rate()
            # RF
            # setcurrents = False
            # setphases = False
            # for i in range(12):
            #     c = i % 4  # channel
            #     g = round((i - c) / 4)  # generator
            #     if self.rf_generator.generator[g].exists:
            #         if self.setpoints.has_option(s, "pwr_channel_%d" % (i + 1)):
            #             if self.setpoints.getboolean(s, "pwr_channel_%d" % (i + 1)):
            #                 self.rf_generator.generator[g].channel[c].onoff_status_checkbutton.select()
            #             else:
            #                 self.rf_generator.generator[g].channel[c].onoff_status_checkbutton.deselect()
            #             self.rf_generator.rf_channel_onoff_cmd()
            #         if self.setpoints.has_option(s, "current_channel_%d" % (i + 1)):
            #             setcurrents = True
            #             self.rf_generator.generator[g].channel[c].current_status.set(self.setpoints.getint(s, "current_channel_%d" % (i + 1)))
            #         if self.setpoints.has_option(s, "phase_channel_%d" % (i + 1)):
            #             setphases = True
            #             self.rf_generator.generator[g].channel[c].phase_status.set(self.setpoints.getint(s, "phase_channel_%d" % (i + 1)))
            #         if self.setpoints.has_option(s, "combined_channel_%d" % (i + 1)):
            #             if self.setpoints.getboolean(s, "combined_channel_%d" % (i + 1)):
            #                 self.rf_generator.generator[g].channel[c].choose_checkbutton.select()
            #             else:
            #                 self.rf_generator.generator[g].channel[c].choose_checkbutton.deselect()
            # if setcurrents:
            #     self.rf_generator.set_currents()
            # if setphases:
            #     self.rf_generator.set_phases()
            # if self.setpoints.has_option(s, "rf_on_off"):
            #     if self.setpoints.getboolean(s, "rf_on_off"):
            #         self.rf_generator.combined_change_button3_cmd()
            #     else:
            #         self.rf_generator.combined_change_button4_cmd()
            # if self.setpoints.has_option(s, "ignite_plasma"):
            #     if self.setpoints.getboolean(s, "ignite_plasma"):
            #         self.rf_generator.ignite_plasma()

    def choose_setpoint(self, i=0):
        self.setpoints_choose = i
        s = self.setpoints.sections()[i]
        self.log.debug("choose setpoints %d: %s" % (i, s))
        self.info_area_setpoints["setpoint val"].set(s)
        if self.setpoints.has_option(s, "load_set") and self.setpoints.getboolean(s, "load_set"):
            self.set_setpoints()

    def choose_previous_setpoint(self, event=None):
        i = self.setpoints_choose
        if i is not None:
            i = max(0, i - 1)
            if i != self.setpoints_choose:
                self.info_area_setpoints["previous setpoint"].flash()
                self.choose_setpoint(i=i)

    def choose_next_setpoint(self, event=None):
        i = self.setpoints_choose
        if i is not None:
            i = min((len(self.setpoints.sections()) - 1, i + 1))
            if i != self.setpoints_choose:
                self.info_area_setpoints["next setpoint"].flash()
                self.choose_setpoint(i=i)
