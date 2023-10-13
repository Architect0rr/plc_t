"""conversion from and to some units

Author: Daniel Mohr
Date: 2013-01-25
"""


def b2i(b):
    if b:
        return 1
    else:
        return 0


def i2b(i):
    if i == "1":
        return True
    else:
        return False


def b2onoff(b: bool):
    if b:
        return "ON"
    else:
        return "OFF"


def b2error(b):
    if b:
        return "ERROR"
    else:
        return ""


def noti2b(i):
    if i == "0":
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


def volt2dac(x):
    r = int((x + 10.0) * 65535.0 / 20.0)
    if x >= 0:
        r = max(32768, r)  # dac-value lower 32768 represents negativ voltage
    r = max(int(0), min(r, int(65535)))
    return r


def dac2volt(r):
    return float(r) * 20.0 / 65535.0 - 10.0


# adc <-> volt
def volt2adc(x):
    if x < 0:
        m = 32768.0  # = - SHRT_MIN
    else:
        m = 32767.0  # = SHRT_MAX
    r = int(x * m / 10.0)
    r = max(int(-32768), min(r, int(32767)))
    return r


def adc2volt(r):
    if r < 0:
        m = 32768.0  # = - SHRT_MIN
    else:
        m = 32767.0  # = SHRT_MAX
    return float(r) * 10.0 / m


# sccm | msccm <-> dac | adc | volt
def sccm2dac(x):
    return volt2dac(sccm2volt(x))


def dac2sccm(x):
    r = volt2sccm(dac2volt(x))
    r = max(0.0, min(r, 1.0))
    return r


def sccm2volt(x):
    return x * 5.0


def volt2sccm(x):
    return x / 5.0


def msccm2dac(x):
    return volt2dac(msccm2volt(x))


def dac2msccm(x):
    return dac2sccm(x) * 1000.0


def msccm2volt(x):
    return sccm2volt(x) / 1000.0


def volt2msccm(x):
    return volt2sccm(x) * 1000.0


def sccm2adc(x):
    return volt2adc(sccm2adc(x))


def adc2sccm(x):
    r = volt2sccm(adc2volt(x))
    r = max(0.0, min(r, 1.0))
    return r


def msccm2adc(x):
    return volt2adc(msccm2volt(x))


def adc2msccm(x):
    return adc2sccm(x) * 1000.0


def adcstring2volt(s):
    r = int(s, 16)
    m = 32768.0  # = - SHRT_MIN
    if r > 32767:  # > SHRT_MAX
        r = r - 65535
        m = 32767.0  # = SHRT_MAX
    return float(r) * 10.0 / m
