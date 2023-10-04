#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pty
import stat

# import time

# import serial
# import logging
from pathlib import Path

# handler = logging.StreamHandler(sys.stdout)
# # formatter: logging.Formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
# formatter: logging.Formatter = logging.Formatter("%(name)s: %(message)s")
# handler.setFormatter(formatter)

# log_rf = logging.getLogger("rf")
# log_rf.setLevel(logging.DEBUG)
# log_rf.addHandler(handler)

# log_dc = logging.getLogger("dc")
# log_dc.setLevel(logging.DEBUG)
# log_dc.addHandler(handler)

combo = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH

master_rf, slave_rf = pty.openpty()
s_name_rf = os.ttyname(slave_rf)
m_name_rf = os.ttyname(master_rf)

s_rf_path = Path(s_name_rf)
# if rf_path.exists():
rf_path = Path("/dev/RF_GEN_01")
rf_path.unlink(True)
os.symlink(s_rf_path, rf_path)
os.chmod(rf_path, combo)

master_dc, slave_dc = pty.openpty()
s_name_dc = os.ttyname(slave_dc)
m_name_dc = os.ttyname(master_dc)

s_dc_path = Path(s_name_dc)
# if dc_path.exists():
dc_path = Path("/dev/RF_DC_01")
dc_path.unlink(True)
os.symlink(s_dc_path, dc_path)
os.chmod(dc_path, combo)

# print(m_name_rf)
# print(s_name_rf)
# print(m_name_dc)
# print(s_name_dc)


# rf_buff = b""
# dc_buff = b""
os.close(slave_rf)
os.close(slave_dc)
while True:
    sys.stdout.write(os.read(master_rf, 1).decode("utf-8"))
    # sym = os.read(master_rf, 1)
    # rf_buff += sym
    # if sym == b"\n":
    #     log_rf.info(rf_buff.decode('utf-8'))
    #     rf_buff = b""

    # sym = os.read(master_dc, 1)
    # dc_buff += sym
    # if sym == b"\n":
    #     log_rf.info(rf_buff.decode('utf-8'))
    #     rf_buff = b""

os.close(master_rf)
os.close(master_dc)

# ser = serial.Serial(s_name)

# To Write to the device
# ser.write(b"Your text")

# To read from the device
# os.read(master, 1000)
