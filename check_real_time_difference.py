#!/usr/bin/python -O
# Author: Daniel Mohr
# Date: 2013-04-14, 2014-07-22

__check_real_time_difference_date__ = "2014-07-22"
__check_real_time_difference_version__ = __check_real_time_difference_date__

import argparse
import numpy
import socket
import struct
import sys
import time

def main():
    help = ""
    parser = argparse.ArgumentParser(
        description='check_real_time_difference.py is a small program to check the real times on different computers.',
        epilog="Author: Daniel Mohr\nDate: %s\nLicense: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007\n\n%s" % (__check_real_time_difference_version__,help),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-ip',
                        nargs=1,
                        default="localhost",
                        type=str,
                        required=False,
                        dest='ip',
                        help='Set the IP/host n to listen. If ip == \"\" the default behavior will be used; typically listen on all possible adresses. default: localhost',
                        metavar='n')
    parser.add_argument('-port',
                        nargs=1,
                        default=15124,
                        type=int,
                        required=False,
                        dest='port',
                        help='Set the port p to listen. If p == 0 the default behavior will be used; typically choose a port. default: 15124',
                        metavar='p')
    parser.add_argument('-nn',
                        nargs=1,
                        default=10,
                        type=int,
                        required=False,
                        dest='nn',
                        help='Do the n communications nn times. default: 10',
                        metavar='nn')
    parser.add_argument('-pnn',
                        nargs=1,
                        default=0.0,
                        type=float,
                        required=False,
                        dest='pnn',
                        help='Set a pause of x seconds between the nn times. default: 0.0',
                        metavar='x')
    parser.add_argument('-n',
                        nargs=1,
                        default=100,
                        type=int,
                        required=False,
                        dest='n',
                        help='Do the communication n times in both directions. default: 100',
                        metavar='n')
    parser.add_argument('-pn',
                        nargs=1,
                        default=0.001,
                        type=float,
                        required=False,
                        dest='pn',
                        help='Set a pause of x seconds between the n times. default: 0.001',
                        metavar='x')
    parser.add_argument('-dn',
                        nargs=1,
                        default=1,
                        type=int,
                        required=False,
                        dest='dn',
                        help='Sends n bytes every time. default: 1',
                        metavar='n')
    parser.add_argument('-debug',
                        nargs=1,
                        default=0,
                        type=int,
                        required=False,
                        dest='debug',
                        help='Set debug level. 0 no debug info (default); 1 debug to STDOUT.',
                        metavar='debug_level')
    parser.add_argument('-timestamp',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='timestamp',
                        help='By specifying this flag a timestamp will be added to the debug output.')
    parser.add_argument('-server',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='server',
                        help='By specifying this flag this script will behave as the server.')
    parser.add_argument('-wait',
                        default=False,
                        required=False,
                        action='store_true',
                        dest='wait',
                        help='By specifying this flag the server tries to use the given port until it is possible.')
    args = parser.parse_args()
    if not isinstance(args.ip,str):
        args.ip = args.ip[0]
    if not isinstance(args.port,int):
        args.port = args.port[0]
    if not isinstance(args.n,int):
        args.n = args.n[0]
    if not isinstance(args.pn,float):
        args.pn = args.pn[0]
    if not isinstance(args.nn,int):
        args.nn = args.nn[0]
    if not isinstance(args.pnn,float):
        args.pnn = args.pnn[0]
    if not isinstance(args.dn,int):
        args.dn = args.dn[0]
    if not isinstance(args.debug,int):
        args.debug = args.debug[0]
    if not isinstance(args.server,bool):
        args.server = args.server[0]
    if not isinstance(args.wait,bool):
        args.wait = args.wait[0]
    if not isinstance(args.timestamp,bool):
        args.timestamp = args.timestamp[0]
    if args.server:
        server(args)
    else:
        client(args)

