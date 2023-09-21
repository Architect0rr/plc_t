"""gui for controling camera

Author: Daniel Mohr
Date: 2013-04-18, 2017-05-30
"""

import PIL.ImageTk
import logging
import re
import socket
import subprocess
import threading
import time
import tkinter

from ..plc_tools import plccameraguidefaultclass

log = logging.getLogger('plc.plc_gui.camera')
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

class camera(plccameraguidefaultclass.camera):
    """gui for camera control

    Author: Daniel Mohr
    Date: 2013-04-18, 2017-05-30
    """
    def __init__(self,config=None,confsect=None,pw=None,screenx=1024,screeny=768,extern_img=None,extern_x=100,notebook=None,notebookindex=None,notebookextern=0):
        """__init__(self,config=None,confsect=None,pw=None,rb=None,vb=None,debugprint=None)

        create gui for camera control

        Parameters:
           config : config from ConfigParser
                    a class to get setting from the configs
           confsect : string
                      a string describing the section in the config file
                      represented by the config
           pw : Tk parent
                the TK-GUI will be created in the parent pw with Tkinter
           screenx : integer
                     the screen resolution in x
           screeny : integer
                     the screen resolution in y

        Author: Daniel Mohr
        Date: 2013-03-21, 2017-05-30
        """
        # http://www.tkdocs.com/tutorial/complex.html
        self.send_data_to_socket_lock = threading.Lock()
        self.socketlock = threading.Lock()
        self.config=config
        self.padx = self.config.values.get('gui','padx')
        self.pady = self.config.values.get('gui','pady')
        self.confsect=confsect
        self.pw=pw
        self.cmd = self.config.values.get(self.confsect,'server_command')
        self.start_server = self.config.values.getboolean(self.confsect,'start_server')
        self.logfile = self.config.values.get(self.confsect,'server_logfile')
        self.rf = self.config.values.get(self.confsect,'server_runfile')
        self.ip = self.config.values.get(self.confsect,'ip')
        self.port = self.config.values.getint(self.confsect,'port')
        self.server_max_start_time = self.config.values.getfloat(self.confsect,'server_max_start_time')
        self.values = None
        self.guid = self.config.values.get(self.confsect,'guid')
        if (self.guid[0:2] == "0x") or (self.guid[0:2] == "0X"):
            self.guid = int(self.guid,16)
        else:
            self.guid = int(self.guid)
        self.vendor = self.config.values.get(self.confsect,'vendor')
        self.model = self.config.values.get(self.confsect,'model')
        self.mode = self.config.values.get(self.confsect,'mode')
        self.color_coding = self.config.values.get(self.confsect,'color_coding')
        self.framerate = self.config.values.getfloat(self.confsect,'framerate')
        self.max_image_size_x = self.config.values.getint(self.confsect,'max x-image')
        self.max_image_size_y = self.config.values.getint(self.confsect,'max y-image')
        self.socket = None
        self.camlist = None
        self.guidlist = None
        self.control_frame_width = self.config.values.getint(self.confsect,'control_frame_width')
        self.log = log
        if float(screenx)/float(screeny) > 2:
            # we have more than 1 monitor, assuming 4:3
            screenx = 0.8*int(screeny * 16.0 / 9.0)
        self.screenx = screenx
        self.screeny = screeny
        self.extern_img = extern_img
        self.extern_x = extern_x
        self.notebook = notebook
        self.notebookindex = notebookindex
        self.notebookextern = notebookextern
        self.update_img_intern = False
        self.update_img_extern = False
        #self.bufsize = 4096 # read/receive Bytes at once
        #self.bufsize = 64 # read/receive Bytes at once
        self.bufsize = self.config.values.getint(self.confsect,'recv_bufsize') # read/receive Bytes at once
        self.log.debug("init camera window %s" % self.confsect)

