#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Daniel Mohr
#
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

"""
queued logging classes for plc
"""

import queue
import threading
import logging
import logging.handlers
from tkinter import ttk

# import string


class LabelLogHandler(logging.Handler):
    def __init__(self, n: int = 5) -> None:
        logging.Handler.__init__(self)
        self.pw: ttk.Label
        self.queue: queue.Queue[str] = queue.Queue()
        self.n = n  # n lines in buffer
        self.maxqueue = 10 * self.n
        self.buffer = self.n * [""]
        self.logrunning = True
        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.name = "LabelLogHandler: loop"
        self.thread.start()

    def set_out(self, pw: ttk.Label) -> None:
        self.pw = pw

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.queue.put(self.format(record))
        except Exception:
            pass

    def loop(self) -> None:
        while self.logrunning:
            record = self.queue.get()
            try:
                self.buffer[0:self.n - 1] = self.buffer[1:self.n]
                self.buffer[self.n - 1] = record
                self.pw.configure(text="\n".join(self.buffer))
            except Exception:
                pass
            self.queue.task_done()
            while self.queue.qsize() > self.maxqueue:
                record = self.queue.get()
                self.queue.task_done()

    def close(self) -> None:
        self.logrunning = False
        self.queue.put("stop logging queue")
        logging.Handler.close(self)


class QueuedWatchedFileHandler(logging.Handler):
    def __init__(self, filename: str) -> None:
        logging.Handler.__init__(self)
        self.background_handler = logging.handlers.WatchedFileHandler(filename)
        self.queue: queue.Queue[logging.LogRecord] = queue.Queue()
        self.logrunning = True
        self.startloopthread()

    def setFormatter(self, fmt: logging.Formatter | None) -> None:
        if fmt is None:
            raise RuntimeError("fmt cannot be None")
        logging.Handler.setFormatter(self, fmt)
        self.background_handler.setFormatter(fmt)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.queue.put(record)
        except Exception:
            pass

    def startloopthread(self) -> None:
        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.name = "QueuedWatchedFileHandler: loop"
        self.thread.start()

    def startloopthreadagain(self) -> None:
        if not self.thread.is_alive():
            self.startloopthread()

    def loop(self) -> None:
        while self.logrunning:
            record = self.queue.get()
            try:
                self.background_handler.emit(record)
            except Exception:
                pass
            self.queue.task_done()

    def close(self) -> None:
        self.logrunning = False
        self.queue.put(logging.LogRecord("", logging.WARNING, "", 1, "stop logging queue", None, None))
        logging.Handler.close(self)


if __name__ == "__main__":
    pass
