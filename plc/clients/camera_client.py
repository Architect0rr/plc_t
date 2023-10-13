#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2014-01-27, 2017-05-30

__camera_client_date__ = "2017-05-30"
__camera_client_version__ = __camera_client_date__

import argparse
import PIL.ImageTk
import logging
import logging.handlers
import socket
import threading
import time
import tkinter

import plc_tools.plccameraguidefaultclass

class gui(plc_tools.plccameraguidefaultclass.camera):
    def __init__(self,args,log,recvbuf,command_line_setting,window_name):
        self.send_data_to_socket_lock = threading.Lock()
        self.socketlock = threading.Lock()
        #self.bufsize = 4096 # read/receive Bytes at once
        #self.bufsize = 64 # read/receive Bytes at once
        self.bufsize = recvbuf # read/receive Bytes at once
        self.command_line_setting = command_line_setting
        self.ip = args.ip
        self.port = args.port
        self.debug = args.debug
        self.log = log
        self.values = None
        self.guid = self.command_line_setting['guid']
        self.mode = None
        self.color_coding = None
        self.framerate = None
        self.socket = None
        self.camlist = None
        self.guidlist = None
        self.main_window = tkinter.Tk()
        self.main_window.title("camera_client.py (%s:%d)%s" %
                               (self.ip,self.port,window_name))
        self.frame1 = tkinter.Frame(self.main_window)
        self.frame1.pack()
        self.frame2 = tkinter.Frame(self.main_window)
        self.frame2.pack()
        self.frame3 = tkinter.Frame(self.frame2)
        self.frame3.grid(column=0,row=0)
        self.frame4 = tkinter.Frame(self.frame2)
        self.frame4.grid(column=1,row=0)
        # control buttons
        self.open_connection_button = tkinter.Button(self.frame1,command=self.open_connection_command,text="connect",state=tkinter.NORMAL)
        self.open_connection_button.pack(side=tkinter.LEFT)
        self.close_connection_button = tkinter.Button(self.frame1,command=self.close_connection_command,text="disconnect",state=tkinter.DISABLED)
        self.close_connection_button.pack(side=tkinter.LEFT)
        self.quit_server_button = tkinter.Button(self.frame1,command=self.quit_server_command,text="quit server",state=tkinter.DISABLED)
        self.quit_server_button.pack(side=tkinter.LEFT)
        self.get_version_button = tkinter.Button(self.frame1,command=self.get_version,text="get version",state=tkinter.DISABLED)
        self.get_version_button.pack(side=tkinter.LEFT)
        # camera control buttons
        self.get_listcams_button = tkinter.Button(self.frame4,command=self.get_listcams_command,text="get camlist",state=tkinter.DISABLED)
        self.get_listcams_button.pack()
        self.guid_optionmenu_frame = tkinter.Frame(self.frame4)
        self.guid_optionmenu_frame.pack()
        self.guid_label = tkinter.Label(self.guid_optionmenu_frame,text="guid:")
        self.guid_label.pack(side=tkinter.LEFT)
        self.guid_optionslist = [" no guid "]
        self.guid_value = tkinter.StringVar()
        self.guid_value.set(self.guid_optionslist[0])
        self.guid_set_button = tkinter.Button(self.guid_optionmenu_frame,command=self.set_guid,text="set guid in GUI")
        self.guid_set_button.pack(side=tkinter.RIGHT)
        self.guid_optionmenu = tkinter.OptionMenu(self.guid_optionmenu_frame,self.guid_value,*self.guid_optionslist)
        self.guid_optionmenu.pack(side=tkinter.RIGHT)
        self.getvalues_button = tkinter.Button(self.frame4,command=self.getvalues_command,text="get values",state=tkinter.DISABLED)
        self.getvalues_button.pack()
        self.setvalues_button = tkinter.Button(self.frame4,command=self.setvalues_command,text="set values",state=tkinter.DISABLED)
        self.setvalues_button.pack()
        self.trigger_optionlist = ["no trigger","extern trigger"]
        self.trigger_value = tkinter.StringVar()
        self.trigger_value.set(self.trigger_optionlist[0])
        self.trigger_optionmenu = tkinter.OptionMenu(self.frame4,self.trigger_value,*self.trigger_optionlist)
        self.trigger_optionmenu.pack()
        self.values_frame = tkinter.Frame(self.frame4)
        self.values_frame.pack()
        self.values_frame_content_objects = dict()
        self.values_frame_content_values = dict()
        self.controlling_frame = tkinter.Frame(self.frame4)
        self.controlling_frame.pack()
        self.recording_path_are_set = False
        self.recording_path_frame = tkinter.Frame(self.controlling_frame)
        self.recording_path_frame.grid(column=0,row=0,columnspan=4)
        self.recording_pathes = ['/tmp/cam_','/tmp/cam_']
        self.create_recording_path_frame()
        self.recording_path_button = tkinter.Button(self.recording_path_frame,command=self.set_recording_path,text="set pathes/prefixes",state=tkinter.DISABLED)
        self.recording_path_button.grid(column=2,row=0,columnspan=2)
        self.recording_path_less_button = tkinter.Button(self.recording_path_frame,command=self.set_recording_less_pathes,text="- path")
        self.recording_path_less_button.grid(column=2,row=1)
        self.recording_path_more_button = tkinter.Button(self.recording_path_frame,command=self.set_recording_more_pathes,text="+ path")
        self.recording_path_more_button.grid(column=3,row=1)
        self.start_cam_button = tkinter.Button(self.controlling_frame,command=self.start_camera,text="start camera",state=tkinter.DISABLED)
        self.start_cam_button.grid(column=0,row=1)
        self.start_recording_button = tkinter.Button(self.controlling_frame,command=self.start_recording,text="start recording",state=tkinter.DISABLED)
        self.start_recording_button.grid(column=1,row=1)
        self.stop_recording_button = tkinter.Button(self.controlling_frame,command=self.stop_recording,text="stop recording",state=tkinter.DISABLED)
        self.stop_recording_button.grid(column=2,row=1)
        self.stop_cam_button = tkinter.Button(self.controlling_frame,command=self.stop_camera,text="stop camera",state=tkinter.DISABLED)
        self.stop_cam_button.grid(column=3,row=1)
        self.recording1frame_button = tkinter.Button(self.controlling_frame,command=self.recording1frame,text="rec 1 frame",state=tkinter.DISABLED)
        self.recording1frame_button.grid(column=0,row=2)
        # pictures on self.frame3
        self.get_frame_button = tkinter.Button(self.frame3,command=self.get_single_frame,text="get frame",state=tkinter.DISABLED)
        self.get_frame_button.grid(column=1,row=0)
        self.live_view_running = False
        self.start_live_view_button = tkinter.Button(self.frame3,command=self.start_live_view,text="start live view")
        self.start_live_view_button.grid(column=0,row=0)
        self.stop_live_view_button = tkinter.Button(self.frame3,command=self.stop_live_view,text="stop live view")
        self.stop_live_view_button.grid(column=2,row=0)
        #
        self.display_appearance_frame = tkinter.Frame(self.frame3)
        self.display_appearance_frame.grid(column=0,row=1,columnspan=3)
        offset = 250
        self.color_palette_highlight_bright = []
        for i in range(offset):
            self.color_palette_highlight_bright.extend((i, i, i)) # grayscale wedge
        for i in range(offset,255):
            self.color_palette_highlight_bright.extend((0, 0, i)) # grayscale wedge
        for i in range(255,256):
            self.color_palette_highlight_bright.extend((i, 0, 0)) # grayscale wedge
        self.display_kind_frame = tkinter.Frame(self.display_appearance_frame)
        self.display_kind_frame.pack(side=tkinter.LEFT)
        self.display_kind_optionlist = ["as is","highlight bright"]
        self.display_kind_value = tkinter.StringVar()
        self.display_kind_value.set(self.display_kind_optionlist[0])
        self.display_kind_optionmenu = tkinter.OptionMenu(self.display_kind_frame,self.display_kind_value,*self.display_kind_optionlist)
        self.display_kind_optionmenu.pack(side=tkinter.LEFT)
        #
        self.scaleframe = tkinter.Frame(self.display_appearance_frame)
        self.scaleframe.pack(side=tkinter.LEFT)
        #
        self.gamma = 1.0
        self.gammalabel = tkinter.Label(self.scaleframe,text="gamma: ")
        self.gammalabel.pack(side=tkinter.LEFT)
        self.gammavar = tkinter.DoubleVar()
        self.gammavar.set(self.gamma)
        self.gammaentry = tkinter.Entry(self.scaleframe,textvariable=self.gammavar,width=5)
        self.gammaentry.pack(side=tkinter.LEFT)
        #
        try:
            self.scale = args.scale
        except:
            self.scale = 1.0
        self.scalelabel = tkinter.Label(self.scaleframe,text="scale: ")
        self.scalelabel.pack(side=tkinter.LEFT)
        self.scalehalfbutton = tkinter.Button(self.scaleframe,text="*0.5",command=self.scalehalf)
        self.scalehalfbutton.pack(side=tkinter.LEFT)
        self.scaledoublebutton = tkinter.Button(self.scaleframe,text="*2",command=self.scaledouble)
        self.scaledoublebutton.pack(side=tkinter.LEFT)
        self.scalevar = tkinter.DoubleVar()
        self.scalevar.set(self.scale)
        self.scaleentry = tkinter.Entry(self.scaleframe,textvariable=self.scalevar,width=5)
        self.scaleentry.pack(side=tkinter.LEFT)
        self.scalesetbutton = tkinter.Button(self.scaleframe,text="set scale",command=self.setscale)
        self.scalesetbutton.pack(side=tkinter.LEFT)
        self.histogram_pic = None
        self.histogram_frame = tkinter.Frame(self.frame3)
        self.histogram_frame.grid(column=0,row=2,columnspan=3)
        self.histogram_frame_control = tkinter.Frame(self.histogram_frame)
        self.histogram_frame_control.pack()
        self.histogram_frame_pic = tkinter.Frame(self.histogram_frame)
        self.histogram_frame_pic.pack()
        self.histogram_create_var = tkinter.IntVar()
        self.histogram_create_checkbutton = tkinter.Checkbutton(self.histogram_frame_control,text="create",command=self.create_histogram_checkbutton,variable=self.histogram_create_var)
        self.histogram_create_checkbutton.pack(side=tkinter.LEFT)
        self.histogram_kind_optionlist = ["histogram","horizontal sums","vertical sums"]
        self.histogram_kind_value = tkinter.StringVar()
        self.histogram_kind_value.set(self.histogram_kind_optionlist[0])
        self.histogram_kind_optionmenu = tkinter.OptionMenu(self.histogram_frame_control,self.histogram_kind_value,*self.histogram_kind_optionlist)
        self.histogram_kind_optionmenu.pack(side=tkinter.LEFT)
        self.histogram_total_brightness_var = tkinter.StringVar()
        self.histogram_total_brightness_var.set("brightness:\n???")
        self.histogram_total_brightness_label = tkinter.Label(self.histogram_frame_control,textvariable=self.histogram_total_brightness_var,height=2,width=22)
        self.histogram_total_brightness_label.pack(side=tkinter.LEFT)
        self.histogram_width = 510
        self.histogram_height = 100
        self.histogram_img = PIL.ImageTk.PhotoImage("L",(self.histogram_width,self.histogram_height))
        self.histogram_label = tkinter.Label(self.histogram_frame_pic, image=self.histogram_img)
        self.histogram_label.pack(side=tkinter.LEFT)
        # picture output
        self.width = 100
        self.height = 100
        self.swidth = int(self.scale*self.width)
        self.sheight = int(self.scale*self.height)
        self.crop_x_1 = None
        self.crop_x_2 = None
        self.crop_y_1 = None
        self.crop_x_2 = None
        self.tcrop_x_1 = None
        self.tcrop_x_2 = None
        self.tcrop_y_1 = None
        self.tcrop_x_2 = None
        self.crop = False
        self.pic = None
        self.pic_lock = threading.Lock()
        self.frame5 = tkinter.Frame(self.frame3)
        self.frame5.grid(column=0,row=3,columnspan=3)
        if args.xdisplay != 0:
            hwx = args.xdisplay
        else:
            hwx = int(0.5*min(self.main_window.winfo_screenwidth(),self.main_window.winfo_screenheight()))
        if args.ydisplay != 0:
            hwy = args.ydisplay
        else:
            hwy = int(0.5*min(self.main_window.winfo_screenwidth(),self.main_window.winfo_screenheight()))
        self.picture_canvas = tkinter.Canvas(self.frame5,height=hwy,width=hwx,confine=False,scrollregion=(0,0,2048,2048))
        self.picture_canvas.grid(column=0,row=0)
        self.picture_canvas_frame = tkinter.Frame(self.frame5)
        self.picture_canvas.create_window(0,0,anchor=tkinter.NW,window=self.picture_canvas_frame,height=2048,width=2048)
        # y scrollbar
        self.scrollY = tkinter.Scrollbar(self.frame5,orient=tkinter.VERTICAL,command=self.picture_canvas.yview)
        self.scrollY.grid(row=0,column=1,sticky=tkinter.N+tkinter.S)
        self.picture_canvas["yscrollcommand"]  =  self.scrollY.set
        # x scrollbar
        self.scrollX = tkinter.Scrollbar(self.frame5,orient=tkinter.HORIZONTAL,command=self.picture_canvas.xview)
        self.scrollX.grid(row=1,column=0,sticky=tkinter.E+tkinter.W)
        self.picture_canvas["xscrollcommand"]  =  self.scrollX.set
        self.update_img_delay = args.update_img_delay
        self.update_picture_label_id = None
        self.img = None
        self.img_time = time.time()
        self.img_last_time = self.img_time + 1.0
        self.update_picture_label = False
        self.update_img_lock = threading.Lock()
        self.create_histogram_lock = threading.Lock()
        self.update_img_it = 0
        self.update_img_it_int = 10
        self.update_img_t0 = time.time()
        self.update_img_t1 = time.time()
        self.picture_label_lock = threading.Lock()
        self.movie_label = None
        self.movie_label_bind_id0 = None
        self.movie_label_bind_id1 = None
        self.movie_label_bind_id2 = None
        self.update_img_request_stop = False
        self.socket_pic_data = None
        self.histogram_pic = None
        self.new_histogram_pic = False
        self.after_widget = self.main_window
        self.notebook = None
        self.extern_img = None
        self.create_picture_label()

    def start(self):
        self.main_window.mainloop()
        self.quit()
        try:
            self.main_window.destroy()
        except:
            pass

    def open_connection_command(self):
        self.log.debug("connect to %s:%d" % (self.ip,self.port))
        self.socketlock.acquire() # lock
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip,self.port))
            self.open_connection_button.configure(state=tkinter.DISABLED)
            self.close_connection_button.configure(state=tkinter.NORMAL)
            self.quit_server_button.configure(state=tkinter.NORMAL)
            self.get_version_button.configure(state=tkinter.NORMAL)
            self.get_listcams_button.configure(state=tkinter.NORMAL)
            self.getvalues_button.configure(state=tkinter.NORMAL)
            self.start_cam_button.configure(state=tkinter.NORMAL)
            self.start_recording_button.configure(state=tkinter.NORMAL)
            self.stop_recording_button.configure(state=tkinter.NORMAL)
            self.recording1frame_button.configure(state=tkinter.NORMAL)
            self.stop_cam_button.configure(state=tkinter.NORMAL)
            self.recording_path_button.configure(state=tkinter.NORMAL)
            self.get_frame_button.configure(state=tkinter.NORMAL)
            self.log.debug("connected")
        except:
            self.socket = None
            self.log.warning("cannot connect to %s:%d" % (self.ip,self.port))
        self.socketlock.release() # release the lock
        if (self.guid != None) and (self.guid != -1) and (self.guid != -2):
            # setting default features; possible not all and not correct!
            self.camlist = [{'vendor': self.command_line_setting['vendor'],
                             'features': {'brightness': {'mode': 'manual', 'val': 16, 'modes': ['manual']}, 'trigger_delay': {'mode': 'manual', 'val': 0.0, 'modes': ['manual']}, 'shutter': {'mode': 'manual', 'val': 2000, 'modes': ['manual', 'auto']}, 'trigger': {'mode': 'TRIGGER_MODE_0', 'val': 0, 'modes': ['TRIGGER_MODE_0', 'TRIGGER_MODE_1', 'TRIGGER_MODE_15']}, 'gain': {'mode': 'manual', 'val': 0, 'modes': ['manual', 'auto']}, 'gamma': {'mode': 'manual', 'val': 0, 'modes': ['manual']}, 'exposure': {'mode': 'manual', 'val': 125, 'modes': ['manual']}},
                             'isospeed': 0,
                             'model': self.command_line_setting['model'],
                             'uid': self.guid,
                             'unit': 0,
                             'modes': {'FORMAT7_0': {'color_codings': [self.color_coding], 'max_image_size': (self.command_line_setting['max_image_size_x'], self.command_line_setting['max_image_size_y']), 'unit_position': (self.command_line_setting['unit_position_x'],self.command_line_setting['unit_position_y'])}}
                             }]
            self.guidlist = [self.guid]
            self.guid_optionslist = ["%s %s (%d)" % (self.command_line_setting['vendor'],self.command_line_setting['model'],self.guid)]
            self.guid_optionmenu.destroy()
            self.guid_value.set(self.guid_optionslist[0])
            self.guid_optionmenu = tkinter.OptionMenu(self.guid_optionmenu_frame,self.guid_value,*self.guid_optionslist)
            self.guid_optionmenu.pack(side=tkinter.RIGHT)
            self.values_frame_content()
            self.getvalues_command()
            x = self.command_line_setting['image_size_x']
            if x != None:
                self.values_frame_content_values['x image_position'].set(int(x))
            y = self.command_line_setting['image_size_y']
            if y != None:
                self.values_frame_content_values['y image_position'].set(int(y))
            x0 = self.command_line_setting['image_position_x']
            if x0 != "default":
                self.values_frame_content_values['x image_position'].set(int(x0))
            y0 = self.command_line_setting['image_position_y']
            if y0 != "default":
                self.values_frame_content_values['y image_position'].set(int(y0))
            brightness = self.command_line_setting['brightness']
            if brightness != "default":
                self.values_frame_content_values['brightness var'].set(int(brightness))
            trigger_delay = self.command_line_setting['trigger_delay']
            if trigger_delay != "default":
                self.values_frame_content_values['trigger_delay var'].set(float(trigger_delay))
            shutter = self.command_line_setting['shutter']
            if shutter != "default":
                self.values_frame_content_values['shutter var'].set(int(shutter))
            trigger = self.command_line_setting['trigger']
            if trigger != "default":
                self.values_frame_content_values['trigger var'].set(int(trigger))
            gain = self.command_line_setting['gain']
            if gain != "default":
                self.values_frame_content_values['gain var'].set(int(gain))
            gamma = self.command_line_setting['gamma']
            if gamma != "default":
                self.values_frame_content_values['gamma var'].set(int(gamma))
            exposure = self.command_line_setting['exposure']
            if exposure != "default":
                self.values_frame_content_values['exposure var'].set(int(exposure))
            if self.command_line_setting['extern_trigger']:
                self.trigger_value.set(self.trigger_optionlist[1])
            self.set_recording_path()
            self.setvalues_command()

    def close_connection_command(self):
        self.log.debug("disconnect to %s:%d" % (self.ip,self.port))
        self.live_view_running = False
        self.socketlock.acquire() # lock
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.log.debug("disconnected")
        except:
            self.log.warning("cannot disconnect to %s:%d" % (self.ip,self.port))
        self.socket = None
        self.socketlock.release() # release the lock
        self.open_connection_button.configure(state=tkinter.NORMAL)
        self.close_connection_button.configure(state=tkinter.DISABLED)
        self.quit_server_button.configure(state=tkinter.DISABLED)
        self.get_version_button.configure(state=tkinter.DISABLED)
        self.get_listcams_button.configure(state=tkinter.DISABLED)
        self.getvalues_button.configure(state=tkinter.DISABLED)
        self.setvalues_button.configure(state=tkinter.DISABLED)
        self.start_cam_button.configure(state=tkinter.DISABLED)
        self.start_recording_button.configure(state=tkinter.DISABLED)
        self.stop_recording_button.configure(state=tkinter.DISABLED)
        self.recording1frame_button.configure(state=tkinter.DISABLED)
        self.stop_cam_button.configure(state=tkinter.DISABLED)
        self.recording_path_button.configure(state=tkinter.DISABLED)
        self.get_frame_button.configure(state=tkinter.DISABLED)

