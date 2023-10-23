#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import time
import threading

import tkinter as tk
import tkinter.font as tkFont
from typing import TypeVar, Callable
import functools


T = TypeVar("T")


def lockit(fn: Callable[..., T]):  # type: ignore
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        self = args[0]
        self.lock.acquire()
        fr = fn(*args, **kwargs)
        self.lock.release()
        return fr

    return wrapper


class CircularProgressbar(tk.Canvas):
    def __init__(
        self,
        _root: tk.Toplevel,
        w: int,
        h: int,
        _interval: int = 0,
        _start_angle: float = 0,
        _full_extent: float = 360.0,
        _text: bool = True,
        def_delta: int = 1,
    ) -> None:
        super().__init__(_root, width=w, height=h, bg="white")

        self.text = _text
        self.interval = _interval
        self.start_ang = _start_angle
        self.start_angle = _start_angle
        self.full_extent = _full_extent

        self.auto = False if self.interval == 0 else True
        self.increment = self.full_extent / self.interval if self.auto else def_delta
        self.extent: float = 0
        if self.auto:
            self.running = False
        if self.text:
            self.percent = "0%"
            self.custom_font = tkFont.Font(family="Helvetica", size=12, weight="bold")

        a = min(w, h)
        dw = round((w - a) / 2)
        dh = round((h - a) / 2)
        width = round(a / 5)

        self.oval1 = self.create_oval(dw, dh, a + dw, a + dh)
        self.oval2 = self.create_oval(dw + width, dh + width, a + dw - width, a + dh - width)
        rt = width / 2
        self.arc = self.create_arc(
            dw + rt,
            dh + rt,
            a + dw - rt,
            a + dh - rt,
            start=self.start_ang,
            extent=self.extent,
            width=width,
            style="arc",
        )

        if self.text:
            self.label = self.create_text(
                round(a / 2) + dw, round(a / 2) + dh, text=self.percent, font=self.custom_font
            )

        self.update()

    def start(self) -> None:
        if self.auto:
            self.running = True
            self.after(self.interval, self.step, self.increment)

    def step(self, delta: float | None = None) -> None:
        """Increment extent and update arc and label displaying how much completed."""
        if delta is None:
            delta = self.increment
        self.extent = (self.extent + delta) % 360
        self.itemconfigure(self.arc, extent=self.extent)
        if self.text:
            percent = "{:.0f}%".format(round(float(self.extent) / self.full_extent * 100))
            self.itemconfigure(self.label, text=percent)
        if self.auto and self.running:
            self.after(self.interval, self.step, delta)

    def stop(self) -> None:
        if self.auto:
            self.running = not self.running


class PassiveSplash(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        tk.Toplevel.__init__(self, parent)
        self.title("Splash")
        w = parent.winfo_width()
        h = parent.winfo_height()
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.update()


class Splash(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        tk.Toplevel.__init__(self, parent)
        self.title("Please wait...")
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.run = True
        self.lock = threading.Lock()

        w = parent.winfo_width()
        h = parent.winfo_height()
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.progressbar = CircularProgressbar(self, w, h, _text=False)
        self.progressbar.pack()

    def dummy(self, len: int) -> None:
        def func() -> None:
            time.sleep(len)
            self.run = False

        self.__thr = threading.Thread(target=func)
        self.__thr.start()

    def exit(self) -> None:
        self.run = False

    def start(self, tm=0.1, rd: int = 0) -> None:
        self.progressbar.start()
        if rd > 0:
            self.dummy(rd)
        while True:
            # print("Acquiring lock")
            self.lock.acquire()
            # print("Lock acquired")
            if not self.run:
                # print("Exiting")
                if rd > 0:
                    self.__thr.join()
                # print("Lock released")
                self.lock.release()
                return
            # print("Not exiting")
            self.lock.release()
            # print("Lock released, step")
            self.progressbar.step(1)
            # print("Step end, updating")
            self.update()
            # print("Updated, sleeping")
            time.sleep(tm)
            # print("Woke up")
        # self.mainloop()


class Splasher:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root

    def splash_start(self) -> None:
        self.root.withdraw()
        self.splash = Splash(self.root)
        self.splash.update()
        self.splash.start(0.1)

    def splash_set_stop(self) -> None:
        self.splash.lock.acquire()
        self.splash.run = False
        self.splash.lock.release()

    def splash_stop(self) -> None:
        self.splash.run = False
        self.splash.destroy()
        self.root.deiconify()


if __name__ == "__main__":
    pass
