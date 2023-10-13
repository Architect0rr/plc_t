#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-04-24, 2014-07-22, 2017-05-30

__acceleration_sensor_client_date__ = "2017-05-30"
__acceleration_sensor_client_version__ = __acceleration_sensor_client_date__

import argparse
import pickle
import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk
import logging
import logging.handlers
import re
import socket
import time
import tkinter
import threading

import plc_tools.plc_socket_communication

class gui(plc_tools.plc_socket_communication.tools_for_socket_communication):
    def __init__(self,args,log):
        self.send_data_to_socket_lock = threading.Lock()
        self.bufsize = 4096 # read/receive Bytes at once
        self.ip = args.ip
        self.port = args.port
        self.debug = args.debug
        self.bwgraphics = bool(args.bwgraphics)
        self.colorgraphics = bool(args.colorgraphics)
        self.diagramgraphics = bool(args.diagram)
        self.maxg = args.maxg
        self.sleep = args.sleep
        self.log = log
        self.socket = None
        self.actualvalue = None
        self.lock = threading.Lock()
        self.running = False
        self.main_window = tkinter.Tk()
        self.main_window.title("acceleration_sensor_client.py (%s:%d)" % (self.ip,self.port))
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
        self.open_connection_button = tkinter.Button(self.frame1,command=self.open_connection_command,text="connect",state=tkinter.NORMAL)
        self.open_connection_button.pack(side=tkinter.LEFT)
        self.close_connection_button = tkinter.Button(self.frame1,command=self.close_connection_command,text="disconnect",state=tkinter.DISABLED)
        self.close_connection_button.pack(side=tkinter.LEFT)
        self.quit_server_button = tkinter.Button(self.frame1,command=self.quit_server_command,text="quit server",state=tkinter.DISABLED)
        self.quit_server_button.pack(side=tkinter.LEFT)
        # values
        if args.shadowlength < 2:
            args.shadowlength = 2
        self.shadowlength = args.shadowlength
        if args.diagramlength < 2:
            args.diagramlength = 2
        self.diagramlength = args.diagramlength
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
        self.x_y_width = args.resolution
        self.x_y_height = args.resolution
        self.x_y_dx = int(self.x_y_width*0.02)
        self.x_y_dy = int(self.x_y_height*0.02)
        self.x_z_width = args.resolution
        self.x_z_height = args.resolution
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
        self.c_x_y_width = args.resolution
        self.c_x_y_height = args.resolution
        self.c_x_y_dx = int(self.c_x_y_width*0.02)
        self.c_x_y_dy = int(self.c_x_y_height*0.02)
        self.c_x_z_width = args.resolution
        self.c_x_z_height = args.resolution
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
            self.diagram_width = 2*args.resolution
            self.diagram_height = args.resolution
            self.create_gui_diagram()
        self.reading_update_lock = threading.Lock()
        self.reading_last = time.time()
        self.update_display_last = time.time()
        self.update_display_delay = args.update_display_delay
        self.update_display_id =  self.main_window.after(1,self.update_display)

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

    def start(self):
        self.main_window.mainloop()
        self.quit()

    def update_display(self):
        if self.update_display_id:
            self.main_window.after_cancel(self.update_display_id)
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
                self.create_show_pictures(xr,yr,zr,x,y,z)
                if self.bwgraphics:
                    self.create_actual_pictures(xr,yr,zr)
                if self.colorgraphics:
                    self.c_create_actual_pictures(xr,yr,zr)
                if self.diagramgraphics:
                    self.create_actual_diagram(xr,yr,zr)
        time.sleep(self.sleep)
        self.reading_update_lock.release() # unlock
        self.update_display_id =  self.main_window.after(self.update_display_delay,self.update_display)

    def quit(self):
        self.lock.acquire() # lock i
        try:
            self.log.info("shutdown and close connection")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass
        self.lock.release() # unlock i
        try:
            self.main_window.destroy()
        except:
            pass

    def send_data_to_socket(self,s,msg):
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = s.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def get_actualvalues(self):
        self.lock.acquire() # lock i
        if self.socket != None:
            self.send_data_to_socket(self.socket,"getact")
            self.actualvalue = self.receive_data_from_socket(self.socket,self.bufsize)
        self.lock.release() # unlock i

    def get_version(self):
        self.lock.acquire() # lock i
        if self.socket != None:
            self.send_data_to_socket(self.socket,"version")
            data = self.receive_data_from_socket(self.socket,self.bufsize)
            self.log.info("server-version: %s" % data)
        self.lock.release() # unlock i

    def open_connection_command(self):
        self.log.debug("connect to %s:%d" % (self.ip,self.port))
        self.lock.acquire() # lock
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip,self.port))
            self.open_connection_button.configure(state=tkinter.DISABLED)
            self.close_connection_button.configure(state=tkinter.NORMAL)
            self.quit_server_button.configure(state=tkinter.NORMAL)
            self.log.debug("connected")
            self.running = True
            self.reading_thread = threading.Thread(target=self.reading)
            self.reading_thread.daemon = True # exit thread when the main thread terminates
            self.reading_thread.start()
        except:
            self.socket = None
            self.log.warning("cannot connect to %s:%d" % (self.ip,self.port))
        self.lock.release() # unlock

    def close_connection_command(self):
        self.lock.acquire() # lock
        self.log.debug("disconnect to %s:%d" % (self.ip,self.port))
        self.running = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.socket = None
        except:
            self.socket = None
        self.lock.release() # unlock
        self.open_connection_button.configure(state=tkinter.NORMAL)
        self.close_connection_button.configure(state=tkinter.DISABLED)
        self.quit_server_button.configure(state=tkinter.DISABLED)

    def quit_server_command(self):
        self.running = False
        self.lock.acquire() # lock
        if self.socket != None:
            self.log.info("quit server and disconnect")
            self.send_data_to_socket(self.socket,"quit")
            self.lock.release() # unlock
            self.close_connection_command()
        else:
            self.lock.release() # unlock

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

    def reading(self):
        i = 0
        t0 = time.time()
        j = 0
        self.log.debug("start reading")
        while self.running:
            self.reading_update_lock.acquire() # lock
            self.get_actualvalues()
            if self.actualvalue[3] != j:
                self.reading_last = time.time()
                # loop infos
                i = i + 1
                if i%125 == 0:
                    t1 = time.time()
                    i = 0
                    self.log.debug("read from server 125 values in %f seconds" % (t1-t0))
                    t0 = time.time()
            j = self.actualvalue[3]
            self.reading_update_lock.release() # unlock
            time.sleep(self.sleep)

    def raw2gs(self,xr,yr,zr,maxg):
        x = self.raw2g(xr,maxg)
        y = -self.raw2g(yr,maxg) # y is inverted
        z = self.raw2g(zr,maxg)
        return [x,y,z]

    def raw2g(self,g,maxvalue):
        return maxvalue * float(g - 2**13) / 2**13