def main():
    help = ""
    help += "crop function: By clicking with the left mouse button on the picture and\n"
    help += "release the mouse button on an possibly other position, the resulting rectangle\n"
    help += "will be displayed and the margin will be cropped. You come back to the original\n"
    help += "view by clicking with the right mouse button."
    
    parser = argparse.ArgumentParser(
        description='camera_client is a client to speak with the socket server camera_server.py to control a camera attached to the server by firewire.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007.\n\n%s" % (__camera_client_date__,help),
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
                        default=15114,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p. default: 15114',
                        metavar='p')
    parser.add_argument('-recvbuf',
                        nargs=1,
                        default=4096,
                        type=int,
                        required=False,
                        dest='recvbuf',
                        help='Set the number of Bytes to receive at once by the socket communication. default: 4096',
                        metavar='n')
    parser.add_argument('-update_img_delay',
                        nargs=1,
                        default=6,
                        type=int,
                        required=False,
                        dest='update_img_delay',
                        help='Set the minimum time delay between displaying 2 images. default: 6',
                        metavar='a')
    parser.add_argument('-xdisplay',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='xdisplay',
                        help='Set the width of the displayed frames. default: 0 (auto)',
                        metavar='x')
    parser.add_argument('-ydisplay',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='ydisplay',
                        help='Set the height of the displayed frames. default: 0 (auto)',
                        metavar='x')
    parser.add_argument('-scale',
                        nargs=1,
                        default=1.0,
                        type=float,
                        required=False,
                        dest='scale',
                        help='Set the initial scale of the view. default: 1.0',
                        metavar='f')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    parser.add_argument('-window_name',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='window_name',
                        help='An optional name for the window.',
                        metavar='name')
    parser.add_argument('-guid',
                        nargs=1,
                        default="",
                        type=str,
                        required=False,
                        dest='guid',
                        help='A camera with this guid will be used. Only with this given, further initial parameters are relevant:',
                        metavar='id')
    parser.add_argument('-vendor',
                        nargs=1,
                        default="AVT",
                        type=str,
                        required=False,
                        dest='vendor',
                        help='default: "AVT"',
                        metavar='name')
    parser.add_argument('-model',
                        nargs=1,
                        default="Guppy F080B",
                        type=str,
                        required=False,
                        dest='model',
                        help='default: "Guppy F080B"',
                        metavar='name')
    parser.add_argument('-max_image_size_x',
                        nargs=1,
                        default=1032,
                        type=int,
                        required=False,
                        dest='max_image_size_x',
                        help='default: 1032',
                        metavar='x')
    parser.add_argument('-max_image_size_y',
                        nargs=1,
                        default=778,
                        type=int,
                        required=False,
                        dest='max_image_size_y',
                        help='default: 778',
                        metavar='y')
    parser.add_argument('-unit_position_x',
                        nargs=1,
                        default=2,
                        type=int,
                        required=False,
                        dest='unit_position_x',
                        help='default: 2',
                        metavar='x')
    parser.add_argument('-unit_position_y',
                        nargs=1,
                        default=2,
                        type=int,
                        required=False,
                        dest='unit_position_y',
                        help='default: 2',
                        metavar='y')
    parser.add_argument('-image_size_x',
                        nargs=1,
                        default=1032,
                        type=int,
                        required=False,
                        dest='image_size_x',
                        help='default: 1032',
                        metavar='x')
    parser.add_argument('-image_size_y',
                        nargs=1,
                        default=778,
                        type=int,
                        required=False,
                        dest='image_size_y',
                        help='default: 778',
                        metavar='y')
    parser.add_argument('-image_position_x',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='image_position_x',
                        help='default: 0',
                        metavar='x')
    parser.add_argument('-image_position_y',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='image_position_y',
                        help='default: 0',
                        metavar='y')
    parser.add_argument('-brightness',
                        nargs=1,
                        default=16,
                        type=int,
                        required=False,
                        dest='brightness',
                        help='default: 16',
                        metavar='i')
    parser.add_argument('-trigger_delay',
                        nargs=1,
                        default=0.0,
                        type=float,
                        required=False,
                        dest='trigger_delay',
                        help='default: 0.0',
                        metavar='i')
    parser.add_argument('-shutter',
                        nargs=1,
                        default=2000,
                        type=int,
                        required=False,
                        dest='shutter',
                        help='default: 2000',
                        metavar='i')
    parser.add_argument('-trigger',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='trigger',
                        help='default: 0',
                        metavar='i')
    parser.add_argument('-gain',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='gain',
                        help='default: 0',
                        metavar='i')
    parser.add_argument('-gamma',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='gamma',
                        help='default: 0',
                        metavar='i')
    parser.add_argument('-exposure',
                        nargs=1,
                        default=125,
                        type=int,
                        required=False,
                        dest='exposure',
                        help='default: 125',
                        metavar='i')
    parser.add_argument('-extern_trigger',
                        action='store_true',
                        default=False,
                        dest='extern_trigger',
                        help='')
    args = parser.parse_args()
    if not isinstance(args.ip,str):
        args.ip = args.ip[0]
    if not isinstance(args.port,int):
        args.port = args.port[0]
    if not isinstance(args.recvbuf,int):
        args.recvbuf = args.recvbuf[0]
    if not isinstance(args.update_img_delay,int):
        args.update_img_delay = args.update_img_delay[0]
    if not isinstance(args.xdisplay,int):
        args.xdisplay = args.xdisplay[0]
    if not isinstance(args.ydisplay,int):
        args.ydisplay = args.ydisplay[0]
    if not isinstance(args.scale,float):
        args.scale = args.scale[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.window_name,str):
        args.window_name = args.window_name[0]
    if args.window_name != "":
        args.window_name = " " + args.window_name
    if not isinstance(args.guid,str):
        args.guid = args.guid[0]
    if args.guid == "":
        args.guid = None
    else:
        try:
            if (args.guid[0:2] == "0x") or (args.guid[0:2] == "0X"):
                args.guid = int(args.guid,16)
            else:
                args.guid = int(args.guid)
        except: pass
    if not isinstance(args.vendor,str):
        args.vendor = args.vendor[0]
    if not isinstance(args.model,str):
        args.model = args.model[0]
    if not isinstance(args.max_image_size_x,int):
        args.max_image_size_x = args.max_image_size_x[0]
    if not isinstance(args.max_image_size_y,int):
        args.max_image_size_y = args.max_image_size_y[0]
    if not isinstance(args.unit_position_x,int):
        args.unit_position_x = args.unit_position_x[0]
    if not isinstance(args.unit_position_y,int):
        args.unit_position_y = args.unit_position_y[0]
    if not isinstance(args.image_size_x,int):
        args.image_size_x = args.image_size_x[0]
    if not isinstance(args.image_size_y,int):
        args.image_size_y = args.image_size_y[0]
    if not isinstance(args.image_position_x,int):
        args.image_position_x = args.image_position_x[0]
    if not isinstance(args.image_position_y,int):
        args.image_position_y = args.image_position_y[0]
    if not isinstance(args.brightness,int):
        args.brightness = args.brightness[0]
    if not isinstance(args.trigger_delay,float):
        args.trigger_delay = args.trigger_delay[0]
    if not isinstance(args.shutter,int):
        args.shutter = args.shutter[0]
    if not isinstance(args.trigger,int):
        args.trigger = args.trigger[0]
    if not isinstance(args.gain,int):
        args.gain = args.gain[0]
    if not isinstance(args.gamma,int):
        args.gamma = args.gamma[0]
    if not isinstance(args.exposure,int):
        args.exposure = args.exposure[0]
    # logging
    log = logging.getLogger('cc')
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
    log.info("start logging in camera_client: %s" % time.strftime("%a, %d %b %Y %H:%M:%S %z %Z", time.localtime()))
    command_line_setting = {"guid": args.guid,
                            "vendor": args.vendor,
                            "model": args.model,
                            "max_image_size_x": args.max_image_size_x,
                            "max_image_size_y": args.max_image_size_y,
                            "unit_position_x": args.unit_position_x,
                            "unit_position_y": args.unit_position_y,
                            "image_size_x": args.image_size_x,
                            "image_size_y": args.image_size_y,
                            "image_position_x": args.image_position_x,
                            "image_position_y": args.image_position_y,
                            "brightness": args.brightness,
                            "trigger_delay": args.trigger_delay,
                            "shutter": args.shutter,
                            "trigger": args.trigger,
                            "gain": args.gain,
                            "gamma": args.gamma,
                            "exposure": args.exposure,
                            "extern_trigger": args.extern_trigger}
    g = gui(args,log,args.recvbuf,command_line_setting,args.window_name)
    g.start()

if __name__ == "__main__":
    main()
