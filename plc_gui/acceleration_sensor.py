"""gui for controlling acceleration sensor

Author: Daniel Mohr
Date: 2013-03-06, 2017-05-30
"""

import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk
import logging
import threading
import time
import tkinter

from . import plcclientserverclass

class acceleration_sensor(plcclientserverclass.socket_communication_class):
    """gui for acceleration sensor

    Author: Daniel Mohr
    Date: 2013-03-06, 2017-05-30
    """
    def myinit(self):
        self.log = logging.getLogger('plc.plc_gui.acceleration_sensor')
        self.after_widget = self.pw
        self.myservername = "acceleration_sensor_server"
        self.bufsize = self.config.values.getint(self.confsect,'recv_bufsize')
        self.updatethreadsleeptime = self.config.values.getfloat(self.confsect,'sleep')
        self.update_intervall = self.config.values.getfloat(self.confsect,'sleep')
        self.ip = self.config.values.get(self.confsect,'ip')
        self.port = self.config.values.getint(self.confsect,'port')
        self.sport = self.config.values.getint(self.confsect,'port')
        self.debug = 0
        self.maxg = self.config.values.getfloat(self.confsect,'maxg')
        self.actualvalue = None
        self.myi = int(self.confsect[len(self.confsect)-1])
        # server variables
        self.cmd = self.config.values.get(self.confsect,'server_command')
        self.start_server = self.config.values.getboolean(self.confsect,'start_server')
        self.dev = "-1"
        self.serialnumber = self.config.values.get(self.confsect,'SerialNumber')
        self.logfile = self.config.values.get(self.confsect,'server_logfile')
        self.datalogfile = self.config.values.get(self.confsect,'server_datalogfile')
        self.datalogformat = self.config.values.getint(self.confsect,'datalogformat')
        self.rf = self.config.values.get(self.confsect,'server_runfile')
        self.server_max_start_time = self.config.values.get(self.confsect,'server_max_start_time')
        # variables for the gui
        self.bwgraphics = self.config.values.getboolean(self.confsect,'bwgraphics')
        self.colorgraphics = self.config.values.getboolean(self.confsect,'colorgraphics')
        self.diagramgraphics = self.config.values.getboolean(self.confsect,'diagramgraphics')
        self.shadowlength = self.config.values.getint(self.confsect,'shadowlength')
        self.diagramlength = self.config.values.getint(self.confsect,'diagramlength')
        self.resolution = self.config.values.getint(self.confsect,'resolution')
        self.update_display_delay = self.config.values.getint(self.confsect,'update_display_delay')
        self.gui()

    def gui(self):
        self.isgui = True
        # gui
        self.main_window = self.pw
        self.frame1 = tkinter.Frame(self.main_window)
        self.frame1.pack()
        self.frame2 = tkinter.Frame(self.main_window)
        self.frame2.pack()
        self.frame3 = tkinter.Frame(self.main_window)
        self.frame3.pack()
        self.frame4 = tkinter.Frame(self.main_window)
        self.frame4.pack()
        self.frame5 = tkinter.Frame(self.main_window)
        self.frame5.pack()
        # control buttons
        self.start_button = tkinter.Button(self.frame1,command=self.start_request,text="connect",state=tkinter.NORMAL)
        self.start_button.pack(side=tkinter.LEFT)
        self.stop_button = tkinter.Button(self.frame1,command=self.stop_request,text="disconnect",state=tkinter.DISABLED)
        self.stop_button.pack(side=tkinter.LEFT)
        self.quit_server_button = tkinter.Button(self.frame1,command=self.quit_server_command,text="quit server",state=tkinter.DISABLED)
        self.quit_server_button.pack(side=tkinter.LEFT)
        # values
        if self.shadowlength < 2:
            self.shadowlength = 2
        if self.diagramlength < 2:
            self.diagramlength = 2
        self.rbuffer_n = int(max(self.shadowlength,self.diagramlength))
        self.rbuffer = self.rbuffer_n * [[0,0,0]]
        self.rbuffer = self.rbuffer_n * [[None,None,None]]
        self.rbuffer_i = 0
        self.acceleration_x_val = tkinter.StringVar()
        self.acceleration_x_val.set("0")
        self.acceleration_y_val = tkinter.StringVar()
        self.acceleration_y_val.set("0")
        self.acceleration_z_val = tkinter.StringVar()
        self.acceleration_z_val.set("0")
        self.acceleration_x_entry = tkinter.Entry(self.frame2,textvariable=self.acceleration_x_val,width=6)
        self.acceleration_x_entry.pack(side=tkinter.LEFT)
        self.acceleration_y_entry = tkinter.Entry(self.frame2,textvariable=self.acceleration_y_val,width=6)
        self.acceleration_y_entry.pack(side=tkinter.LEFT)
        self.acceleration_z_entry = tkinter.Entry(self.frame2,textvariable=self.acceleration_z_val,width=6)
        self.acceleration_z_entry.pack(side=tkinter.LEFT)
        self.show_width = 10
        self.show_height = 20
        self.show_x_pic_draft = PIL.Image.new("RGB",(self.show_width,self.show_height),color=(0,0,0))
        self.show_x_img = PIL.ImageTk.PhotoImage("RGB",(self.show_width,self.show_height))
        self.show_x_img.paste(self.show_x_pic_draft)
        self.show_x_label = tkinter.Label(self.frame2,image=self.show_x_img)
        self.show_x_label.pack(side=tkinter.LEFT)
        self.show_y_pic_draft = PIL.Image.new("RGB",(self.show_width,self.show_height),color=(0,0,0))
        self.show_y_img = PIL.ImageTk.PhotoImage("RGB",(self.show_width,self.show_height))
        self.show_y_img.paste(self.show_y_pic_draft)
        self.show_y_label = tkinter.Label(self.frame2,image=self.show_y_img)
        self.show_y_label.pack(side=tkinter.LEFT)
        self.show_z_pic_draft = PIL.Image.new("RGB",(self.show_width,self.show_height),color=(0,0,0))
        self.show_z_img = PIL.ImageTk.PhotoImage("RGB",(self.show_width,self.show_height))
        self.show_z_img.paste(self.show_z_pic_draft)
        self.show_z_label = tkinter.Label(self.frame2,image=self.show_z_img)
        self.show_z_label.pack(side=tkinter.LEFT)
        # graphics
        if self.shadowlength > 2:
            self.shadow = True
        else:
            self.shadow = False
        self.x_y_width = self.resolution
        self.x_y_height = self.resolution
        self.x_y_dx = int(self.x_y_width*0.02)
        self.x_y_dy = int(self.x_y_height*0.02)
        self.x_z_width = self.resolution
        self.x_z_height = self.resolution
        self.x_z_dx = int(self.x_z_width*0.02)
        self.x_z_dy = int(self.x_z_height*0.02)
        # graphics gui
        self.pic_x_y = None
        self.x_y_img = None
        self.x_y_label = None
        self.pic_x_z = None
        self.x_z_img = None
        self.x_z_label = None
        if self.bwgraphics:
            self.create_gui_picture()
        # color graphics
        if self.shadowlength > 2:
            self.c_shadow = True
        else:
            self.c_shadow = False
        self.c_x_y_width = self.resolution
        self.c_x_y_height = self.resolution
        self.c_x_y_dx = int(self.c_x_y_width*0.02)
        self.c_x_y_dy = int(self.c_x_y_height*0.02)
        self.c_x_z_width = self.resolution
        self.c_x_z_height = self.resolution
        self.c_x_z_dx = int(self.c_x_z_width*0.02)
        self.c_x_z_dy = int(self.c_x_z_height*0.02)
        # color graphics gui
        self.c_pic_x_y = None
        self.c_x_y_img = None
        self.c_x_y_label = None
        self.c_pic_x_z = None
        self.c_x_z_img = None
        self.c_x_z_label = None
        if self.colorgraphics:
            self.c_create_gui_picture()
        # diagram graphics
        if self.diagramgraphics:
            self.diagram_width = 2*self.resolution
            self.diagram_height = self.resolution
            self.create_gui_diagram()
        self.reading_update_lock = threading.Lock()
        self.reading_last = time.time()
        self.update_display_last = time.time()
        self.update_display_id =  self.after_widget.after(1,self.update_display)

    def extern_update_start(self,extern_stringvar=None,notebook=None,notebookindex=None,notebookextern=0):
        self.update_extern_delay = self.config.values.get(self.confsect,'update_extern_delay')
        self.extern_update_lock = threading.Lock()
        self.extern_update_id = None
        self.extern_stringvar = extern_stringvar
        self.notebook = notebook
        self.notebookindex = notebookindex
        self.notebookextern = notebookextern
        self.update_img = True
        self.extern_update_running = True
        self.extern_update_id = self.after_widget.after(self.update_extern_delay,self.extern_update)

    def extern_update(self):
        self.extern_update_lock.acquire() # lock
        #self.extern_stringvar.set("%f" % time.time())
        # acc%d=(?.??,?.??,?.??)
        if self.actualvalue != None:
            [xr,yr,zr] = self.actualvalue[0:3]
            [x,y,z] = self.raw2gs(xr,yr,zr,self.maxg)
            self.extern_stringvar.set("acc%d=(%+1.2f,%+1.2f,%+1.2f)" % (self.myi,x,y,z))
        if self.extern_update_running:
            self.extern_update_id = self.after_widget.after(self.update_extern_delay,self.extern_update)
        self.extern_update_lock.release() # release the lock


    def create_gui_picture(self):
        self.pic_x_y = self.create_picture_draft(self.x_y_width,self.x_y_height,self.x_y_dx,self.x_y_dy,"x","y")
        self.x_y_img = PIL.ImageTk.PhotoImage("L",(self.x_y_width,self.x_y_height))
        self.x_y_img.paste(self.pic_x_y)
        self.x_y_label = tkinter.Label(self.frame3,image=self.x_y_img)
        self.x_y_label.pack(side=tkinter.LEFT)
        self.pic_x_z = self.create_picture_draft(self.x_z_width,self.x_z_height,self.x_y_dx,self.x_y_dy,"x","z")
        self.x_z_img = PIL.ImageTk.PhotoImage("L",(self.x_z_width,self.x_z_height))
        self.x_z_img.paste(self.pic_x_z)
        self.x_z_label = tkinter.Label(self.frame3,image=self.x_z_img)
        self.x_z_label.pack(side=tkinter.LEFT)

    def c_create_gui_picture(self):
        self.c_pic_x_y = self.c_create_picture_draft(self.c_x_y_width,self.c_x_y_height,self.c_x_y_dx,self.c_x_y_dy,"x","y")
        self.c_x_y_img = PIL.ImageTk.PhotoImage("RGB",(self.c_x_y_width,self.c_x_y_height))
        self.c_x_y_img.paste(self.c_pic_x_y)
        self.c_x_y_label = tkinter.Label(self.frame4,image=self.c_x_y_img)
        self.c_x_y_label.pack(side=tkinter.LEFT)
        self.c_pic_x_z = self.c_create_picture_draft(self.c_x_z_width,self.c_x_z_height,self.c_x_y_dx,self.c_x_y_dy,"x","z")
        self.c_x_z_img = PIL.ImageTk.PhotoImage("RGB",(self.c_x_z_width,self.c_x_z_height))
        self.c_x_z_img.paste(self.c_pic_x_z)
        self.c_x_z_label = tkinter.Label(self.frame4,image=self.c_x_z_img)
        self.c_x_z_label.pack(side=tkinter.LEFT)

    def create_gui_diagram(self):
        self.diagram_pic_draft = self.create_diagram_pic_draft()
        self.diagram_img = PIL.ImageTk.PhotoImage("RGB",(self.diagram_width,self.diagram_height))
        self.diagram_img.paste(self.diagram_pic_draft)
        self.diagram_label = tkinter.Label(self.frame5,image=self.diagram_img)
        self.diagram_label.pack()

    def create_picture_draft(self,width,height,dx,dy,xn,yn):
        # create picture draft
        pic = PIL.Image.new("L",(width,height),color=0)
        draw = PIL.ImageDraw.Draw(pic)
        r = 1.0
        color = 50
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=0.5*color)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        r = 0.75
        color = 100
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=0.5*color)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        r = 0.5
        color = 150
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=0.5*color)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        color = 150
        draw.line(( 0,0,
                    width,height ),
                  fill=color)
        draw.line(( 0,height,
                    width,0 ),
                  fill=color)
        r = 0.25
        color = 200
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=0.5*color)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        color = 200
        draw.line(( 0,0,
                    width,height ),
                  fill=color)
        draw.line(( 0,height,
                    width,0 ),
                  fill=color)
        (tx,ty) = draw.textsize(xn)
        draw.text((int(width/2.0-tx/2.0),height-ty-1),xn,fill=200)
        (tx,ty) = draw.textsize(yn)
        draw.text((2,int(height/2.0-ty/2.0)),yn,fill=200)
        del draw
        return pic.copy()

    def c_create_picture_draft(self,width,height,dx,dy,xn,yn):
        # create color picture draft
        pic = PIL.Image.new("RGB",(width,height),color=(0,0,0))
        draw = PIL.ImageDraw.Draw(pic)
        r = 1.0
        color = (50,50,50)
        color2 = (25,25,25)
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=color2)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        r = 0.75
        color = (100,100,100)
        color2 = (50,50,50)
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=color2)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        r = 0.5
        color = (150,150,150)
        color2 = (75,75,75)
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=color2)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        color = (150,150,150)
        draw.line(( 0,0,
                    width,height ),
                  fill=color)
        draw.line(( 0,height,
                    width,0 ),
                  fill=color)
        r = 0.25
        color = (200,200,200)
        color2 = (100,100,100)
        xx1 = int(((width-2*dx)/2.0) * (-1*r) + ((width-2*dx)/2.0+dx))
        yy1 = int(((height-2*dy)/2.0) * (-1*r) + ((height-2*dy)/2.0+dy))
        xx2 = int(((width-2*dx)/2.0) * (1*r) + ((width-2*dx)/2.0+dx))
        yy2 = int(((height-2*dy)/2.0) * (1*r) + ((height-2*dy)/2.0+dy))
        draw.ellipse((xx1,yy1,xx2,yy2),fill=color2)
        draw.line(( xx1,yy1,
                    xx2,yy1 ),
                  fill=color)
        draw.line(( xx1,yy2,
                    xx2,yy2 ),
                  fill=color)
        draw.line(( xx1,yy1,
                    xx1,yy2 ),
                  fill=color)
        draw.line(( xx2,yy1,
                    xx2,yy2 ),
                  fill=color)
        t = "% 1.2f g" % (r*self.maxg)
        xx1 = int(width/2.0 - draw.textsize(t)[0]/2.0)
        draw.text((xx1,yy1),t,fill=color)
        draw.line(( 0,0,
                    width,height ),
                  fill=color)
        draw.line(( 0,height,
                    width,0 ),
                  fill=color)
        (tx,ty) = draw.textsize(xn)
        draw.text((int(width/2.0-tx/2.0),height-ty-1),xn,fill=(200,200,200))
        (tx,ty) = draw.textsize(yn)
        draw.text((2,int(height/2.0-ty/2.0)),yn,fill=(200,200,200))
        del draw
        return pic.copy()

    def create_diagram_pic_draft(self):
        pic = PIL.Image.new("RGB",(self.diagram_width,self.diagram_height),color=(0,0,0))
        draw = PIL.ImageDraw.Draw(pic)
        color = (200,200,200)
        f = 0.0
        yy = int(self.diagram_height/2 + f * self.diagram_height/2)
        draw.line((0,yy,self.diagram_width,yy),fill=color,width=2)
        draw.text((0,yy),"% 1.2f g" % (f*self.maxg))
        color = (150,150,150)
        f = 0.25
        yy = int(self.diagram_height/2 + f * self.diagram_height/2)
        draw.line((0,yy,self.diagram_width,yy),fill=color)
        draw.text((0,yy),"% 1.2f g" % (-f*self.maxg))
        yy = int(self.diagram_height/2 - f * self.diagram_height/2)
        draw.line((0,yy,self.diagram_width,yy),fill=color)
        draw.text((0,yy),"% 1.2f g" % (f*self.maxg))
        color = (100,100,100)
        f = 0.5
        yy = int(self.diagram_height/2 + f * self.diagram_height/2)
        draw.line((0,yy,self.diagram_width,yy),fill=color)
        draw.text((0,yy),"% 1.2f g" % (-f*self.maxg))
        yy = int(self.diagram_height/2 - f * self.diagram_height/2)
        draw.line((0,yy,self.diagram_width,yy),fill=color)
        draw.text((0,yy),"% 1.2f g" % (f*self.maxg))
        color = (50,50,50)
        f = 0.75
        yy = int(self.diagram_height/2 + f * self.diagram_height/2)
        draw.line((0,yy,self.diagram_width,yy),fill=color)
        draw.text((0,yy),"% 1.2f g" % (-f*self.maxg))
        yy = int(self.diagram_height/2 - f * self.diagram_height/2)
        draw.line((0,yy,self.diagram_width,yy),fill=color)
        draw.text((0,yy),"% 1.2f g" % (f*self.maxg))
        #draw.text((int(self.diagram_width/2 - 60),10),"-%1.2f g < " % self.maxg,fill=(255,255,255))
        t = "-%1.2f g < x < %1.2f g" % (self.maxg,self.maxg)
        draw.text((int(1*self.diagram_width/4.0-draw.textsize(t)[0]/2.0),10),t,fill=(255,0,0))
        t = "-%1.2f g < y < %1.2f g" % (self.maxg,self.maxg)
        draw.text((int(2*self.diagram_width/4.0-draw.textsize(t)[0]/2.0),10),t,fill=(0,255,0))
        t = "-%1.2f g < z < %1.2f g" % (self.maxg,self.maxg)
        draw.text((int(3*self.diagram_width/4.0-draw.textsize(t)[0]/2.0),10),t,fill=(0,0,255))
        #draw.text((int(self.diagram_width/2 + 20),10),"< %1.2f g" % self.maxg,fill=(255,255,255))
        del draw
        return pic

    def update_display(self):
        if self.update_display_id:
            self.after_widget.after_cancel(self.update_display_id)
            self.update_display_id = None
        self.reading_update_lock.acquire() # lock
        if self.actualvalue:
            if self.update_display_last < self.reading_last:
                self.update_display_last = time.time()
                [xr,yr,zr] = self.actualvalue[0:3]
                self.rbuffer[self.rbuffer_i] = [xr,yr,zr]
                self.rbuffer_i = (self.rbuffer_i+1)%self.rbuffer_n
                [x,y,z] = self.raw2gs(xr,yr,zr,self.maxg)
                self.acceleration_x_val.set("%+1.3f" % x)
                self.acceleration_y_val.set("%+1.3f" % y)
                self.acceleration_z_val.set("%+1.3f" % z)
                # pictures
                if self.notebook != None:
                    sn = self.notebook.select()
                    sni = self.notebook.index(sn)
                    if sni == self.notebookindex:
                        self.update_img = True
                    elif sni == self.notebookextern:
                        self.update_img = False
                if self.update_img:
                    self.create_show_pictures(xr,yr,zr,x,y,z)
                    if self.bwgraphics:
                        self.create_actual_pictures(xr,yr,zr)
                    if self.colorgraphics:
                        self.c_create_actual_pictures(xr,yr,zr)
                    if self.diagramgraphics:
                        self.create_actual_diagram(xr,yr,zr)
        self.reading_update_lock.release() # unlock
        self.update_display_id =  self.after_widget.after(self.update_display_delay,self.update_display)

    def correct_state_intern(self):
        if self.isgui:
            if (self.socket != None):
                self.start_button.configure(state=tkinter.DISABLED)
                self.stop_button.configure(state=tkinter.NORMAL)
                self.quit_server_button.configure(state=tkinter.NORMAL)
            else:
                self.start_button.configure(state=tkinter.NORMAL)
                self.stop_button.configure(state=tkinter.DISABLED)
                self.quit_server_button.configure(state=tkinter.DISABLED)

    def quit(self):
        try:
            self.log.info("shutdown and close connection")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass
        self.socket = None

    def quit_server_command(self):
        self.running = False
        self.updatethreadrunning = False
        time.sleep(0.001)
        self.lock.acquire() # lock
        if self.socket != None:
            self.log.info("quit server and disconnect")
            self.send_data_to_socket(self.socket,"quit")
            self.lock.release() # unlock
            self.stop()
        else:
            self.lock.release() # unlock
        self.correct_state_intern()

    def picture_value_position(self,l,d,x):
        return int(((l-2*d)/2.0) * float(x - 2**13) / 2**13 + ((l-2*d)/2.0+d))

    def picture_value_position2(self,l,d,x):
        return int(((l-2*d)/2.0) * float(-x + 2**13) / 2**13 + ((l-2*d)/2.0+d))

    def create_actual_picture(self,pic,width,dx,x,height,dy,y,shadow,i1,i2):
        dc = 255
        if pic.mode == "L":
            color = dc
        else:
            color = (dc,0,0)
        draw = PIL.ImageDraw.Draw(pic)
        if shadow:
            xxo = None
            yyo = None
            s = float(dc) / self.shadowlength
            for i in range(1,self.shadowlength):
                ii = self.shadowlength-i
                a = self.rbuffer[(self.rbuffer_i-ii)%self.rbuffer_n]
                xs = a[i1]
                if xs != None:
                    ys = a[i2]
                    c = int(dc - ii*s)
                    if pic.mode == "L":
                        color = c
                    else:
                        color = (c,0,0)
                    xx = self.picture_value_position(width,dx,xs)
                    if i2 == 2:
                        yy = self.picture_value_position2(height,dy,ys)
                    else:
                        yy = self.picture_value_position(height,dy,ys)
                    if xxo != None:
                        draw.line((xxo,yyo,xx,yy),fill=color)
                    xxo = xx
                    yyo = yy
        xx = self.picture_value_position(width,dx,x)
        if i2 == 2:
            yy = self.picture_value_position2(height,dy,y)
        else:
            yy = self.picture_value_position(height,dy,y)
        draw.line(( xx-dx,yy,
                    xx+dx,yy ),
                  fill=color,width=2)
        draw.line(( xx,yy-dy,
                    xx,yy+dy ),
                  fill=color,width=2)
        del draw
        return pic

    def create_actual_pictures(self,xr,yr,zr):
        # create actual picture
        pic1 = self.create_actual_picture(self.pic_x_y.copy(),self.x_y_width,self.x_y_dx,xr,self.x_y_height,self.x_y_dy,yr,self.shadow,0,1)
        self.x_y_img.paste(pic1)
        pic2 = self.create_actual_picture(self.pic_x_z.copy(),self.x_z_width,self.x_z_dx,xr,self.x_z_height,self.x_z_dy,zr,self.shadow,0,2)
        self.x_z_img.paste(pic2)

    def c_create_actual_pictures(self,xr,yr,zr):
        # create actual color picture
        pic1 = self.create_actual_picture(self.c_pic_x_y.copy(),self.c_x_y_width,self.c_x_y_dx,xr,self.c_x_y_height,self.c_x_y_dy,yr,self.c_shadow,0,1)
        self.c_x_y_img.paste(pic1)
        pic2 = self.create_actual_picture(self.c_pic_x_z.copy(),self.c_x_z_width,self.c_x_z_dx,xr,self.c_x_z_height,self.c_x_z_dy,zr,self.c_shadow,0,2)
        self.c_x_z_img.paste(pic2)

    def create_actual_diagram(self,xr,yr,zr):
        # create actual diagram
        pic = self.diagram_pic_draft.copy()
        s = float(self.diagram_width) / self.diagramlength
        to = None
        xxo = None
        yyo = None
        zzo = None
        draw = PIL.ImageDraw.Draw(pic)
        for i in range(self.diagramlength):
            ii = self.diagramlength-i
            t = int(self.diagram_width - ii*s)
            [x,y,z] = self.rbuffer[(self.rbuffer_i-ii)%self.rbuffer_n]
            if x != None:
                xx = int((self.diagram_height/2) + (self.diagram_height/2) * float(-x + 2**13) / 2**13)
                yy = int((self.diagram_height/2) + (self.diagram_height/2) * float(y - 2**13) / 2**13)
                zz = int((self.diagram_height/2) + (self.diagram_height/2) * float(-z + 2**13) / 2**13)
                if to != None:
                    color = (255,0,0)
                    draw.line((to,xxo,t,xx),fill=color)
                    color = (0,255,0)
                    draw.line((to,yyo,t,yy),fill=color)
                    color = (0,0,255)
                    draw.line((to,zzo,t,zz),fill=color)
                to = t
                xxo = xx
                yyo = yy
                zzo = zz
                if ii == 1:
                    [xg,yg,zg] = self.raw2gs(x,y,z,self.maxg)
                    tx = "% 1.2f g" % xg
                    txw = draw.textsize(tx)[0]
                    ty = "% 1.2f g" % yg
                    tyw = draw.textsize(ty)[0]
                    tz = "% 1.2f g" % zg
                    tzw = draw.textsize(tz)[0]
                    draw.text((t-txw-tyw-tzw,xx),tx,fill = (255,150,150))
                    draw.text((t-tyw-tzw,yy),ty,fill = (150,255,150))
                    draw.text((t-tzw,zz),tz,fill = (150,150,255))
        del draw
        self.diagram_img.paste(pic)

    def create_show_pictures(self,xr,yr,zr,x,y,z):
        pic = self.show_x_pic_draft.copy()
        draw = PIL.ImageDraw.Draw(pic)
        xx = int((self.show_height/2) + (self.show_height/2) * float(-xr + 2**13) / 2**13)
        w = 3
        if abs(x) < 0.1:
            w = 1
        draw.line((0,xx,self.show_width-1,xx),fill=(255,150,150),width=w)
        del draw
        self.show_x_img.paste(pic)
        pic = self.show_y_pic_draft.copy()
        draw = PIL.ImageDraw.Draw(pic)
        yy = int((self.show_height/2) + (self.show_height/2) * float(-yr + 2**13) / 2**13)
        w = 3
        if abs(y) < 0.1:
            w = 1
        draw.line((0,yy,self.show_width-1,yy),fill=(150,255,150),width=w)
        del draw
        self.show_y_img.paste(pic)
        pic = self.show_z_pic_draft.copy()
        draw = PIL.ImageDraw.Draw(pic)
        zz = int((self.show_height/2) + (self.show_height/2) * float(-zr + 2**13) / 2**13)
        w = 3
        if abs(z) < 0.1:
            w = 1
        draw.line((0,zz,self.show_width-1,zz),fill=(150,150,255),width=w)
        del draw
        self.show_z_img.paste(pic)

    def raw2gs(self,xr,yr,zr,maxg):
        x = self.raw2g(xr,maxg)
        y = -self.raw2g(yr,maxg) # y is inverted
        z = self.raw2g(zr,maxg)
        return [x,y,z]

    def raw2g(self,g,maxvalue):
        return maxvalue * float(g - 2**13) / 2**13