#        self.master_paned_window = ttk.Panedwindow(self.pw,orient=Tkinter.HORIZONTAL)
#        self.view_frame = ttk.Labelframe(self.master_paned_window,text="view",width=self#.screenx-self.control_frame_width,height=int(0.8*self.screeny))
#        #self.view_frame = Tkinter.LabelFrame(self.master_paned_window,text="view",width=self.screenx-self.control_frame_width,height=int(0.8*self.screeny))
#        self.control_frame = ttk.Labelframe(self.master_paned_window,text="control",width=self.control_frame_width,height=int(0.8*self.screeny))
#        #self.control_frame = Tkinter.LabelFrame(self.master_paned_window,text="control",width=self.control_frame_width,height=int(0.8*self.screeny))
#        self.master_paned_window.add(self.view_frame)
#        self.master_paned_window.add(self.control_frame)
#        self.master_paned_window.pack()

        self.master_paned_window = tkinter.PanedWindow(self.pw,orient=tkinter.HORIZONTAL,height=int(0.8*self.screeny))
        self.view_frame = tkinter.LabelFrame(self.master_paned_window,text="view",width=self.screenx-self.control_frame_width,height=int(0.8*self.screeny))
        self.control_frame = tkinter.LabelFrame(self.master_paned_window,text="control",width=self.control_frame_width,height=int(0.8*self.screeny))
        self.master_paned_window.add(self.view_frame)
        self.master_paned_window.add(self.control_frame)
        self.master_paned_window.pack()

