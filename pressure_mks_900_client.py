#!/usr/bin/python -O
# Author: Richard Schlitz, Daniel Mohr
# Date: 2013-02-04, 2014-07-22

__pressure900_client_date__ = "2014-07-22"
__pressure900_client_version__ = __pressure900_client_date__

import argparse
import pickle
import logging
import logging.handlers
import re
import socket
import time
import tkinter

class gui():
    def __init__(self,args,log):
        self.ip = args.ip
        self.port = args.port
        self.debug = args.debug
        self.log = log
        self.actualvalue = {'PR': "",'U':"",'GC':"",'GT':""}
        self.setpoint = {'PR': "",'U':"",'GC':"",'GT':""}
        self.socket = None
        self.main_window = tkinter.Tk()
        self.main_window.title("pressure900_client.py (%s:%d)" % (self.ip,self.port))
        self.frame1 = tkinter.Frame(self.main_window)
        self.frame1.pack()
        self.frame2 = tkinter.Frame(self.main_window)
        self.frame2.pack()
        self.frame3 = tkinter.Frame(self.main_window)
        self.frame3.pack()
        # control buttons
        self.open_connection_button = tkinter.Button(self.frame1,command=self.open_connection_command,text="connect",state=tkinter.NORMAL)
        self.open_connection_button.pack(side=tkinter.LEFT)
        self.close_connection_button = tkinter.Button(self.frame1,command=self.close_connection_command,text="disconnect",state=tkinter.DISABLED)
        self.close_connection_button.pack(side=tkinter.LEFT)
        self.quit_server_button = tkinter.Button(self.frame1,command=self.quit_server_command,text="quit server",state=tkinter.DISABLED)
        self.quit_server_button.pack(side=tkinter.LEFT)
        self.timedelay_val = tkinter.IntVar()
        self.timedelay_val.set("?")
        self.timedelay_entry = tkinter.Entry(self.frame1,justify=tkinter.CENTER,textvariable=self.timedelay_val,width=4)
        self.timedelay_entry.pack(side=tkinter.LEFT)
        self.timedelay_button = tkinter.Button(self.frame1,command=self.set_timedelay,text="set timedelay",state=tkinter.DISABLED)
        self.timedelay_button.pack(side=tkinter.LEFT)
        self.get_version_button = tkinter.Button(self.frame1,command=self.get_version,text="get version",state=tkinter.DISABLED)
        self.get_version_button.pack(side=tkinter.LEFT)
        self.get_actualvalues_button = tkinter.Button(self.frame1,command=self.get_actualvalues,text="get actual values",state=tkinter.DISABLED)
        self.get_actualvalues_button.pack(side=tkinter.LEFT)
        self.set_actualvalues_button = tkinter.Button(self.frame1,command=self.set_actualvalues,text="set actual values",state=tkinter.DISABLED)
        self.set_actualvalues_button.pack(side=tkinter.LEFT)
        self.get_press_b = tkinter.Button(self.frame3,command=self.get_pressure,text="get pressure").pack(side=tkinter.LEFT)
        # setvalues and actual values
        self.channel_setpoint_checkbutton = dict()
        self.channel_setpoint_checkbutton_var = dict()
        self.channel_actual_value_var = dict()
        self.channel_actual_value_label = dict()
        self.gastype = tkinter.StringVar()
        self.gastype.set("?")
        self.gastype_menu = tkinter.OptionMenu(self.frame2,self.gastype,"ARGON","HELIUM","HYDROGEN","NITROGEN","AIR","H20")#state=Tkinter.DISABLED)
        self.gastype_menu.pack(side=tkinter.LEFT)
        self.gascorr_val = tkinter.IntVar()
        self.gascorr_val.set("?")
        self.gascorr_entry = tkinter.Entry(self.frame2,justify=tkinter.CENTER,textvariable=self.gascorr_val,width=4)
        self.gascorr_entry.pack(side=tkinter.LEFT)
        self.unit = tkinter.StringVar()
        self.unit.set("?")
        self.unit_menu = tkinter.OptionMenu(self.frame2,self.unit,"PASCAL","TORR","MBAR")#,state=Tkinter.DISABLED)
        self.unit_menu.pack(side=tkinter.LEFT)
        self.channel = tkinter.StringVar()
        self.channel.set("?")
        self.channel_menu = tkinter.OptionMenu(self.frame2,self.channel,"PR1","PR2","PR3")#state=Tkinter.DISABLED)
        self.channel_menu.pack(side=tkinter.LEFT)
        self.pressure_val = tkinter.StringVar()
        self.pressure_val.set("?")
        self.pressure_disp = tkinter.Entry(self.frame3,textvariable=self.pressure_val,justify=tkinter.CENTER,state="readonly")
        self.pressure_disp.pack(side=tkinter.LEFT,fill=tkinter.X)
        
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

    def set_actualvalues(self):
        if self.socket != None:
            self.log.debug("sending setpoint to the server")
            self.button_changed()
            self.log.debug("send data to %s:%d" % (self.ip,self.port))
            s = pickle.dumps(self.setpoint,-1)
            v = 'setact%d %s' % (len(s),s)
            self.socket.sendall(v)
            #print v

    def get_actualvalues(self):
        if self.socket != None:
            self.log.debug("get actualvalues from the server")
            self.socket.sendall("getact")
            v = self.socket.recv(1024*1024)
            r = re.findall("^([0-9]+) ",v)
            if r:
                length = int(r[0])
                v = v[1+len(r[0]):]
                self.actualvalue = pickle.loads(v[0:length])
                self.gastype.set(self.actualvalue['GT'])
                self.gascorr_val.set(float(self.actualvalue['GC']))
                self.channel.set(self.actualvalue['PR'])
                self.unit.set(self.actualvalue['U'])

    def get_pressure(self):
        if self.socket != None:
            self.socket.sendall("p")
            v = self.socket.recv(1024*1024)
            r = re.findall("^([0-9]+) ",v)
            #print v,r
            if r:
                length = int(r[0])
                v = v[1+len(r[0]):]
                self.pressure_val.set(pickle.loads(v[0:length]))

    def get_version(self):
        if self.socket != None:
            self.socket.sendall("version")
            v = self.socket.recv(100)
            self.log.info("server-version: %s" % v)

    def set_timedelay(self):
        if self.socket != None:
            v = min(max(1,self.timedelay_val.get()),999)
            self.timedelay_val.set(v)
            self.log.debug("set timedelay of the server to %03d ms" % v)
            self.socket.sendall("timedelay%03d" % v)

    def button_changed(self):
        if self.gastype.get() != -1:
            self.setpoint['GT'] = self.gastype.get()
        if self.gascorr_val.get() != -1:
            self.setpoint['GC'] = self.gascorr_val.get()
        if self.channel.get() != -1:
            self.setpoint['PR'] = self.channel.get()
        if self.unit.get() != -1:
            self.setpoint['U'] = self.unit.get()
        
        #print self.setpoint
        #if self.socket != None:
        #    self.log.debug("send data to %s:%d" % (self.ip,self.port))
        #    s = cPickle.dumps(self.setpoint,-1)
        #    v = 'p%d %s' % (len(s),s)
        #    self.socket.sendall(v)
        #self.main_window.after(100,func=self.set_actualvalues) # call after 100 milliseconds

    def open_connection_command(self):
        self.log.debug("connect to %s:%d" % (self.ip,self.port))
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip,self.port))
            self.open_connection_button.configure(state=tkinter.DISABLED)
            self.close_connection_button.configure(state=tkinter.NORMAL)
            self.quit_server_button.configure(state=tkinter.NORMAL)
            self.timedelay_button.configure(state=tkinter.NORMAL)
            self.get_version_button.configure(state=tkinter.NORMAL)
            self.get_actualvalues_button.configure(state=tkinter.NORMAL)
            self.set_actualvalues_button.configure(state=tkinter.NORMAL)
            self.log.debug("connected")
        except:
            self.socket = None
            self.log.warning("cannot connect to %s:%d" % (self.ip,self.port))
   
    def close_connection_command(self):
        self.log.debug("disconnect to %s:%d" % (self.ip,self.port))
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.socket = None
        self.open_connection_button.configure(state=tkinter.NORMAL)
        self.close_connection_button.configure(state=tkinter.DISABLED)
        self.quit_server_button.configure(state=tkinter.DISABLED)
        self.timedelay_button.configure(state=tkinter.DISABLED)
        self.get_version_button.configure(state=tkinter.DISABLED)
        self.get_actualvalues_button.configure(state=tkinter.DISABLED)
        self.set_actualvalues_button.configure(state=tkinter.DISABLED)
   
    def quit_server_command(self):
        if self.socket != None:
            self.log.info("quit server and disconnect")
            self.socket.sendall("quit")
            self.close_connection_command()

