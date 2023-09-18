#!/usr/bin/python -O
# Author: Richard Schlitz, Daniel Mohr
# Date: 2013-10-04, 2014-07-22

__mks_651_client_date__ = "2014-07-22"
__mks_651_client_version__ = __mks_651_client_date__

import argparse
import pickle
import logging
import logging.handlers
import re
import socket
import threading
import time
import tkinter

import plc_tools.plc_socket_communication

class gui(plc_tools.plc_socket_communication.tools_for_socket_communication):
    def __init__(self,args,log):
        self.send_data_to_socket_lock = threading.Lock()
        self.bufsize = 4096 # read/receive Bytes at once
        self.ip = args.ip
        self.port = args.port
        self.debug = args.debug
        self.log = log
        self.actualvalue = {'M':['R37',""],'O':[None,""],'C':[None,""],'H':[None,""],'D1':[None,""],'D2':[None,""],
							'D3':[None,""],'D4':[None,""],'D5':[None,""],'T1':['R26',""],'T2':['R27',""],
                            'T3':['R28',""],'T4':['R29',""],'T5':['R30',""],'S1': ['R1',""],'S2': ['R2',""],
                            'S3':['R3',""],'S4':['R4',""],'S5':['R10',""],'E':['R33',""],'F':['R34',""],
                            'V':['R51',""],'X1':['R41',""],'X2':['R42',""],'X3':['R43',""],'X4':['R44',""],
                            'X5':['R45',""],'M1':['R46',""],'M2':['R47',""],'M3':['R48',""],'M4':['R49',""],
                            'M5':['R50',""]}
        self.channel_dict = {"1-A":["","","",""],"2-B":["","","",""],"3-C":["","","",""],"4-D":["","","",""],"5-E":["","","",""],"none":["","","",""]}
        self.setpoint = self.actualvalue.copy()
        self.socket = None
        self.main_window = tkinter.Tk()
        self.main_window.title("mks_651_client.py (%s:%d)" % (self.ip,self.port))
        self.frame1 = tkinter.Frame(self.main_window)
        self.frame1.pack()
        self.frame2 = tkinter.Frame(self.main_window)
        self.frame2.pack()
        self.frame3 = tkinter.Frame(self.main_window)
        self.frame3.pack()
        self.frame4 = tkinter.Frame(self.main_window)
        self.frame4.pack()
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
        self.open_button = tkinter.Button(self.frame2,command=self.open_vent,text="Open",state=tkinter.DISABLED)
        self.open_button.pack(side=tkinter.LEFT)
        self.close_button = tkinter.Button(self.frame2,command=self.close_vent,text="Close",state=tkinter.DISABLED)
        self.close_button.pack(side=tkinter.LEFT)
        self.stop_button = tkinter.Button(self.frame2,command=self.stop_vent,text="Stop",state=tkinter.DISABLED)
        self.stop_button.pack(side=tkinter.LEFT)
        self.full_scale_values = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0, 10000.0, 1.3332, 2.6664, 13.332, 133.32, 1333.2, 6666.0, 13332.0]
        self.srange = tkinter.StringVar()
        self.srange.set("?")
        self.srange_list = ["00-0.1","01-0.2","02-0.5","03-1","04-2","05-5","06-10","07-50","08-100","09-500","10-1000",
                            "11-5000","12-10000","13-1.33","14-2.66","15-13.33","16-133.3","17-1333","18-6666","19-13332"]
        self.srange_menu = tkinter.OptionMenu(self.frame2,self.srange,*self.srange_list)
        self.srange_menu.pack(side=tkinter.LEFT)
        self.unit = tkinter.StringVar()
        self.unit.set("?")
        self.unit_list = ["00-Torr","01-mTorr","02-mbar","03-ubar","04-KPa","05-Pa","06-cmH2O","07-inH2O"]
        self.unit_menu = tkinter.OptionMenu(self.frame2,self.unit,*self.unit_list)
        self.unit_menu.pack(side=tkinter.LEFT)
        self.regul_type = tkinter.StringVar()
        self.regul_type.set("?")
        self.regul_type_list = ["0-Self Regulation","1-PID Regulation"]
        self.regul_menu = tkinter.OptionMenu(self.frame2,self.regul_type,*self.regul_type_list)
        self.regul_menu.pack(side=tkinter.LEFT)
        self.channel = tkinter.StringVar()
        self.channel.set("none")
        self.channel_list = ["1-A","2-B","3-C","4-D","5-E","none"]
        self.channel_menu = tkinter.OptionMenu(self.frame3,self.channel,*self.channel_list,command=self.update_channel)
        self.channel_menu.pack(side=tkinter.LEFT)
        self.channel_menu.configure(state=tkinter.DISABLED)
        self.setpoint_val = tkinter.StringVar()
        self.setpoint_val.set("?")
        self.setpoint_entry = tkinter.Entry(self.frame3,justify=tkinter.CENTER,textvariable=self.setpoint_val)
        self.setpoint_entry.pack(side=tkinter.LEFT)
        self.contr_type_val = tkinter.StringVar()
        self.contr_type_val.set("?")
        self.contr_type_list = ["0-Position","1-Pressure"]
        self.contr_type_menu = tkinter.OptionMenu(self.frame3,self.contr_type_val,*self.contr_type_list)
        self.contr_type_menu.pack(side=tkinter.LEFT)
        self.lead_val = tkinter.StringVar()
        self.lead_val.set("?")
        self.lead_label = tkinter.Label(self.frame3,text="Lead:")
        self.lead_label.pack(side=tkinter.LEFT)
        self.lead_entry = tkinter.Entry(self.frame3,justify=tkinter.CENTER,textvariable=self.lead_val)
        self.lead_entry.pack(side=tkinter.LEFT)
        self.gain_label = tkinter.Label(self.frame3,text="Gain:")
        self.gain_label.pack(side=tkinter.LEFT)
        self.gain_val = tkinter.StringVar()
        self.gain_val.set("?")
        self.gain_entry = tkinter.Entry(self.frame3,justify=tkinter.CENTER,textvariable=self.gain_val)
        self.gain_entry.pack(side=tkinter.LEFT)
        self.set_channel_val_button = tkinter.Button(self.frame3,command=self.set_channel_val,text="save current channel",state=tkinter.DISABLED)
        self.set_channel_val_button.pack(side=tkinter.LEFT)
        self.get_press_b = tkinter.Button(self.frame4,command=self.get_pressure,text="get pressure",state=tkinter.DISABLED)
        self.get_press_b.pack(side=tkinter.LEFT)
        self.pressure_val = tkinter.StringVar()
        self.pressure_val.set("?")
        self.pressure_disp = tkinter.Entry(self.frame4,textvariable=self.pressure_val,justify=tkinter.CENTER,state="readonly",width=26)
        self.pressure_disp.pack(side=tkinter.LEFT,fill=tkinter.X)
        self.get_vent_b = tkinter.Button(self.frame4,command=self.get_vent,text="get vent",state=tkinter.DISABLED)
        self.get_vent_b.pack(side=tkinter.LEFT)
        self.vent_val = tkinter.StringVar()
        self.vent_val.set("?")
        self.vent_disp = tkinter.Entry(self.frame4,textvariable=self.vent_val,justify=tkinter.CENTER,state="readonly")
        self.vent_disp.pack(side=tkinter.LEFT,fill=tkinter.X)
        
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
            self.update_before_send()
            self.log.debug("send data to %s:%d" % (self.ip,self.port))
            s = pickle.dumps(self.setpoint,-1)
            v = 'set%d %s' % (len(s),s)
            self.socket.sendall(v)
            #print v

    def get_actualvalues(self):
        if self.socket != None:
            self.log.debug("get actualvalues from the server")
            self.socket.sendall("get")
            self.actualvalue = self.receive_data_from_socket(self.socket,self.bufsize)
            self.update_after_receive()

    def get_pressure(self):
        if self.socket != None:
            self.socket.sendall("gap")
            p = self.receive_data_from_socket(self.socket,self.bufsize)
            fs = None
            try:
                fsindex = self.srange.get()[0:2]
                fs = self.full_scale_values[int(fsindex)]
                unit = self.unit.get()[3:]
            except: pass
            if fs:
                P = fs * float(p) / 100.0
                self.pressure_val.set("%8.4f %s (%s)" % (P,unit,p))
            else:
                self.pressure_val.set("(%s)" % p)

    def get_vent(self):
        if self.socket != None:
            self.socket.sendall("gav")
            v = self.socket.recv(1024)
            r = re.findall("^([0-9]+) ",v)
            if r:
                length = int(r[0])
                v = v[1+len(r[0]):]
                self.vent_val.set(pickle.loads(v[0:length]))
    
    def open_vent(self):
        if self.socket:
            self.socket.sendall("ovn")
        
    def close_vent(self):
        if self.socket:
            self.socket.sendall("cvn")
        
    def stop_vent(self):
        if self.socket:
            self.socket.sendall("svn")

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
            self.socket.sendall("std%03d" % v)

    def set_channel_val(self):
        dummy = self.channel.get()
        self.channel_dict[dummy][0] = self.setpoint_val.get()
        self.channel_dict[dummy][1] = self.contr_type_val.get()[0]
        self.channel_dict[dummy][2] = self.lead_val.get()
        self.channel_dict[dummy][3] = self.gain_val.get()
        #print self.channel_dict
        
    def update_channel(self,dummy):
        self.setpoint_val.set(self.channel_dict[dummy][0])
        self.contr_type_val.set(self.contr_type_list[int(self.channel_dict[dummy][1])])
        self.lead_val.set(self.channel_dict[dummy][2])
        self.gain_val.set(self.channel_dict[dummy][3])
        #print self.channel_dict
        
    def update_before_send(self):
        self.setpoint['E'][1] = self.srange.get()[0:2]
        self.setpoint['F'][1] = self.unit.get()[0:2] # maybe 0?
        self.setpoint['V'][1] = self.regul_type.get()[0]
        for i in range(1,6):
            if (str(i) == self.channel.get()[0]):
                self.setpoint['D%i' % i][1] = "1"
            else:
                self.setpoint['D%i' % i][1] = "0"
            self.setpoint['S%i' % i][1] = self.channel_dict[self.channel_list[i-1]][0]
            self.setpoint['T%i' % i][1] = self.channel_dict[self.channel_list[i-1]][1]
            self.setpoint['X%i' % i][1] = self.channel_dict[self.channel_list[i-1]][2]
            self.setpoint['M%i' % i][1] = self.channel_dict[self.channel_list[i-1]][3]
        self.setpoint['O'][1] = "0"
        self.setpoint['C'][1] = "0"
        self.setpoint['H'][1] = "0"
        #print self.setpoint
        #if self.socket != None:
        #    self.log.debug("send data to %s:%d" % (self.ip,self.port))
        #    s = cPickle.dumps(self.setpoint,-1)
        #    v = 'p%d %s' % (len(s),s)
        #    self.socket.sendall(v)
        #self.main_window.after(100,func=self.set_actualvalues) # call after 100 milliseconds
    
    def update_after_receive(self):
        flag = 0
        self.srange.set(self.srange_list[int(self.actualvalue['E'][1])])
        self.unit.set(self.unit_list[int(self.actualvalue['F'][1])])
        self.regul_type.set(self.regul_type_list[int(self.actualvalue['V'][1])])
        if ("1" == self.actualvalue['H'][1]):
            self.stop_button.configure(bg='blue')
        else:
            self.stop_button.configure(bg='light gray')
        if ("1" == self.actualvalue['O'][1]):
            self.open_button.configure(bg='blue')
        else:
            self.open_button.configure(bg='light gray')
        if ("1" == self.actualvalue['C'][1]):
            self.close_button.configure(bg='blue')
        else:
            self.close_button.configure(bg='light gray')
        for i in range(1,6):
            if ("1" == self.actualvalue['D%i' % i][1]):
                self.channel.set(self.channel_list[i-1])
                flag = 1
            self.channel_dict[self.channel_list[i-1]][0] = self.actualvalue['S%i' % i][1]
            self.channel_dict[self.channel_list[i-1]][1] = self.actualvalue['T%i' % i][1]
            self.channel_dict[self.channel_list[i-1]][2] = self.actualvalue['X%i' % i][1]
            self.channel_dict[self.channel_list[i-1]][3] = self.actualvalue['M%i' % i][1]
        if flag:
            self.update_channel(self.channel.get())
        else:
            self.channel.set(self.channel_list[5])
            
        
        
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
            self.set_channel_val_button.configure(state=tkinter.NORMAL)
            self.get_press_b.configure(state=tkinter.NORMAL)
            self.get_vent_b.configure(state=tkinter.NORMAL)
            self.channel_menu.configure(state=tkinter.NORMAL)
            self.close_button.configure(state=tkinter.NORMAL)
            self.stop_button.configure(state=tkinter.NORMAL)
            self.open_button.configure(state=tkinter.NORMAL)
            self.log.debug("connected")
        ##sollte nachher auskommentiert werden?
            self.get_actualvalues()
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
        self.set_channel_val_button.configure(state=tkinter.DISABLED)
        self.get_press_b.configure(state=tkinter.DISABLED)
        self.get_vent_b.configure(state=tkinter.DISABLED)
        self.channel_menu.configure(state=tkinter.DISABLED)
        self.open_button.configure(state=tkinter.DISABLED)
        self.close_button.configure(state=tkinter.DISABLED)
        self.stop_button.configure(state=tkinter.DISABLED)
   
    def quit_server_command(self):
        if self.socket != None:
            self.log.info("quit server and disconnect")
            self.socket.sendall("quit")
            self.close_connection_command()

def main():
    parser = argparse.ArgumentParser(
        description='mks_651_client is a client to speak with the socket server mks_651_server.py to control the series 651 pressure controller on a serial interface.',
        epilog="Author: Richard Schlitz, Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__mks_651_client_date__,help),
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
                        default=15122,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p. default: 15122',
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
