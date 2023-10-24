#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-05-13, 2014-07-22

__multi_purpose_controller_client_date__ = "2014-07-22"
__multi_purpose_controller_client_version__ = __multi_purpose_controller_client_date__

import time
import socket
import logging
import argparse
import threading
import tkinter as tk
import logging.handlers

from ..plc_tools.plc_socket_communication import socket_communication


class gui(socket_communication):
    def __init__(self, args, log):
        self.send_data_to_socket_lock = threading.Lock()
        self.bufsize = 4096  # read/receive Bytes at once
        self.ip = args.ip
        self.port = args.port
        self.debug = args.debug
        self.log = log
        self.actualvalue = {
            "DO": 4 * [None],
            "R": 2 * [None],
            "U05": None,
            "U15": None,
            "U24": None,
            "DAC": 4 * [0.0],
            "DI": 4 * [None],
            "ADC": 8 * [0],
        }
        self.setpoint = {"DO": 4 * [None], "R": 2 * [None], "U05": None, "U15": None, "U24": None, "DAC": 4 * [0.0]}
        self.socket = None
        self.main_window = tk.Tk()
        self.main_window.title("multi_purpose_controller_client.py (%s:%d)" % (self.ip, self.port))
        self.frame1 = tk.Frame(self.main_window)
        self.frame1.pack()
        self.frame2 = tk.Frame(self.main_window)
        self.frame2.pack()
        # control buttons
        self.open_connection_button = tk.Button(
            self.frame1, command=self.open_connection_command, text="connect", state=tk.NORMAL
        )
        self.open_connection_button.pack(side=tk.LEFT)
        self.close_connection_button = tk.Button(
            self.frame1, command=self.close_connection_command, text="disconnect", state=tk.DISABLED
        )
        self.close_connection_button.pack(side=tk.LEFT)
        self.quit_server_button = tk.Button(
            self.frame1, command=self.quit_server_command, text="quit server", state=tk.DISABLED
        )
        self.quit_server_button.pack(side=tk.LEFT)
        self.trigger_out_var = tk.IntVar()
        self.trigger_out_var.set(1)
        self.trigger_out_checkbutton = tk.Checkbutton(self.frame1, text="trigger", variable=self.trigger_out_var)
        self.trigger_out_checkbutton.pack(side=tk.LEFT)
        self.timedelay_val = tk.IntVar()
        self.timedelay_val.set("?")
        self.timedelay_entry = tk.Entry(self.frame1, justify=tk.CENTER, textvariable=self.timedelay_val, width=4)
        self.timedelay_entry.pack(side=tk.LEFT)
        self.timedelay_button = tk.Button(
            self.frame1, command=self.set_timedelay, text="set timedelay", state=tk.DISABLED
        )
        self.timedelay_button.pack(side=tk.LEFT)
        self.get_version_button = tk.Button(
            self.frame1, command=self.get_version, text="get version", state=tk.DISABLED
        )
        self.get_version_button.pack(side=tk.LEFT)
        self.get_actualvalues_button = tk.Button(
            self.frame1, command=self.get_actualvalues, text="get actual values", state=tk.DISABLED
        )
        self.get_actualvalues_button.pack(side=tk.LEFT)
        # setvalues and actual values
        self.channel_setpoint_checkbutton = dict()
        self.channel_setpoint_checkbutton_var = dict()
        self.channel_actual_value_var = dict()
        self.channel_actual_value_label = dict()
        channel = 0
        col = 0
        r = 0
        for p in ["DO", "R"]:
            for c in range(len(self.actualvalue[p])):
                self.channel_setpoint_checkbutton_var[channel] = tk.IntVar()
                self.channel_setpoint_checkbutton[channel] = tk.Checkbutton(
                    self.frame2,
                    command=self.button_changed,
                    text="%s %d" % (p, c),
                    variable=self.channel_setpoint_checkbutton_var[channel],
                )
                self.channel_setpoint_checkbutton[channel].grid(column=col, row=r)
                self.channel_actual_value_var[channel] = tk.StringVar()
                self.channel_actual_value_var[channel].set("?")
                self.channel_actual_value_label[channel] = tk.Label(
                    self.frame2, textvariable=self.channel_actual_value_var[channel], width=6, justify=tk.CENTER
                )
                self.channel_actual_value_label[channel].grid(column=col + 1, row=r)
                r += 1
                channel += 1
            col += 2
            r = 0
        for p in ["U05", "U15", "U24"]:
            self.channel_setpoint_checkbutton_var[channel] = tk.IntVar()
            self.channel_setpoint_checkbutton[channel] = tk.Checkbutton(
                self.frame2,
                command=self.button_changed,
                text="%s" % (p),
                variable=self.channel_setpoint_checkbutton_var[channel],
            )
            self.channel_setpoint_checkbutton[channel].grid(column=col, row=r)
            self.channel_actual_value_var[channel] = tk.StringVar()
            self.channel_actual_value_var[channel].set("?")
            self.channel_actual_value_label[channel] = tk.Label(
                self.frame2, textvariable=self.channel_actual_value_var[channel], width=6, justify=tk.CENTER
            )
            self.channel_actual_value_label[channel].grid(column=col + 1, row=r)
            r += 1
            channel += 1
        col += 2
        r = 0
        for p in ["DAC"]:
            for c in range(len(self.actualvalue[p])):
                self.channel_setpoint_checkbutton_var[channel] = tk.DoubleVar()
                self.channel_setpoint_checkbutton[channel] = tk.Entry(
                    self.frame2, textvariable=self.channel_setpoint_checkbutton_var[channel], width=7
                )
                self.channel_setpoint_checkbutton[channel].grid(column=col, row=r)
                self.channel_actual_value_var[channel] = tk.StringVar()
                self.channel_actual_value_var[channel].set("?")
                self.channel_actual_value_label[channel] = tk.Label(
                    self.frame2, textvariable=self.channel_actual_value_var[channel], width=9, justify=tk.CENTER
                )
                self.channel_actual_value_label[channel].grid(column=col + 1, row=r)
                r += 1
                channel += 1
        self.set_button = tk.Button(self.frame2, command=self.button_changed, text="set", state=tk.NORMAL)
        self.set_button.grid(column=col, row=r, rowspan=2)
        col += 2
        r = 0
        for p in ["DI"]:
            for c in range(len(self.actualvalue[p])):
                self.channel_setpoint_checkbutton[channel] = tk.Label(self.frame2, text=" %s %d:" % (p, c))
                self.channel_setpoint_checkbutton[channel].grid(column=col, row=r)
                self.channel_actual_value_var[channel] = tk.StringVar()
                self.channel_actual_value_var[channel].set("?")
                self.channel_actual_value_label[channel] = tk.Label(
                    self.frame2, textvariable=self.channel_actual_value_var[channel], width=6, justify=tk.CENTER
                )
                self.channel_actual_value_label[channel].grid(column=col + 1, row=r)
                r += 1
                channel += 1
        col += 2
        r = 0
        for p in ["ADC"]:
            for c in range(len(self.actualvalue[p])):
                self.channel_setpoint_checkbutton[channel] = tk.Label(self.frame2, text=" %s %d:" % (p, c))
                self.channel_setpoint_checkbutton[channel].grid(column=col, row=r)
                self.channel_actual_value_var[channel] = tk.StringVar()
                self.channel_actual_value_var[channel].set("?")
                self.channel_actual_value_label[channel] = tk.Label(
                    self.frame2, textvariable=self.channel_actual_value_var[channel], width=9, justify=tk.CENTER
                )
                self.channel_actual_value_label[channel].grid(column=col + 1, row=r)
                r += 1
                channel += 1

    def start(self):
        self.main_window.mainloop()
        self.quit()

    def quit(self):
        try:
            self.log.info("shutdown and close connection")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass
        try:
            self.main_window.destroy()
        except:
            pass

    def get_actualvalues(self):
        if self.socket != None:
            self.log.debug("get actualvalues form the server")
            # self.socket.sendall("getact")
            self.send_data_to_socket(self.socket, "getact")
            self.actualvalue = self.receive_data_from_socket(self.socket, self.bufsize)
            channel = 0
            for p in ["DO", "R"]:
                for c in range(len(self.actualvalue[p])):
                    self.channel_actual_value_var[channel].set("%s" % self.actualvalue[p][c])
                    if self.actualvalue[p][c]:
                        self.channel_setpoint_checkbutton[channel].select()
                    else:
                        self.channel_setpoint_checkbutton[channel].deselect()
                    channel += 1
            for p in ["U05", "U15", "U24"]:
                self.channel_actual_value_var[channel].set("%s" % self.actualvalue[p])
                if self.actualvalue[p]:
                    self.channel_setpoint_checkbutton[channel].select()
                else:
                    self.channel_setpoint_checkbutton[channel].deselect()
                channel += 1
            for p in ["DAC"]:
                for c in range(len(self.actualvalue[p])):
                    self.channel_actual_value_var[channel].set("%+ 2.3f V" % self.actualvalue[p][c])
                    channel += 1
            for p in ["DI"]:
                for c in range(len(self.actualvalue[p])):
                    self.channel_actual_value_var[channel].set("%s" % self.actualvalue[p][c])
                    channel += 1
            for p in ["ADC"]:
                for c in range(len(self.actualvalue[p])):
                    self.channel_actual_value_var[channel].set("%+ 2.3f V" % self.actualvalue[p][c])
                    channel += 1

    def get_version(self):
        if self.socket != None:
            # self.socket.sendall("version")
            self.send_data_to_socket(self.socket, "version")
            v = self.socket.recv(self.bufsize)
            self.log.info("server-version: %s" % v)

    def set_timedelay(self):
        if self.socket != None:
            v = min(max(1, self.timedelay_val.get()), 999)
            self.timedelay_val.set(v)
            self.log.debug("set timedelay of the server to %03d ms" % v)
            # self.socket.sendall("timedelay%03d" % v)
            self.send_data_to_socket(self.socket, "timedelay%03d" % v)

    def button_changed(self):
        channel = 0
        for p in ["DO", "R"]:
            for c in range(len(self.actualvalue[p])):
                if self.channel_setpoint_checkbutton_var[channel].get() == 1:
                    self.setpoint[p][c] = True
                elif self.channel_setpoint_checkbutton_var[channel].get() == 0:
                    self.setpoint[p][c] = False
                self.channel_actual_value_var[channel].set("%s" % self.actualvalue[p][c])
                channel += 1
        for p in ["U05", "U15", "U24"]:
            if self.channel_setpoint_checkbutton_var[channel].get() == 1:
                self.setpoint[p] = True
            elif self.channel_setpoint_checkbutton_var[channel].get() == 0:
                self.setpoint[p] = False
            self.channel_actual_value_var[channel].set("%s" % self.actualvalue[p])
            channel += 1
        for p in ["DAC"]:
            for c in range(len(self.actualvalue[p])):
                self.setpoint[p][c] = self.channel_setpoint_checkbutton_var[channel].get()
                if self.setpoint[p][c] < -10.0:
                    self.setpoint[p][c] = -10.0
                    self.channel_setpoint_checkbutton_var[channel].set(-10.0)
                elif self.setpoint[p][c] > +10.0:
                    self.setpoint[p][c] = +10.0
                    self.channel_setpoint_checkbutton_var[channel].set(+10.0)
                self.channel_actual_value_var[channel].set("%+ 2.3f V" % self.actualvalue[p][c])
                channel += 1
        if self.socket != None:
            self.log.debug("send data to %s:%d" % (self.ip, self.port))
            v = "p %s" % self.create_send_format(self.setpoint)
            if self.trigger_out_var.get() == 1:
                v = "%s!w2d" % v
            self.send_data_to_socket(self.socket, v)
        self.main_window.after(100, func=self.get_actualvalues)  # call after 100 milliseconds

    def open_connection_command(self):
        self.log.debug("connect to %s:%d" % (self.ip, self.port))
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            self.open_connection_button.configure(state=tk.DISABLED)
            self.close_connection_button.configure(state=tk.NORMAL)
            self.quit_server_button.configure(state=tk.NORMAL)
            self.timedelay_button.configure(state=tk.NORMAL)
            self.get_version_button.configure(state=tk.NORMAL)
            self.get_actualvalues_button.configure(state=tk.NORMAL)
            self.set_button.configure(state=tk.NORMAL)
            self.log.debug("connected")
        except:
            self.socket = None
            self.log.warning("cannot connect to %s:%d" % (self.ip, self.port))

    def close_connection_command(self):
        self.log.debug("disconnect to %s:%d" % (self.ip, self.port))
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.socket = None
        self.open_connection_button.configure(state=tk.NORMAL)
        self.close_connection_button.configure(state=tk.DISABLED)
        self.quit_server_button.configure(state=tk.DISABLED)
        self.timedelay_button.configure(state=tk.DISABLED)
        self.get_version_button.configure(state=tk.DISABLED)
        self.get_actualvalues_button.configure(state=tk.DISABLED)
        self.set_button.configure(state=tk.DISABLED)

    def quit_server_command(self):
        if self.socket != None:
            self.log.info("quit server and disconnect")
            # self.socket.sendall("quit")
            self.send_data_to_socket(self.socket, "quit")
            self.close_connection_command()


def main():
    parser = argparse.ArgumentParser(
        description="multi_purpose_controller_client is a client to speak with the socket server multi_purpose_controller_server.py to control the multi purpose controller on an serial interface.",
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s"
        % (__multi_purpose_controller_client_date__, help),
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
        default=15113,
        type=int,
        required=False,
        dest="port",
        help="Set the port p. default: 15113",
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
    ch.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    # add the handlers to log
    log.addHandler(ch)
    log.info(
        "start logging in multi_purpose_controller_client: %s"
        % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime())
    )
    g = gui(args, log)
    g.start()


if __name__ == "__main__":
    main()
