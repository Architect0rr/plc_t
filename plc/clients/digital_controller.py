#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-05-13, 2014-07-22

__digital_controller_client_date__ = "2014-07-22"
__digital_controller_client_version__ = __digital_controller_client_date__

import time
import socket
import logging
import tkinter
import argparse
import logging.handlers
from typing import Dict, Any

from plc.plc_tools import plc_socket_communication


class gui(plc_socket_communication.tools_for_socket_communication):
    def __init__(self, args: argparse.Namespace, log: logging.Logger) -> None:
        super().__init__()
        self.bufsize: int = 4096  # read/receive Bytes at once
        self.ip: str = args.ip
        self.port: int = args.port
        self.debug: int = args.debug
        self.log: logging.Logger = log
        self.setpoint: Dict[str, Any] = {
            "A": 8 * [None],
            "B": 8 * [None],
            "dispenser": {"n": None, "ton": None, "shake": False, "port": None, "channel": None, "toff": None},
            "C": 8 * [None],
            "D": 8 * [None],
        }
        self.actualvalue = {
            "A": 8 * [None],
            "B": 8 * [None],
            "dispenser": {"n": None, "ton": None, "shake": False, "port": None, "channel": None, "toff": None},
            "C": 8 * [None],
            "D": 8 * [None],
        }

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.main_window = tkinter.Tk()
        self.main_window.title("digital_controller_client.py (%s:%d)" % (self.ip, self.port))
        self.frame1 = tkinter.Frame(self.main_window)
        self.frame1.pack()
        self.frame2 = tkinter.Frame(self.main_window)
        self.frame2.pack()
        self.frame3 = tkinter.Frame(self.main_window)
        self.frame3.pack()
        # control buttons
        self.open_connection_button = tkinter.Button(
            self.frame1, command=self.open_connection_command, text="connect", state=tkinter.NORMAL
        )
        self.open_connection_button.pack(side=tkinter.LEFT)
        self.close_connection_button = tkinter.Button(
            self.frame1, command=self.close_connection_command, text="disconnect", state=tkinter.DISABLED
        )
        self.close_connection_button.pack(side=tkinter.LEFT)
        self.quit_server_button = tkinter.Button(
            self.frame1, command=self.quit_server_command, text="quit server", state=tkinter.DISABLED
        )
        self.quit_server_button.pack(side=tkinter.LEFT)
        self.trigger_out_var = tkinter.IntVar()
        self.trigger_out_var.set(1)
        self.trigger_out_checkbutton = tkinter.Checkbutton(self.frame1, text="trigger", variable=self.trigger_out_var)
        self.trigger_out_checkbutton.pack(side=tkinter.LEFT)
        self.timedelay_val = tkinter.IntVar()
        self.timedelay_val.set(0)
        self.timedelay_entry = tkinter.Entry(
            self.frame1, justify=tkinter.CENTER, textvariable=self.timedelay_val, width=4
        )
        self.timedelay_entry.pack(side=tkinter.LEFT)
        self.timedelay_button = tkinter.Button(
            self.frame1, command=self.set_timedelay, text="set timedelay", state=tkinter.DISABLED
        )
        self.timedelay_button.pack(side=tkinter.LEFT)
        self.get_version_button = tkinter.Button(
            self.frame1, command=self.get_version, text="get version", state=tkinter.DISABLED
        )
        self.get_version_button.pack(side=tkinter.LEFT)
        self.get_actualvalues_button = tkinter.Button(
            self.frame1, command=self.get_actualvalues, text="get actual values", state=tkinter.DISABLED
        )
        self.get_actualvalues_button.pack(side=tkinter.LEFT)
        # setvalues and actual values
        self.channel_setpoint_checkbutton = dict()
        self.channel_setpoint_checkbutton_var = dict()
        self.channel_actual_value_var = dict()
        self.channel_actual_value_label = dict()
        channel = 0
        col = 0
        r = 0
        for p in ["A", "B", "C", "D"]:
            for c in range(8):
                self.channel_setpoint_checkbutton_var[channel] = tkinter.IntVar()
                self.channel_setpoint_checkbutton[channel] = tkinter.Checkbutton(
                    self.frame2,
                    command=self.button_changed,
                    text=f"{p} {c}",
                    variable=self.channel_setpoint_checkbutton_var[channel],
                )
                self.channel_setpoint_checkbutton[channel].grid(column=col, row=r)
                self.channel_actual_value_var[channel] = tkinter.StringVar()
                self.channel_actual_value_var[channel].set("?")
                self.channel_actual_value_label[channel] = tkinter.Label(
                    self.frame2, textvariable=self.channel_actual_value_var[channel], width=6, justify=tkinter.CENTER
                )
                self.channel_actual_value_label[channel].grid(column=col + 1, row=r)
                r += 1
                channel += 1
            col += 2
            r = 0
        # dispenser
        self.dispenser: Dict[str, Any] = {}
        self.dispenser["label"] = tkinter.Label(self.frame3, text="dispenser:")
        self.dispenser["label"].pack(side=tkinter.LEFT)
        self.dispenser["n val"] = tkinter.IntVar()
        self.dispenser["n entry"] = tkinter.Entry(
            self.frame3, justify=tkinter.CENTER, textvariable=self.dispenser["n val"], width=3
        )
        self.dispenser["n entry"].pack(side=tkinter.LEFT)
        self.dispenser["n label"] = tkinter.Label(self.frame3, text="shakes.")
        self.dispenser["n label"].pack(side=tkinter.LEFT)
        self.dispenser["ton label"] = tkinter.Label(self.frame3, text=" T_on:")
        self.dispenser["ton label"].pack(side=tkinter.LEFT)
        self.dispenser["ton val"] = tkinter.IntVar()
        self.dispenser["ton entry"] = tkinter.Entry(
            self.frame3, justify=tkinter.CENTER, textvariable=self.dispenser["ton val"], width=4
        )
        self.dispenser["ton entry"].pack(side=tkinter.LEFT)
        self.dispenser["ton label unit"] = tkinter.Label(self.frame3, text="ms.")
        self.dispenser["ton label unit"].pack(side=tkinter.LEFT)

        self.dispenser["toff label"] = tkinter.Label(self.frame3, text=" T_off:")
        self.dispenser["toff label"].pack(side=tkinter.LEFT)
        self.dispenser["toff val"] = tkinter.IntVar()
        self.dispenser["toff entry"] = tkinter.Entry(
            self.frame3, justify=tkinter.CENTER, textvariable=self.dispenser["toff val"], width=4
        )
        self.dispenser["toff entry"].pack(side=tkinter.LEFT)
        self.dispenser["toff label unit"] = tkinter.Label(self.frame3, text="ms.")
        self.dispenser["toff label unit"].pack(side=tkinter.LEFT)
        self.dispenser["port val"] = tkinter.StringVar()
        self.dispenser["port label"] = tkinter.Label(self.frame3, text=" port:")
        self.dispenser["port label"].pack(side=tkinter.LEFT)
        self.dispenser["port entry"] = tkinter.Entry(
            self.frame3, justify=tkinter.CENTER, textvariable=self.dispenser["port val"], width=2
        )
        self.dispenser["port entry"].pack(side=tkinter.LEFT)
        self.dispenser["channel val"] = tkinter.IntVar()
        self.dispenser["channel label"] = tkinter.Label(self.frame3, text=" channel:")
        self.dispenser["channel label"].pack(side=tkinter.LEFT)
        self.dispenser["channel entry"] = tkinter.Entry(
            self.frame3, justify=tkinter.CENTER, textvariable=self.dispenser["channel val"], width=2
        )
        self.dispenser["channel entry"].pack(side=tkinter.LEFT)
        self.dispenser["shake button"] = tkinter.Button(self.frame3, command=self.shake_dispenser, text="do the shake")
        self.dispenser["shake button"].pack(side=tkinter.LEFT)
        self.dispenser["n val"].set(-1)
        self.dispenser["ton val"].set(40)
        self.dispenser["toff val"].set(255)
        self.dispenser["port val"].set("")
        self.dispenser["channel val"].set(-1)

    def start(self):
        self.main_window.mainloop()
        self.quit()

    def quit(self):
        try:
            self.log.info("shutdown and close connection")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.connected = False
        except Exception:
            pass
        try:
            self.main_window.destroy()
        except Exception:
            pass

    def get_actualvalues(self):
        if self.connected:
            self.log.debug("get actualvalues from the server")
            # self.socket.sendall("getact")
            self.send_data_to_socket(self.socket, b"getact")
            self.actualvalue = self.receive_data_from_socket(self.socket, self.bufsize)
            channel = 0
            for p in ["A", "B", "C", "D"]:
                for c in range(8):
                    self.channel_actual_value_var[channel].set("%s" % self.actualvalue[p][c])
                    if self.actualvalue[p][c]:
                        self.channel_setpoint_checkbutton[channel].select()
                    else:
                        self.channel_setpoint_checkbutton[channel].deselect()
                    channel += 1
            if self.actualvalue["dispenser"]["n"] is not None:
                self.dispenser["n val"].set(self.actualvalue["dispenser"]["n"])
            if self.actualvalue["dispenser"]["ton"] is not None:
                self.dispenser["ton val"].set(int(round(self.actualvalue["dispenser"]["ton"] * 1000.0)))
            if self.actualvalue["dispenser"]["toff"] is not None:
                self.dispenser["toff val"].set(int(round(self.actualvalue["dispenser"]["toff"] * 1000.0)))
            if self.actualvalue["dispenser"]["port"] is not None:
                self.dispenser["port val"].set(self.actualvalue["dispenser"]["port"])
            if self.actualvalue["dispenser"]["channel"] is not None:
                self.dispenser["channel val"].set(self.actualvalue["dispenser"]["channel"])

    def get_version(self):
        if self.connected:
            # self.socket.sendall("version")
            self.send_data_to_socket(self.socket, b"version")
            v = self.socket.recv(self.bufsize)
            self.log.info("server-version: %s" % v)

    def set_timedelay(self):
        if self.connected:
            v = min(max(1, self.timedelay_val.get()), 999)
            self.timedelay_val.set(v)
            self.log.debug("set timedelay of the server to %03d ms" % v)
            # self.socket.sendall("timedelay%03d" % v)
            ms = "timedelay%03d" % v
            self.send_data_to_socket(self.socket, ms.encode("urf-8"))

    def shake_dispenser(self):
        self.setpoint["dispenser"]["shake"] = True
        self.button_changed()
        self.setpoint["dispenser"]["shake"] = False

    def button_changed(self):
        channel = 0
        for p in ["A", "B", "C", "D"]:
            for c in range(8):
                if self.channel_setpoint_checkbutton_var[channel].get() == 1:
                    self.setpoint[p][c] = True
                elif self.channel_setpoint_checkbutton_var[channel].get() == 0:
                    self.setpoint[p][c] = False
                self.channel_actual_value_var[channel].set("%s" % self.actualvalue[p][c])
                channel += 1
        if self.dispenser["n val"].get() != -1:
            self.setpoint["dispenser"]["n"] = self.dispenser["n val"].get()
        if self.dispenser["ton val"].get() != -1:
            self.setpoint["dispenser"]["ton"] = self.dispenser["ton val"].get() / 1000.0
        if self.dispenser["toff val"].get() != -1:
            self.setpoint["dispenser"]["toff"] = self.dispenser["toff val"].get() / 1000.0
        if self.dispenser["port val"].get() != "":
            self.setpoint["dispenser"]["port"] = self.dispenser["port val"].get()
        if self.dispenser["channel val"].get() != -1:
            self.setpoint["dispenser"]["channel"] = self.dispenser["channel val"].get()
        if self.connected:
            self.log.debug("send data to %s:%d" % (self.ip, self.port))
            v = "p %s" % self.create_send_format(self.setpoint)
            if self.trigger_out_var.get() == 1:
                v = "%s!w2d" % v
            self.send_data_to_socket(self.socket, v.encode("utf-8"))
        self.main_window.after(100, func=self.get_actualvalues)  # call after 100 milliseconds

    def open_connection_command(self):
        self.log.debug("connect to %s:%d" % (self.ip, self.port))
        try:
            self.socket.connect((self.ip, self.port))
            self.connected = True
            self.open_connection_button.configure(state=tkinter.DISABLED)
            self.close_connection_button.configure(state=tkinter.NORMAL)
            self.quit_server_button.configure(state=tkinter.NORMAL)
            self.timedelay_button.configure(state=tkinter.NORMAL)
            self.get_version_button.configure(state=tkinter.NORMAL)
            self.get_actualvalues_button.configure(state=tkinter.NORMAL)
            self.log.debug("connected")
        except Exception:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.log.warning("cannot connect to %s:%d" % (self.ip, self.port))

    def close_connection_command(self):
        self.log.debug("disconnect to %s:%d" % (self.ip, self.port))
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.open_connection_button.configure(state=tkinter.NORMAL)
        self.close_connection_button.configure(state=tkinter.DISABLED)
        self.quit_server_button.configure(state=tkinter.DISABLED)
        self.timedelay_button.configure(state=tkinter.DISABLED)
        self.get_version_button.configure(state=tkinter.DISABLED)
        self.get_actualvalues_button.configure(state=tkinter.DISABLED)

    def quit_server_command(self):
        if self.connected:
            self.log.info("quit server and disconnect")
            # self.socket.sendall("quit")
            self.send_data_to_socket(self.socket, b"quit")
            self.close_connection_command()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="digital_controller_client is a client to speak with the socket server digital_controller_server.py to control the digital controller on an serial interface.",
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s"
        % (__digital_controller_client_date__, help),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-ip",
        nargs=1,
        default="localhost",
        type=str,
        required=False,
        dest="ip",
        help="Set the IP/host n. default: localhost",
        metavar="n",
    )
    parser.add_argument(
        "-port",
        nargs=1,
        default=15112,
        type=int,
        required=False,
        dest="port",
        help="Set the port p. default: 15112",
        metavar="p",
    )
    parser.add_argument(
        "-debug",
        nargs=1,
        default=0,
        type=int,
        required=False,
        dest="debug",
        help="Set debug level. 0 no debug info (default); 1 debug to STDOUT.",
        metavar="debug_level",
    )
    args = parser.parse_args()
    if not isinstance(args.ip, str):
        args.ip = args.ip[0]
    if not isinstance(args.port, int):
        args.port = args.port[0]
    if not isinstance(args.debug, int):
        args.debug = args.debug[0]
    # logging
    log = logging.getLogger("dcc")
    log.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG)  # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO)  # logging.WARNING = 30
    ch.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S"))
    # add the handlers to log
    log.addHandler(ch)
    log.info(
        "start logging in digital_controller_client: %s"
        % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime())
    )
    g = gui(args, log)
    g.start()


if __name__ == "__main__":
    main()
