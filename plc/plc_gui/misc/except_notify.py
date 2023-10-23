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

import sys
import multiprocessing as mp

from .misc import proccesses_to_join, bcolors


def wrapper(title: str, message: str) -> None:
    mp.freeze_support()
    import tkinter
    from tkinter import ttk

    root = tkinter.Tk()
    root.title(title)
    frm = ttk.Frame(root, padding=10)
    ttk.Label(frm, text=message).pack()
    ttk.Button(frm, text="Quit", command=root.destroy).pack()
    frm.pack()
    root.mainloop()


def show(exc: Exception, context: str | None = None) -> None:
    exc_type = type(exc)
    title = "An exception occurred"
    message = f"""
    Exception type: {exc_type}
    EXC mess: {str(exc)}
    Exception context:
    {context}

    Traceback:
    {exc.__traceback__}
    """

    if mp.get_start_method() == "spawn":
        p = mp.Process(target=wrapper, args=(title, message))
        p.start()
        proccesses_to_join.append(p)
    else:
        print(bcolors.bold_red + "Cannot notify you" + bcolors.reset, file=sys.stderr)


if __name__ == "__main__":
    pass