def client(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.ip,args.port))

    nn = args.nn
    n = args.n
    dn = args.dn
    v = dn*"."
    pn = args.pn
    pnn = args.pnn
    dotimestamp = args.timestamp
    send_data_to_socket(s,struct.pack("!I",nn))
    send_data_to_socket(s,struct.pack("!I",n))
    send_data_to_socket(s,struct.pack("!I",dn))
    send_data_to_socket(s,struct.pack("!d",pn))
    send_data_to_socket(s,struct.pack("!d",pnn))
    roundtimes = [] # time need for the network
    offsets = [] # offset between A and B; offset > 0 means B is in future
    if args.debug > 0:
        if dotimestamp:
            print("# timestamp           offset           roundtime ")
        else:
            print("# offset           roundtime ")
        sys.stdout.flush()
    for ii in range(nn):
        # local -> remote
        [t1,t4] = client_once(n,s,v,dn,pn)
        t2 = [] # receive from A at B at these times
        t3 = [] # send from B to A at these time
        roundtime = [] # time need for the network
        offset = [] # offset between A and B; offset > 0 means B is in future
        for i in range(n):
            t2 += struct.unpack("!d",recieve_data_from_socket(s,8))
            t3 += struct.unpack("!d",recieve_data_from_socket(s,8))
            roundtime += [(t4[i]-t1[i]) - (t3[i]-t2[i])]
            offset += [0.5 * ((t2[i]-t1[i]) + (t3[i]-t4[i]))] # = T(B) - T(A)
        if args.debug > 0:
            if dotimestamp:
                print(("  %f   %+f msec   %f msec   (A -> B)" % (time.time(),numpy.mean(offset)*1000,numpy.mean(roundtime)*1000)))
            else:
                print(("  %+f msec   %f msec   (A -> B)" % (numpy.mean(offset)*1000,numpy.mean(roundtime)*1000)))
            sys.stdout.flush()
        roundtimes += roundtime
        offsets += offset
        # remote -> local
        [t2,t3] = server_once(1,s,1,".",0.001)
        [t2,t3] = server_once(n,s,dn,v,pn)
        t1 = [] # send from B to A at these times
        t4 = [] # receive from A at B at these time
        roundtime = [] # time need for the network
        offset = [] # offset between A and B; offset > 0 means B is in future
        for i in range(n):
            t1 += struct.unpack("!d",recieve_data_from_socket(s,8))
            t4 += struct.unpack("!d",recieve_data_from_socket(s,8))
            roundtime += [(t4[i]-t1[i]) - (t3[i]-t2[i])]
            offset += [0.5 * ((t1[i]-t2[i]) + (t4[i]-t3[i]))] # = T(B) - T(A)
        if args.debug > 0:
            if dotimestamp:
                print(("  %f   %+f msec   %f msec   (A <- B)" % (time.time(),numpy.mean(offset)*1000,numpy.mean(roundtime)*1000)))
            else:
                print(("  %+f msec   %f msec   (A <- B)" % (numpy.mean(offset)*1000,numpy.mean(roundtime)*1000)))
            sys.stdout.flush()
        roundtimes += roundtime
        offsets += offset
        time.sleep(pnn)
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    if args.debug > 0:
        print("")
    print(("arithmetic mean of round time:         %f msec" % (numpy.mean(roundtimes)*1000)))
    print(("arithmetic mean of expected offset:    %f msec" % (numpy.mean(offsets)*1000)))
    print(("standard deviation of expected offset: %f msec" % (numpy.std(offsets)*1000)))
    sys.stdout.flush()

def client_once(n,s,v,dn,pn):
    time.sleep(0.001)
    t1 = [] # send from A to B at these times
    t4 = [] # receive from B at A at these time
    for i in range(n):
        t1 += [time.time()]
        send_data_to_socket(s,v)
        recieve_data_from_socket(s,dn)
        t4 += [time.time()]
        time.sleep(pn)
    return [t1,t4]

def server(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    if args.wait:
        while not connected:
            try:
                s.bind((args.ip, args.port))
                connected = True
                print("listen")
            except:
                print("could not listen, try again in 3 seconds.")
                time.sleep(3)
    else:
        s.bind((args.ip, args.port))
    s.listen(1)
    conn, addr = s.accept()
    nn = struct.unpack("!I",recieve_data_from_socket(conn,4))[0]
    n = struct.unpack("!I",recieve_data_from_socket(conn,4))[0]
    dn = struct.unpack("!I",recieve_data_from_socket(conn,4))[0]
    pn = struct.unpack("!d",recieve_data_from_socket(conn,8))[0]
    pnn = struct.unpack("!d",recieve_data_from_socket(conn,8))[0]
    v = dn*"."
    for ii in range(nn):
        [t2,t3] = server_once(n,conn,dn,v,pn)
        for i in range(n):
            send_data_to_socket(conn,struct.pack("!d",t2[i]))
            send_data_to_socket(conn,struct.pack("!d",t3[i]))
        [t1,t4] = client_once(1,conn,v,1,0.001)
        [t1,t4] = client_once(n,conn,v,dn,pn)
        for i in range(n):
            send_data_to_socket(conn,struct.pack("!d",t1[i]))
            send_data_to_socket(conn,struct.pack("!d",t4[i]))
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
    s.close()

def server_once(n,conn,dn,v,pn):
    t2 = []
    t3 = []
    for i in range(n):
        recvdata = recieve_data_from_socket(conn,dn)
        t2 += [time.time()]
        time.sleep(pn)
        t3 += [time.time()]
        send_data_to_socket(conn,v)
    time.sleep(pn+0.001)
    return [t2,t3]

def send_data_to_socket(s,msg):
    totalsent = 0
    msglen = len(msg)
    while totalsent < msglen:
        sent = s.send(msg[totalsent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent

def recieve_data_from_socket(s,totalbytes):
    data = ""
    while len(data) < totalbytes:
        data += s.recv(min(totalbytes-len(data),4096))
    return data

if __name__ == "__main__":
    main()