def main():
    parser = argparse.ArgumentParser(
        description='pressure900_client is a client to speak with the socket server pressure900_server.py to control the series 900 pressure controller on a serial interface.',
        epilog="Author: Richard Schlitz\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__pressure900_client_date__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-ip',
                        nargs=1,
                        default="localhost",
                        type=str,
                        required=False,
                        dest='ip',
                        help='Set the IP/host n. default: localhost',
                        metavar='n')
    parser.add_argument('-port',
                        nargs=1,
                        default=15121,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p. default: 15121',
                        metavar='p')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    args = parser.parse_args()
    if not isinstance(args.ip,str):
        args.ip = args.ip[0]
    if not isinstance(args.port,int):
        args.port = args.port[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    # logging
    log = logging.getLogger('dcc')
    log.setLevel(logging.DEBUG) # logging.DEBUG = 10
    # create console handler
    ch = logging.StreamHandler()
    if args.debug > 0:
        ch.setLevel(logging.DEBUG) # logging.DEBUG = 10
    else:
        ch.setLevel(logging.INFO) # logging.WARNING = 30
    ch.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s',datefmt='%H:%M:%S'))
    # add the handlers to log
    log.addHandler(ch)
    log.info("start logging in digital_controller_client: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    g = gui(args,log)
    g.start()

if __name__ == "__main__":
    main()