def main():
    parser = argparse.ArgumentParser(
        description='acceleration_sensor_client is a client to speak with the socket server acceleration_sensor_server.py to control the acceleration sensor.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__acceleration_sensor_client_date__,help),
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
                        default=15123,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p. default: 15123',
                        metavar='p')
    parser.add_argument('-bwgraphics',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='bwgraphics',
                        help='Setting this flag to 1 enables black/white graphics. default: 1',
                        metavar='i')
    parser.add_argument('-colorgraphics',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='colorgraphics',
                        help='Setting this flag to 1 enables color graphics. default: 0',
                        metavar='i')
    parser.add_argument('-diagram',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='diagram',
                        help='Setting this flag to 1 enables the diagram graphics. default: 0',
                        metavar='i')
    parser.add_argument('-resolution',
                        nargs=1,
                        default=400,
                        type=int,
                        required=False,
                        dest='resolution',
                        help='Set the width and height of the graphics to p pixel. default: 400',
                        metavar='p')
    parser.add_argument('-sleep',
                        nargs=1,
                        default=0.035,
                        type=float,
                        required=False,
                        dest='sleep',
                        help='Set the sleep time in seconds between reading new values from the server. Shorter than 0.008 is useless. default: 0.035',
                        metavar='s')
    parser.add_argument('-shadow',
                        nargs=1,
                        default=16,
                        type=int,
                        required=False,
                        dest='shadowlength',
                        help='Set length of the shadow. default: 16',
                        metavar='n')
    parser.add_argument('-diagramlength',
                        nargs=1,
                        default=320,
                        type=int,
                        required=False,
                        dest='diagramlength',
                        help='Set length of the diagram. default: 320',
                        metavar='n')
    parser.add_argument('-maxg',
                        nargs=1,
                        default=2.0,
                        type=float,
                        required=False,
                        dest='maxg',
                        help='Set the measurement range in g. default 2 for +-2g',
                        metavar='x')
    parser.add_argument('-update_display_delay',
                        nargs=1,
                        default=6,
                        type=int,
                        required=False,
                        dest='update_display_delay',
                        help='Set the minimum time delay between displaying new values. default: 6',
                        metavar='a')
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
    if not isinstance(args.bwgraphics,int):
        args.bwgraphics = args.bwgraphics[0]
    if not isinstance(args.colorgraphics,int):
        args.colorgraphics = args.colorgraphics[0]
    if not isinstance(args.diagram,int):
        args.diagram = args.diagram[0]
    if not isinstance(args.resolution,int):
        args.resolution = args.resolution[0]
    if not isinstance(args.sleep,float):
        args.sleep = args.sleep[0]
    if not isinstance(args.diagramlength,int):
        args.diagramlength = args.diagramlength[0]
    if not isinstance(args.shadowlength,int):
        args.shadowlength = args.shadowlength[0]
    if not isinstance(args.update_display_delay,int):
        args.update_display_delay = args.update_display_delay[0]
    if not isinstance(args.maxg,float):
        args.maxg = args.maxg[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    # logging
    log = logging.getLogger('asc')
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
