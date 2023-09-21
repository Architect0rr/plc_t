"""queued logging classes for plc

Author: Daniel Mohr
Date: 2013-03-17
"""

import logging
import logging.handlers
import queue
import threading

# import string


class LabelLogHandler(logging.Handler):
    def __init__(self, n=5):
        logging.Handler.__init__(self)
        self.pw = None
        self.queue = queue.Queue()
        self.n = n  # n lines in buffer
        self.maxqueue = 10 * self.n
        self.buffer = self.n * [""]
        self.logrunning = True
        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.name = "LabelLogHandler: loop"
        self.thread.start()

    def set_out(self, pw):
        self.pw = pw

    def emit(self, record):
        if self.pw is not None:
            try:
                self.queue.put(self.format(record))
            except Exception:
                pass

    def loop(self):
        while self.logrunning:
            record = self.queue.get()
            if self.pw is not None:
                try:
                    self.buffer[0:self.n - 1] = self.buffer[1:self.n]
                    self.buffer[self.n - 1] = record
                    # self.pw.set(string.join(self.buffer,"\n"))
                    self.pw.set("\n".join(self.buffer))
                except Exception:
                    pass
            self.queue.task_done()
            while self.queue.qsize() > self.maxqueue:
                record = self.queue.get()
                self.queue.task_done()

    def close(self):
        self.logrunning = False
        self.queue.put("stop logging queue")
        logging.Handler.close(self)


class QueuedWatchedFileHandler(logging.Handler):
    def __init__(self, filename):
        logging.Handler.__init__(self)
        self.background_handler = logging.handlers.WatchedFileHandler(filename)
        self.queue = queue.Queue()
        self.logrunning = True
        self.startloopthread()

    def setFormatter(self, form):
        logging.Handler.setFormatter(self, form)
        self.background_handler.setFormatter(form)

    def emit(self, record):
        try:
            self.queue.put(record)
        except Exception:
            pass

    def startloopthread(self):
        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.name = "QueuedWatchedFileHandler: loop"
        self.thread.start()

    def startloopthreadagain(self):
        if not self.thread.is_alive():
            self.startloopthread()

    def loop(self):
        while self.logrunning:
            record = self.queue.get()
            try:
                self.background_handler.emit(record)
            except Exception:
                pass
            self.queue.task_done()

    def close(self):
        self.logrunning = False
        self.queue.put(logging.LogRecord("", logging.WARNING, "", 1, "stop logging queue", None, None))
        logging.Handler.close(self)
