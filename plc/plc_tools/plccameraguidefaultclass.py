"""default functions of a class for a gui for a camera

Author: Daniel Mohr
Date: 2013-10-28, 2017-05-30
"""

import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk
import numpy
import re
import threading
import time
import tkinter

from . import plc_socket_communication

class camera(plc_socket_communication.tools_for_socket_communication):
    """default functions of a class for a gui for a camera

    Author: Daniel Mohr
    Date: 2013-10-28, 2017-05-30
    """
    def __init__(self):
        self.send_data_to_socket_lock = threading.Lock()

    def __del__(self):
        try:
            if self.update_picture_label_id:
                self.log.debug("stop picture update")
                self.after_widget.after_cancel(self.update_picture_label_id)
                self.update_picture_label_id = None
        except: pass
        try:
            self.log.debug("stop live view")
            self.stop_live_view()
        except: pass
        try:
            self.close_connection_command()
        except: pass

    def create_histogram_checkbutton(self):
        if ((not self.live_view_running) and
            (self.histogram_create_var.get() == 1)):
            self.create_histogram()

    def create_histogram(self):
        self.create_histogram_lock.acquire() # lock
        if self.pic != None:
            if self.histogram_kind_value.get() == "horizontal sums":
                hist = list(numpy.array(self.pic).sum(1))
                totalbrightness = sum(hist)
            elif self.histogram_kind_value.get() == "vertical sums":
                hist = list(numpy.array(self.pic).sum(0))
                totalbrightness = sum(hist)
            else:
                hist = self.pic.histogram() # hist is a list
                totalbrightness = sum(list(numpy.array(self.pic).sum(0)))
            [width,height] = self.pic.size
            brightness = float(totalbrightness)/(255.0*width*height)
            self.histogram_total_brightness_var.set("brightness:\n%f" % brightness)
            self.histogram_pic = PIL.Image.new("L",(self.histogram_width,self.histogram_height),color=0)
            draw = PIL.ImageDraw.Draw(self.histogram_pic)
            lh = len(hist)
            xs = float(self.histogram_width)/lh
            ys = float(self.histogram_height)/max(hist)
            for i in range(lh):
                x = int(i*xs)
                y = self.histogram_height - int(hist[i]*ys)
                while x < int((i+1)*xs):
                    draw.line(( x,self.histogram_height,
                                x,y ),
                              fill=255)
                    x += 1
            del draw
            self.new_histogram_pic = True
        self.create_histogram_lock.release() # release the lock

    def setscale(self):
        self.scale = self.scalevar.get()
        self.swidth = int(self.scale*self.width)
        self.sheight = int(self.scale*self.height)
        self.picture_label_lock.acquire() # lock
        self.update_picture_label = True
        self.picture_label_lock.release() # release the lock

    def scalehalf(self):
        self.scale = 0.5 * self.scale
        self.swidth = int(self.scale*self.width)
        self.sheight = int(self.scale*self.height)
        self.scalevar.set(self.scale)
        self.picture_label_lock.acquire() # lock
        self.update_picture_label = True
        self.picture_label_lock.release() # release the lock

    def scaledouble(self):
        self.scale = 2.0 * self.scale
        self.swidth = int(self.scale*self.width)
        self.sheight = int(self.scale*self.height)
        self.scalevar.set(self.scale)
        self.picture_label_lock.acquire() # lock
        self.update_picture_label = True
        self.picture_label_lock.release() # release the lock

    def _create_picture_label(self):
        self.picture_label_lock.acquire() # lock
        self.log.debug("_create_picture_label %f" % time.time())
        if self.img != None:
            del self.img
            #self.img.__del__
        if self.movie_label != None:
            self.log.debug("destroy")
            self.movie_label.unbind(self.movie_label_bind_id0)
            self.movie_label.unbind(self.movie_label_bind_id1)
            self.movie_label.unbind(self.movie_label_bind_id2)
            self.movie_label.destroy()
        self.pic_lock.acquire() # lock
        try:
            gamma = float(self.gammavar.get())
            if 0.0 <= gamma and gamma <= 1000.0:
                self.gamma = gamma
        except: pass
        if self.display_kind_value.get() == self.display_kind_optionlist[1]: # highlight bright
            self.img = PIL.ImageTk.PhotoImage("P",(self.swidth,self.sheight),gamma=self.gamma)
            self.img_format = "P"
        else:
            self.img = PIL.ImageTk.PhotoImage("L",(self.swidth,self.sheight),gamma=self.gamma)
            self.img_format = "L"
        if self.pic != None:
            if self.crop:
                self.pic = self.pic.crop((self.crop_x_1,self.crop_y_1,
                                               self.crop_x_2,self.crop_y_2))
            self.pic = self.pic.resize((self.swidth,self.sheight))
            self.img.paste(self.pic) # this takes a long time
        self.movie_label = tkinter.Label(self.picture_canvas_frame,image=self.img,cursor='tcross')
        self.pic_lock.release() # release the lock
        self.movie_label.grid(column=0,row=3,columnspan=3)
        self.movie_label_bind_id0 = self.movie_label.bind("<Button-1>",self.movie_label_click)
        self.movie_label_bind_id1 = self.movie_label.bind("<ButtonRelease-1>",self.movie_label_release)
        self.movie_label_bind_id2 = self.movie_label.bind("<Button-3>",self.movie_label_crop_off)
        self.picture_label_lock.release() # release the lock

    def create_picture_label(self):
        if self.update_picture_label_id:
            self.after_widget.after_cancel(self.update_picture_label_id)
            self.update_picture_label_id = None
        self._create_picture_label()
        self.update_picture_label_id = self.after_widget.after(1,self.update_img)

    def update_img(self):
        """periodical update of the camera images in the gui

        Author: Daniel Mohr
        Date: 2013-02-26, 2017-05-30
        """
        self.update_img_lock.acquire() # lock
        if self.update_img_request_stop:
            self.update_img_request_stop = False
            self.after_widget.after(1,self.stop_live_view)
        #if self.update_picture_label_id:
        #    self.after_widget.after_cancel(self.update_picture_label_id)
        #    self.update_picture_label_id = None
        self.picture_label_lock.acquire() # lock
        if self.update_picture_label:
            self.update_picture_label = False
            self.picture_label_lock.release() # release the lock
            self._create_picture_label()
            self.picture_label_lock.acquire() # lock
        self.picture_label_lock.release() # release the lock
        if self.img_last_time <= self.img_time : # recieve time is newer
            if self.notebook != None:
                sn = self.notebook.select()
                sni = self.notebook.index(sn)
                if sni == self.notebookindex:
                    self.update_img_intern = True
                    self.update_img_extern = False
                elif sni == self.notebookextern:
                    self.update_img_intern = False
                    self.update_img_extern = True
            self.pic_lock.acquire() # lock
            self.pic = PIL.Image.fromarray(self.socket_pic_data['frame'])
            if self.histogram_create_var.get() == 1:
                self.create_histogram()
            [width,height] = self.pic.size
            self.pic_lock.release() # release the lock
            if (width != self.width) or (height != self.height):
                self.width = width
                self.height = height
                self.swidth = int(self.scale*self.width)
                self.sheight = int(self.scale*self.height)
                self._create_picture_label()
            self.picture_label_lock.acquire() # lock
            self.pic_lock.acquire() # lock
            if self.height != self.sheight:
                self.pic = self.pic.resize((self.swidth,self.sheight))
            if self.crop:
                self.pic = self.pic.crop((self.crop_x_1,self.crop_y_1,
                                               self.crop_x_2,self.crop_y_2))
                self.pic = self.pic.resize((self.swidth,self.sheight))
            if ((self.notebook == None) or self.update_img_intern):
                #self.log.debug("intern")
                if self.display_kind_value.get() == self.display_kind_optionlist[0]: # as is
                    if self.img_format == "P":
                        self.update_picture_label = True
                    else:
                        self.img.paste(self.pic) # this takes a long time
                elif self.display_kind_value.get() == self.display_kind_optionlist[1]: # highlight bright
                    # generate special color palette
                    if self.img_format == "L":
                        self.update_picture_label = True
                    else:
                        p = self.pic.copy()
                        p.putpalette(self.color_palette_highlight_bright)
                        self.img.paste(p) # this takes a long time
                # on many computers it is not possible to get 30 or more
            if (self.extern_img != None) and ((self.notebook == None) or self.update_img_extern):
                #self.log.debug("extern")
                self.extern_img.paste(self.pic.resize((self.extern_x,int(float(height)*float(self.extern_x)/float(width)))))
            self.pic_lock.release() # release the lock
            self.picture_label_lock.release() # release the lock
            self.img_last_time = time.time()
        if ((self.histogram_create_var.get() == 1) and
            ((self.notebook == None) or self.update_img_intern)):
            self.create_histogram_lock.acquire() # lock
            if self.new_histogram_pic:
                self.new_histogram_pic = False
                self.histogram_img.paste(self.histogram_pic)
            self.create_histogram_lock.release() # release the lock
        self.update_picture_label_id = self.after_widget.after(self.update_img_delay,self.update_img)
        self.update_img_lock.release() # release the lock

    def movie_label_click(self,event):
        self.log.debug("click at %d,%d" % (event.x,event.y))
        self.tcrop_x_1 = event.x
        self.tcrop_y_1 = event.y

    def movie_label_release(self,event):
        self.log.debug("release at %d,%d and will crop" % (event.x,event.y))
        self.tcrop_x_2 = max(event.x,self.tcrop_x_1)
        self.tcrop_x_1 = min(event.x,self.tcrop_x_1)
        self.tcrop_y_2 = max(event.y,self.tcrop_y_1)
        self.tcrop_y_1 = min(event.y,self.tcrop_y_1)
        if self.crop:
            self.crop = False
            x_1 = int( self.crop_x_1 +
                       ( (self.crop_x_2-self.crop_x_1) *
                         self.tcrop_x_1 / self.swidth ) )
            x_2 = int( self.crop_x_1 +
                       ( (self.crop_x_2-self.crop_x_1) *
                         self.tcrop_x_2 / self.swidth ) )
            y_1 = int( self.crop_y_1 +
                       ( (self.crop_y_2-self.crop_y_1) *
                         self.tcrop_y_1 / self.sheight ) )
            y_2 = int( self.crop_y_1 +
                       ( (self.crop_y_2-self.crop_y_1) *
                         self.tcrop_y_2 / self.sheight ) )
            self.crop_x_1 = x_1
            self.crop_x_2 = x_2
            self.crop_y_1 = y_1
            self.crop_y_2 = y_2
        else:
            self.crop = False
            self.crop_x_1 = self.tcrop_x_1
            self.crop_x_2 = self.tcrop_x_2
            self.crop_y_1 = self.tcrop_y_1
            self.crop_y_2 = self.tcrop_y_2
        self.crop_x_1 = max(0,min(self.crop_x_1,self.swidth))
        self.crop_x_2 = max(0,min(self.crop_x_2,self.swidth))
        self.crop_y_1 = max(0,min(self.crop_y_1,self.sheight))
        self.crop_y_2 = max(0,min(self.crop_y_2,self.sheight))
        if self.crop_x_1 == self.crop_x_2:
            if self.crop_x_2 == self.swidth:
                self.crop_x_1 -= 1
            else:
                self.crop_x_2 += 1
        if self.crop_y_1 == self.crop_y_2:
            if self.crop_y_2 == self.sheight:
                self.crop_y_1 -= 1
            else:
                self.crop_y_2 += 1
        self.crop = True

    def movie_label_crop_off(self,event):
        self.crop = False
        self.log.debug("crop off")

    def create_recording_path_frame(self):
        try:
            for i in self.recording_pathes_labels:
                i.destroy()
            for i in self.recording_pathes_entries:
                i.destroy()
        except:
            pass
        self.recording_pathes_labels = []
        self.recording_pathes_vals = []
        self.recording_pathes_entries = []
        i = 0
        for p in self.recording_pathes:
            self.recording_pathes_labels += [tkinter.Label(self.recording_path_frame,text="%d. recording path/prefix:" % (i+1))]
            self.recording_pathes_labels[i].grid(column=0,row=i)
            self.recording_pathes_vals += [tkinter.StringVar()]
            self.recording_pathes_vals[i].set(p)
            self.recording_pathes_entries += [tkinter.Entry(self.recording_path_frame,textvariable=self.recording_pathes_vals[i], width=20)]
            self.recording_pathes_entries[i].grid(column=1,row=i)
            i += 1

    def start(self):
        pass

    def quit(self):
        try:
            self.log.info("shutdown and close connection")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass

    def get_listcams_command(self):
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.log.debug("get listcams from the server")
            self.send_data_to_socket(self.socket,"listcams")
            self.camlist = self.receive_data_from_socket(self.socket,self.bufsize)
            self.guidlist = []
            self.guid_optionslist = []
            for l in self.camlist:
                self.guidlist += [l['guid']]
                self.guid_optionslist += ["%s %s (%s)" % (l['vendor'],l['model'],l['guid'])]
            if len(self.guid_optionslist) == 0:
                self.guid_optionslist = [" no guid found"]
            self.guid_optionmenu.destroy()
            self.guid_value.set(self.guid_optionslist[0])
            self.guid_optionmenu = tkinter.OptionMenu(self.guid_optionmenu_frame,self.guid_value,*self.guid_optionslist)
            self.guid_optionmenu.pack(side=tkinter.RIGHT)
            self.values_frame_content()
        self.socketlock.release() # release the lock

    def getvalues_command(self):
        self.getvalues_button.configure(state=tkinter.DISABLED)
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.log.debug("get values from the server")
            self.send_data_to_socket(self.socket,"getvalues")
            self.values = self.receive_data_from_socket(self.socket,self.bufsize)
            self.setvalues_button.configure(state=tkinter.NORMAL)
            self.values_frame_content()
        self.socketlock.release() # release the lock
        self.getvalues_button.configure(state=tkinter.NORMAL)

    def set_image_size(self):
        index = None
        if self.camlist != None:
            v = self.guid_value.get() # AVT Guppy F080B (2892819639808492)
            r = re.findall("\(([0-9]+)\)$",v)
            if r:
                guid = r[0]
                if guid in self.guidlist:
                    index = self.guidlist.index(guid)
                elif int(guid) in self.guidlist:
                    index = self.guidlist.index(int(guid))
        xmax = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][0]
        ymax = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][1]
        x = self.values_frame_content_values['x image_size'].get()
        x0 = self.values_frame_content_values['x image_position'].get()
        y = self.values_frame_content_values['y image_size'].get()
        y0 = self.values_frame_content_values['y image_position'].get()
        upx,upy = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['unit_position']
        if x + x0 > xmax:
            if x <= xmax:
                x0 = xmax - x
            else:
                x = xmax
                x0 = 0
        while x0%upx != 0:
            x0 += 1
            if x + x0 > xmax:
                x -= 1
        if y + y0 > ymax:
            if y <= ymax:
                y0 = ymax - y
            else:
                y = ymax
                y0 = 0
        while y0%upy != 0:
            y0 += 1
            if y + y0 > ymax:
                y -= 1
        self.values_frame_content_values['x image_size'].set(x)
        self.values_frame_content_values['x image_position'].set(x0)
        self.values_frame_content_values['y image_size'].set(y)
        self.values_frame_content_values['y image_position'].set(y0)

    def set_image_position(self):
        index = None
        if self.camlist != None:
            v = self.guid_value.get() # AVT Guppy F080B (2892819639808492)
            r = re.findall("\(([0-9]+)\)$",v)
            if r:
                guid = r[0]
                if guid in self.guidlist:
                    index = self.guidlist.index(guid)
                elif int(guid) in self.guidlist:
                    index = self.guidlist.index(int(guid))
        xmax = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][0]
        ymax = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][1]
        x = self.values_frame_content_values['x image_size'].get()
        x0 = self.values_frame_content_values['x image_position'].get()
        y = self.values_frame_content_values['y image_size'].get()
        y0 = self.values_frame_content_values['y image_position'].get()
        upx,upy = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['unit_position']
        if x + x0 > xmax:
            if x0 < xmax:
                x = xmax - x0
            else:
                x = 1
                x0 = xmax-1
        while x0%upx != 0:
            x0 += 1
            if x + x0 > xmax:
                x -= 1
        if y + y0 > ymax:
            if y0 <= ymax:
                y = ymax - y0
            else:
                y = 1
                y0 = ymax -1
        while y0%upy != 0:
            y0 += 1
            if y + y0 > ymax:
                y -= 1
        self.values_frame_content_values['x image_size'].set(x)
        self.values_frame_content_values['x image_position'].set(x0)
        self.values_frame_content_values['y image_size'].set(y)
        self.values_frame_content_values['y image_position'].set(y0)

    def values_frame_content(self):
        self.log.debug("create content for values_frame")
        index = None
        if self.camlist != None:
            v = self.guid_value.get() # AVT Guppy F080B (2892819639808492)
            r = re.findall("\(([0-9]+)\)$",v)
            if r:
                guid = r[0]
                if guid in self.guidlist:
                    index = self.guidlist.index(guid)
                elif int(guid) in self.guidlist:
                    index = self.guidlist.index(int(guid))
        self.log.debug("create content for values_frame 1")
        if (self.camlist != None) and (index != None):
            self.log.debug("create content for values_frame 2")
            # create content for values_frame
            for i in self.values_frame_content_objects:
                self.values_frame_content_objects[i].destroy()
            self.values_frame_content_objects = dict()
            self.values_frame_content_values = dict()
            r = 0
            # isospeed
            self.values_frame_content_objects['isospeed label 1'] = tkinter.Label(self.values_frame,text="isospeed:")
            self.values_frame_content_objects['isospeed label 1'].grid(column=0,row=r)
            self.values_frame_content_objects['isospeed label 2'] = tkinter.Label(self.values_frame,text="%s" % self.camlist[index]['isospeed'])
            self.values_frame_content_objects['isospeed label 2'].grid(column=1,row=r)
            r += 1
            # modes
            self.values_frame_content_objects['mode label'] = tkinter.Label(self.values_frame,text="mode:")
            self.values_frame_content_objects['mode label'].grid(column=0,row=r)
            self.values_frame_content_values['mode'] = tkinter.StringVar()
            i = 0
            if self.values != None:
                i = list(self.camlist[index]['modes'].keys()).index(self.values['mode'])
            self.values_frame_content_values['mode'].set(list(self.camlist[index]['modes'].keys())[i])
            self.values_frame_content_objects['mode optionmenu'] = tkinter.OptionMenu(self.values_frame,self.values_frame_content_values['mode'],*sorted(self.camlist[index]['modes'].keys()))
            self.values_frame_content_objects['mode optionmenu'].grid(column=1,row=r)
            self.values_frame_content_objects['mode button'] = tkinter.Button(self.values_frame,command=self.set_mode,text="set mode")
            self.values_frame_content_objects['mode button'].grid(column=2,row=r)
            r += 1
            # framerates
            if 'framerates' in list(self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()].keys()):
                self.values_frame_content_objects['framerate label'] = tkinter.Label(self.values_frame,text="framerate:")
                self.values_frame_content_objects['framerate label'].grid(column=0,row=r)
                self.values_frame_content_values['framerate'] = tkinter.StringVar()
                try:
                    i = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['framerates'].index(self.values['framerate'])
                except:
                    i = len(self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['framerates'])-1
                self.values_frame_content_values['framerate'].set(self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['framerates'][i])
                self.values_frame_content_objects['framerate optionmenu'] = tkinter.OptionMenu(self.values_frame,
                                                                                               self.values_frame_content_values['framerate'],
                                                                                               *sorted(self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['framerates']))
                self.values_frame_content_objects['framerate optionmenu'].grid(column=1,row=r)
                r += 1
            else: # FORMAT7_x
                # max_image_size
                self.values_frame_content_objects['max_image_size label 1'] = tkinter.Label(self.values_frame,text="max. image size:")
                self.values_frame_content_objects['max_image_size label 1'].grid(column=0,row=r)
                self.values_frame_content_objects['max_image_size label 2'] = tkinter.Label(self.values_frame,text="%dx%d" % (self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][0],self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][1]))
                self.values_frame_content_objects['max_image_size label 2'].grid(column=1,row=r)
                r += 1
                # image_size
                try:
                    x = self.values['image_size'][0]
                    y = self.values['image_size'][1]
                except:
                    x = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][0]
                    y = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][1]
                self.values_frame_content_objects['x - image_size label'] = tkinter.Label(self.values_frame,text="x - image size:")
                self.values_frame_content_objects['x - image_size label'].grid(column=0,row=r)
                self.values_frame_content_values['x image_size'] = tkinter.IntVar()
                self.values_frame_content_values['x image_size'].set(x)
                self.values_frame_content_objects['x - image_size entry'] = tkinter.Entry(self.values_frame,textvariable = self.values_frame_content_values['x image_size'],width=6)
                self.values_frame_content_objects['x - image_size entry'].grid(column=1,row=r)
                r += 1
                self.values_frame_content_objects['y - image_size label'] = tkinter.Label(self.values_frame,text="y - image size:")
                self.values_frame_content_objects['y - image_size label'].grid(column=0,row=r)
                self.values_frame_content_values['y image_size'] = tkinter.IntVar()
                self.values_frame_content_values['y image_size'].set(y)
                self.values_frame_content_objects['y - image_size entry'] = tkinter.Entry(self.values_frame,textvariable = self.values_frame_content_values['y image_size'],width=6)
                self.values_frame_content_objects['y - image_size entry'].grid(column=1,row=r)
                # set
                self.values_frame_content_objects['set image_size button'] = tkinter.Button(self.values_frame,command=self.set_image_size,text="set image size")
                self.values_frame_content_objects['set image_size button'].grid(column=2,row=r)
                r += 1
                # image_position (AOI: area of interest)
                try:
                    x = self.values['image_position'][0]
                    y = self.values['image_position'][1]
                except:
                    x = 0
                    y = 0
                self.values_frame_content_objects['x - image_position label'] = tkinter.Label(self.values_frame,text="x - image position:")
                self.values_frame_content_objects['x - image_position label'].grid(column=0,row=r)
                self.values_frame_content_values['x image_position'] = tkinter.IntVar()
                self.values_frame_content_values['x image_position'].set(x)
                self.values_frame_content_objects['x - image_position entry'] = tkinter.Entry(self.values_frame,textvariable = self.values_frame_content_values['x image_position'],width=6)
                self.values_frame_content_objects['x - image_position entry'].grid(column=1,row=r)
                r += 1
                self.values_frame_content_objects['y - image_position label'] = tkinter.Label(self.values_frame,text="y - image position:")
                self.values_frame_content_objects['y - image_position label'].grid(column=0,row=r)
                self.values_frame_content_values['y image_position'] = tkinter.IntVar()
                self.values_frame_content_values['y image_position'].set(y)
                self.values_frame_content_objects['y - image_position entry'] = tkinter.Entry(self.values_frame,textvariable = self.values_frame_content_values['y image_position'],width=6)
                self.values_frame_content_objects['y - image_position entry'].grid(column=1,row=r)
                # set
                self.values_frame_content_objects['set image_position button'] = tkinter.Button(self.values_frame,command=self.set_image_position,text="set image position")
                self.values_frame_content_objects['set image_position button'].grid(column=2,row=r)
                r += 1
                # color_codings
                self.values_frame_content_objects['color_codings label'] = tkinter.Label(self.values_frame,text="color coding:")
                self.values_frame_content_objects['color_codings label'].grid(column=0,row=r)
                self.values_frame_content_values['color_coding'] = tkinter.StringVar()
                self.values_frame_content_values['color_coding'].set(self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['color_codings'][0])
                self.values_frame_content_objects['color_coding optionmenu'] = tkinter.OptionMenu(self.values_frame,
                                                                                               self.values_frame_content_values['color_coding'],
                                                                                               *sorted(self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['color_codings']))
                self.values_frame_content_objects['color_coding optionmenu'].grid(column=1,row=r)
                r += 1
                # framerate
                self.values_frame_content_objects['framerate label'] = tkinter.Label(self.values_frame,text="framerate:")
                self.values_frame_content_objects['framerate label'].grid(column=0,row=r)
                self.values_frame_content_values['framerate'] = tkinter.DoubleVar()
                v = 10
                try:
                    v = self.values['framerate']
                except:
                    pass
                self.values_frame_content_values['framerate'].set(v)
                self.values_frame_content_objects['framerate entry'] = tkinter.Entry(self.values_frame,textvariable = self.values_frame_content_values['framerate'],width=6)
                self.values_frame_content_objects['framerate entry'].grid(column=1,row=r)
                r += 1
            # features
            for f in self.camlist[index]['features']:
                self.values_frame_content_objects['%s label' % f] = tkinter.Label(self.values_frame,text="%s:" % f)
                self.values_frame_content_objects['%s label' % f].grid(column=0,row=r)
                v = 0
                if self.values != None:
                    try:
                        v = self.values['feature_settings']['val'][f]
                    except:
                        pass
                if isinstance(self.camlist[index]['features'][f]['val'],float):
                    self.values_frame_content_values['%s var' % f] = tkinter.DoubleVar()
                else:
                    self.values_frame_content_values['%s var' % f] = tkinter.IntVar()
                self.values_frame_content_values['%s var' % f].set(v)
                self.values_frame_content_objects['%s entry' % f] = tkinter.Entry(self.values_frame,textvariable = self.values_frame_content_values['%s var' % f],width=6)
                self.values_frame_content_objects['%s entry' % f].grid(column=1,row=r)
                self.values_frame_content_values['%s mode var' % f] = tkinter.StringVar()
                v = ""
                if self.values != None:
                    try:
                        v = self.values['feature_settings']['mode'][f]
                    except:
                        pass
                self.values_frame_content_values['%s mode var' % f].set(v)
                self.values_frame_content_objects['%s optionmenu' % f] = tkinter.OptionMenu(self.values_frame,self.values_frame_content_values['%s mode var' % f],*self.camlist[index]['features'][f]['modes'])
                self.values_frame_content_objects['%s optionmenu' % f].grid(column=2,row=r)
                r += 1

    def set_mode(self):
        if (self.camlist != None) and (self.values != None):
            self.set_values_from_gui_to_variable()
            self.values_frame_content()

    def set_guid(self):
        try:
            v = self.guid_value.get() # AVT Guppy F080B (2892819639808492)
            r = re.findall("\(([0-9]+)\)$",v)
            if r:
                guid = int(r[0])
                self.values['guid'] = guid
                if guid in self.guidlist:
                    index = self.guidlist.index(guid)
                elif int(guid) in self.guidlist:
                    index = self.guidlist.index(int(guid))
                if self.guid == None:
                    self.guid = guid
                elif self.guid != guid:
                    self.guid = guid
                    self.values['image_size'] = (self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][0],self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][1])
                    self.values['image_position'] = (0,0)
                    self.values_frame_content()
        except:
            pass

    def set_values_from_gui_to_variable(self):
        index = None
        try:
            v = self.guid_value.get() # AVT Guppy F080B (2892819639808492)
            r = re.findall("\(([0-9]+)\)$",v)
            if r:
                guid = int(r[0])
                self.values['guid'] = guid
                if guid in self.guidlist:
                    index = self.guidlist.index(guid)
                elif int(guid) in self.guidlist:
                    index = self.guidlist.index(int(guid))
                if self.guid == None:
                    self.guid = guid
                elif self.guid != guid:
                    self.guid = guid
        except:
            pass
        if index != None:
            try:
                self.values['mode'] = self.values_frame_content_values['mode'].get()
            except:
                pass
            try:
                self.values['framerate'] = float(self.values_frame_content_values['framerate'].get())
            except:
                pass
            try:
                x = self.values_frame_content_values['x image_size'].get()
                x0 = self.values_frame_content_values['x image_position'].get()
                y = self.values_frame_content_values['y image_size'].get()
                y0 = self.values_frame_content_values['y image_position'].get()
            except:
                x = None
            if x == None:
                try:
                    x = self.values['image_size'][0]
                    y = self.values['image_size'][1]
                    x0 = self.values['image_size'][0]
                    y0 = self.values['image_size'][1]
                except:
                    x = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][0]
                    y = self.camlist[index]['modes'][self.values_frame_content_values['mode'].get()]['max_image_size'][1]
                    x0 = 0
                    y0 = 0
            self.values['image_size'] = (x,y)
            self.values['image_position'] = (x0,y0)
            try:
                for f in self.camlist[index]['features']:
                    self.values['feature_settings']['val'][f] = self.values_frame_content_values['%s var' % f].get()
                    self.values['feature_settings']['mode'][f] = self.values_frame_content_values['%s mode var' % f].get()
            except:
                pass
            try:
                if self.trigger_value.get() == self.trigger_optionlist[1]:
                    self.values['extern_trigger'] = True
                else:
                    self.values['extern_trigger'] = False
                print("####",self.values['extern_trigger'])
            except:
                pass
        self.values_frame_content()

    def setvalues_command(self):
        self.setvalues_button.configure(state=tkinter.DISABLED)
        r = False
        if self.live_view_running:
            self.stop_live_view()
            r = True
        self.socketlock.acquire() # lock
        if (self.socket != None) and (self.values != None):
            self.set_values_from_gui_to_variable()
            self.log.debug("set values to the server")
            self.send_data_to_socket(self.socket,"setvalues %s" % self.create_send_format(self.values))
            self.log.debug("ready setting values to the server")
        self.socketlock.release() # release the lock
        if r:
            self.start_live_view()
        self.setvalues_button.configure(state=tkinter.NORMAL)

    def get_version(self):
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.send_data_to_socket(self.socket,"version")
            data = self.receive_data_from_socket(self.socket,self.bufsize)
            self.log.info("server-version: %s" % data)
        self.socketlock.release() # release the lock

    def start_camera(self):
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.send_data_to_socket(self.socket,"startcam")
        self.socketlock.release() # release the lock

    def stop_camera(self):
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.send_data_to_socket(self.socket,"stopcam")
        self.socketlock.release() # release the lock

    def start_recording(self):
        if not self.recording_path_are_set:
            self.set_recording_path()
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.send_data_to_socket(self.socket,"startrec")
        self.socketlock.release() # release the lock

    def recording1frame(self):
        if not self.recording_path_are_set:
            self.log.info("will set path automatically")
            self.set_recording_path()
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.send_data_to_socket(self.socket,"rec1frame")
        self.socketlock.release() # release the lock

    def get_single_frame(self):
        """get a single frame with socket communication from camera server

        Author: Daniel Mohr
        Date: 2013-02-27
        """
        rd = False
        data = None
        self.socketlock.acquire() # lock
        if self.socket != None:
            try:
                self.send_data_to_socket(self.socket,"get1frame")
                data = self.receive_data_from_socket(self.socket,self.bufsize)
                rd = True
            except:
                self.log.warning('cannot get frame from server')
        self.socketlock.release() # release the lock
        self.update_img_lock.acquire() # lock
        if not data:
            rd = False
            self.update_img_request_stop = True
        if rd:
            self.socket_pic_data = data
            self.img_time = time.time()
        else:
            self.update_img_request_stop = True
        self.update_img_lock.release() # release the lock

    def start_live_view(self):
        if self.socket != None:
            if not self.live_view_running:
                self.live_view_running = True
                self.get_frame_button.configure(state=tkinter.DISABLED)
                self.liveview_thread = threading.Thread(target=self.liveview)
                self.liveview_thread.daemon = True # exit thread when the main thread terminates
                self.liveview_thread.start()

    def liveview(self):
        it = 0
        itint2 = 10
        dt = None
        t0 = time.time()
        while self.live_view_running:
            self.get_single_frame()
            it += 1
            if it == itint2:
                t1 = time.time()
                dt = t1-t0
                self.log.debug("get %d frames in %f sec (framerate: %f)" % (it,dt,it/dt))
                it = 0
                t0 = time.time()
            if dt:
                time.sleep(max(dt/(itint2*10.0),0.006))

    def stop_live_view(self):
        self.live_view_running = False
        self.get_frame_button.configure(state=tkinter.NORMAL)

    def stop_recording(self):
        self.socketlock.acquire() # lock
        if self.socket != None:
            try:
                self.send_data_to_socket(self.socket,"stoprec")
            except:
                self.log.error("cannot stop recording")
        self.socketlock.release() # release the lock

    def set_recording_path(self):
        self.socketlock.acquire() # lock
        for i in range(len(self.recording_pathes)):
            p = self.recording_pathes_vals[i].get()
            p = p.replace("$date",time.strftime("%Y-%m-%d"))
            if (self.guid != None) and (self.guid != -1) and (self.guid != -2):
                p = p.replace("$guid","%d" % self.guid)
            self.recording_pathes_vals[i].set(p)
            self.recording_pathes[i] = p
        if self.socket != None:
            self.send_data_to_socket(self.socket,"setpathes %s" % self.create_send_format(self.recording_pathes))
            self.recording_path_are_set = True
        self.socketlock.release() # release the lock

    def set_recording_less_pathes(self):
        self.recording_pathes = self.recording_pathes[0:len(self.recording_pathes)-1]
        self.create_recording_path_frame()
        if len(self.recording_pathes) <= 1:
            self.recording_path_less_button.configure(state=tkinter.DISABLED)

    def set_recording_more_pathes(self):
        self.recording_pathes += [""]
        self.create_recording_path_frame()
        if len(self.recording_pathes) > 1:
            self.recording_path_less_button.configure(state=tkinter.NORMAL)

    def quit_server_command(self):
        try:
            self.log.debug("stop live view")
            self.stop_live_view()
        except: pass
        try:
            self.log.debug("stop recording")
            self.stop_recording()
        except: pass
        try:
            self.log.debug("stop camera")
            self.stop_camera()
        except: pass
        self.log.debug("try to quit server")
        self.socketlock.acquire() # lock
        if self.socket != None:
            self.log.info("quit server and disconnect")
            self.live_view_running = False
            try:
                self.send_data_to_socket(self.socket,"quit")
            except: pass
            self.socketlock.release() # release the lock
            self.close_connection_command()
        else:
            self.socketlock.release() # release the lock
