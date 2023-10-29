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
conversion from and to some units
"""


from typing import Literal


def b2i(b: bool) -> Literal[1, 0]:
    if b:
        return 1
    else:
        return 0


def i2b(i: Literal[1, 0]) -> bool:
    if i == 1:
        return True
    else:
        return False


def b2onoff(b: bool) -> Literal['ON', 'OFF']:
    if b:
        return "ON"
    else:
        return "OFF"


def b2error(b: bool) -> Literal['ERROR', '']:
    if b:
        return "ERROR"
    else:
        return ""


def noti2b(i: int) -> bool:
    if i == 0:
        return True
    else:
        return False


# dac <-> volt
# def volt2dac(x,onlypositiv=False):
#     r = int((x + 10.0) * 65535.0 / 20.0)
#     if onlypositiv == True:
#         r = max(32768,r) # dac-values lower 32768 represent negativ voltage
#     r = max(int(0),min(r,int(65535)))
#     return r


def volt2dac(x: float) -> int:
    r = round((x + 10.0) * 65535.0 / 20.0)
    if x >= 0:
        r = max(32768, r)  # dac-value lower 32768 represents negativ voltage
    r = max(int(0), min(r, int(65535)))
    return r


def dac2volt(r: str) -> float:
    return float(r) * 20.0 / 65535.0 - 10.0


# adc <-> volt
def volt2adc(x: float) -> int:
    if x < 0:
        m = 32768.0  # = - SHRT_MIN
    else:
        m = 32767.0  # = SHRT_MAX
    r = int(x * m / 10.0)
    r = max(int(-32768), min(r, int(32767)))
    return r


def adc2volt(r: float) -> float:
    if r < 0:
        m = 32768.0  # = - SHRT_MIN
    else:
        m = 32767.0  # = SHRT_MAX
    return float(r) * 10.0 / m


# sccm | msccm <-> dac | adc | volt
def sccm2dac(x: float) -> int:
    return volt2dac(sccm2volt(x))


def dac2sccm(x: str) -> float:
    r = volt2sccm(dac2volt(x))
    r = max(0.0, min(r, 1.0))
    return r


def sccm2volt(x: float) -> float:
    return x * 5.0


def volt2sccm(x: float) -> float:
    return x / 5.0


def msccm2dac(x: float) -> int:
    return volt2dac(msccm2volt(x))


def dac2msccm(x: str) -> float:
    return dac2sccm(x) * 1000.0


def msccm2volt(x: float) -> float:
    return sccm2volt(x) / 1000.0


def volt2msccm(x: float) -> float:
    return volt2sccm(x) * 1000.0


# def sccm2adc(x):
#     return volt2adc(sccm2adc(x))


def adc2sccm(x: float) -> float:
    r = volt2sccm(adc2volt(x))
    r = max(0.0, min(r, 1.0))
    return r


def msccm2adc(x: float) -> int:
    return volt2adc(msccm2volt(x))


def adc2msccm(x: float) -> float:
    return adc2sccm(x) * 1000.0


def adcstring2volt(s: str) -> float:
    r = int(s, 16)
    m = 32768.0  # = - SHRT_MIN
    if r > 32767:  # > SHRT_MAX
        r = r - 65535
        m = 32767.0  # = SHRT_MAX
    return float(r) * 10.0 / m