#        self.view_frame = Tkinter.LabelFrame(self.pw,text="view",width=self.screenx-self.control_frame_width,height=int(0.8*self.screeny))
#        self.view_frame.pack(side=Tkinter.LEFT)
#        self.control_frame = Tkinter.LabelFrame(self.pw,text="control",width=self.control_frame_width,height=int(0.8*self.screeny))
#        self.control_frame.pack(side=Tkinter.LEFT)

        #print "cam %s view width = %d" % (self.confsect,self.view_frame.winfo_width())
        self.control_frame1 = tkinter.Frame(self.control_frame)
        self.control_frame1.pack()
        self.frame4 = tkinter.Frame(self.control_frame)
        self.frame4.pack()
        self.control_frame3 = tkinter.Frame(self.control_frame)
        self.control_frame3.pack()
        self.frame3 = tkinter.Frame(self.view_frame)
        self.frame3.pack()
        # frame1
        self.open_connection_button = tkinter.Button(self.control_frame1,command=self.open_connection_command,text="connect",state=tkinter.NORMAL)
        self.open_connection_button.pack(side=tkinter.LEFT)
        self.close_connection_button = tkinter.Button(self.control_frame1,command=self.close_connection_command,text="disconnect",state=tkinter.DISABLED)
        self.close_connection_button.pack(side=tkinter.LEFT)
        self.quit_server_button = tkinter.Button(self.control_frame1,command=self.quit_server_command,text="quit server",state=tkinter.DISABLED)
        self.quit_server_button.pack(side=tkinter.LEFT)
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
        self.values_frame = tkinter.Frame(self.frame4)
        self.values_frame.pack()
        self.values_frame_content_objects = dict()
        self.values_frame_content_values = dict()
        self.controlling_frame = tkinter.Frame(self.frame4)
        self.controlling_frame.pack()
        self.recording_path_are_set = False
        self.recording_path_frame = tkinter.Frame(self.controlling_frame)
        self.recording_path_frame.grid(column=0,row=0,columnspan=4)
        self.camera_pathes_exists_in_config = False
        if self.config.values.has_option(self.confsect,'camera_file_prefix1'):
            i = 1
            s = True
            self.recording_pathes = []
            while s:
                s = False
                if self.config.values.has_option(self.confsect,'camera_file_prefix%d' % i):
                    p = self.config.values.get(self.confsect,'camera_file_prefix%d' % i)
                    if len(p) > 0:
                        self.recording_pathes += [p]
                        i += 1
                        s = True
                        self.camera_pathes_exists_in_config = True
        else:
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
        self.scale = 1.0
        #self.scaleframe = Tkinter.Frame(self.frame3)
        #self.scaleframe.grid(column=0,row=1,columnspan=3)
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
        self.histogram_frame = tkinter.Frame(self.frame3)
        self.histogram_frame.grid(column=0,row=2,columnspan=3)
        self.histogram_frame_control = tkinter.Frame(self.histogram_frame)
        self.histogram_frame_control.pack()
        self.histogram_frame_pic = tkinter.Frame(self.histogram_frame)
        self.histogram_frame_pic.pack()
        self.histogram_create_var = tkinter.IntVar()
        #self.histogram_create_checkbutton = Tkinter.Checkbutton(self.histogram_frame,text="create\nhistogram",command=self.create_histogram_checkbutton,variable=self.histogram_create_var)
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
        self.histogram_width = 450
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
        hw = int(0.5*min(self.screenx,self.screeny))
        self.picture_canvas = tkinter.Canvas(self.frame5,height=hw,width=hw,confine=False,scrollregion=(0,0,2048,2048))
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
        self.update_img_delay = self.config.values.get(self.confsect,'update_img_delay')
        self.update_picture_label_id = None
        self.img = None
        self.img_time = time.time()
        self.img_last_time = self.img_time + 1.0
        self.update_picture_label = False
        self.update_img_lock = threading.Lock()
        self.create_histogram_lock = threading.Lock()
        self.picture_label_lock = threading.Lock()
        self.movie_label = None
        self.movie_label_bind_id0 = None
        self.movie_label_bind_id1 = None
        self.movie_label_bind_id2 = None
        self.update_img_request_stop = False
        self.socket_pic_data = None
        self.histogram_pic = None
        self.new_histogram_pic = False
        #self.after_widget = self.open_connection_button
        self.after_widget = self.pw
        self.create_picture_label()

    def quit(self):
        try:
            self.log.info("shutdown and close connection")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass
        self.socket = None

    def open_connection_command(self):
        if self.socket == None:
            self.log.debug("try to connect to %s:%d" % (self.ip,self.port))
            self.socketlock.acquire() # lock
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ip,self.port))
                self.log.debug("connected")
            except:
                self.socket = None
            self.socketlock.release() # release the lock
            if (self.socket == None) and (self.start_server):
                c = [self.cmd]
                if (self.guid != None) and (self.guid != -1) and (self.guid != -2):
                    c += ["-guid","%s" % self.guid]
                if (self.mode != None) and (self.mode != "-1"):
                    c += ["-mode",self.mode]
                if (self.color_coding != None) and (self.color_coding != "-1"):
                    c += ["-color_coding",self.color_coding]
                if (self.framerate != None) and (self.framerate != "-1"):
                    c += ["-framerate","%s" % self.framerate]
                c += ["-logfile",self.logfile,
                     "-runfile",self.rf,
                     "-ip",self.ip,
                     "-port","%s" % self.port]
                #self.log.debug("start camera_server '%s'" %  (string.join(c)))
                self.log.debug("start camera_server '%s'" %  (" ".join(c)))
                prc_srv = subprocess.Popen(c)
                t0 = time.time()
                prc_srv.poll()
                while ((prc_srv.returncode == None) and
                       (time.time()-t0<self.server_max_start_time)):
                    time.sleep(0.01)
                    prc_srv.poll()
                prc_srv.poll()
                if prc_srv.returncode == None:
                    self.log.debug("camera_server does not fork until now!")
                else:
                    if prc_srv.returncode == 0:
                        self.log.debug("camera_server seems to fork")
                    else:
                        self.log.warning("camera_server terminate with status: %s" % prc_srv.returncode)
                time.sleep(0.5)
        if self.socket == None:
            self.log.debug("try to connect to %s:%s" % (self.ip,self.port))
            self.socketlock.acquire() # lock
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ip,self.port))
                self.log.debug("connected")
            except:
                self.socket = None
                self.log.warning("cannot connect to %s:%d" % (self.ip,self.port))
            self.socketlock.release() # release the lock
        if self.socket != None:
            self.open_connection_button.configure(state=tkinter.DISABLED)
            self.close_connection_button.configure(state=tkinter.NORMAL)
            self.quit_server_button.configure(state=tkinter.NORMAL)
            self.get_listcams_button.configure(state=tkinter.NORMAL)
            self.getvalues_button.configure(state=tkinter.NORMAL)
            self.start_cam_button.configure(state=tkinter.NORMAL)
            self.start_recording_button.configure(state=tkinter.NORMAL)
            self.stop_recording_button.configure(state=tkinter.NORMAL)
            self.recording1frame_button.configure(state=tkinter.NORMAL)
            self.stop_cam_button.configure(state=tkinter.NORMAL)
            self.recording_path_button.configure(state=tkinter.NORMAL)
            self.get_frame_button.configure(state=tkinter.NORMAL)
            if (self.guid != None) and (self.guid != -1) and (self.guid != -2):
                self.log.debug("get all")
                # setting default features; possible not all and not correct!
                self.camlist = [{'vendor': self.vendor,
                                 'features': {'brightness': {'mode': 'manual', 'val': 16, 'modes': ['manual']}, 'trigger_delay': {'mode': 'manual', 'val': 0.0, 'modes': ['manual']}, 'shutter': {'mode': 'manual', 'val': 2000, 'modes': ['manual', 'auto']}, 'trigger': {'mode': 'TRIGGER_MODE_0', 'val': 0, 'modes': ['TRIGGER_MODE_0', 'TRIGGER_MODE_1', 'TRIGGER_MODE_15']}, 'gain': {'mode': 'manual', 'val': 0, 'modes': ['manual', 'auto']}, 'gamma': {'mode': 'manual', 'val': 0, 'modes': ['manual']}, 'exposure': {'mode': 'manual', 'val': 125, 'modes': ['manual']}},
                                 'isospeed': 0,
                                 'model': self.model,
                                 'guid': self.guid,
                                 'unit': 0,
                                 'modes': {'FORMAT7_0': {'color_codings': [self.color_coding], 'max_image_size': (self.max_image_size_x, self.max_image_size_y), 'unit_position': (self.config.values.getint(self.confsect,'unit_position x'), self.config.values.getint(self.confsect,'unit_position y'))}}
                                 }]
                self.guidlist = [self.guid]
                self.guid_optionslist = ["%s %s (%d)" % (self.vendor,self.model,self.guid)]
                self.guid_optionmenu.destroy()
                self.guid_value.set(self.guid_optionslist[0])
                self.guid_optionmenu = tkinter.OptionMenu(self.guid_optionmenu_frame,self.guid_value,*self.guid_optionslist)
                self.guid_optionmenu.pack(side=tkinter.RIGHT)
                self.values_frame_content()
                self.getvalues_command()
                x = self.config.values.get(self.confsect,'x-image size')
                if x != "default":
                    self.values_frame_content_values['x image_position'].set(int(x))
                y = self.config.values.get(self.confsect,'y-image size')
                if y != "default":
                    self.values_frame_content_values['y image_position'].set(int(y))
                x0 = self.config.values.get(self.confsect,'x-image position')
                if x0 != "default":
                    self.values_frame_content_values['x image_position'].set(int(x0))
                y0 = self.config.values.get(self.confsect,'y-image position')
                if y0 != "default":
                    self.values_frame_content_values['y image_position'].set(int(y0))
                brightness = self.config.values.get(self.confsect,'brightness')
                if brightness != "default":
                    self.values_frame_content_values['brightness var'].set(int(brightness))
                trigger_delay = self.config.values.get(self.confsect,'trigger_delay')
                if trigger_delay != "default":
                    self.values_frame_content_values['trigger_delay var'].set(float(trigger_delay))
                shutter = self.config.values.get(self.confsect,'shutter')
                if shutter != "default":
                    self.values_frame_content_values['shutter var'].set(int(shutter))
                trigger = self.config.values.get(self.confsect,'trigger')
                if trigger != "default":
                    self.values_frame_content_values['trigger var'].set(int(trigger))
                gain = self.config.values.get(self.confsect,'gain')
                if gain != "default":
                    self.values_frame_content_values['gain var'].set(int(gain))
                gamma = self.config.values.get(self.confsect,'gamma')
                if gamma != "default":
                    self.values_frame_content_values['gamma var'].set(int(gamma))
                exposure = self.config.values.get(self.confsect,'exposure')
                if exposure != "default":
                    self.values_frame_content_values['exposure var'].set(int(exposure))
                if self.camera_pathes_exists_in_config:
                    self.set_recording_path()
                self.setvalues_command()

    def close_connection_command(self):
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.log.debug("try to disconnect to %s:%d" % (self.ip,self.port))
            self.live_view_running = False
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                self.log.debug("disconnected")
            except:
                self.log.debug("cannot disconnect")
            self.socket = None
        self.socketlock.release() # release the lock
        self.close_connection_button.configure(state=tkinter.DISABLED)
        self.quit_server_button.configure(state=tkinter.DISABLED)
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
        self.after_widget.after(5000,func=self.open_connection_button_normal) # call after 5000 milliseconds; camera server needs some time to shutdown

    def open_connection_button_normal(self):
        self.open_connection_button.configure(state=tkinter.NORMAL)
