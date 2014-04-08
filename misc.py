#!/usr/bin/env python3

"""Provide general tools to FlexA."""

import sys
import re
import subprocess
import socket
from threading import Thread
from distutils.util import strtobool
from xmlrpc.client import ServerProxy

class Ping(object):
    
    def __init__(self):
         self.ip_list = []
         self.online = []
         self.offline = []
      
    def scan(self, ip_list):
         """ 
         Recive a list of strings with ip
         Complete list onlines and offline hosts
         """
         for ip in ip_list:
            server_addr = 'http://{}:5000'.format(ip)
            host = ServerProxy(server_addr)
            if self.ping(host):
                self.online.append(ip)
            else:
                self.offline.append(ip)

    def ping(self, host):
         """
         this function 'pinging' on hosts
         recive a xmlrpc.ServerProxy object
         0 - offline
         1 - online
         """
         try:
            host.still_alive()
            return 1
         except (ConnectionRefusedError, OSError, TimeoutError):
            return 0


def split_file(fil, nparts):
    """Recive
    pointer of file - fil
    how many part to split  - nparts
    """

    #config size of file
    size = fil.seek(0,2)
    #set in initial of file
    fil.seek(0)
    #inicialize list of parts
    part = []
    #size of parts
    chucksize = size//nparts

    #get parts but not the last
    for i in range(nparts-1):
        part.append(fil.read(chucksize))

    #get the last part that can has size<chucksize
    part.append(fil.read(size - fil.tell()))

    return part

def join_file(fil, parts):
    """Recive
    list whith all parts of file - parts
    name of file that will save  - name
    """

    #how many parts
    nparts = len(parts)
    #write in file
    for i in range(nparts):
        fil.write( parts[i].read())

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    question -- is a string that is presented to the user.
    default -- is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no" or None (meaning an answer is
    required of the user).

    The "answer" return value is one of "yes" or "no".

    """
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    try:
        while True:
            print(question + prompt)
            choice = input().lower()
            try:
                if default is not None and choice == '':
                    return strtobool(default)
                elif choice:
                    return strtobool(choice)
            except ValueError:
                print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
    except KeyboardInterrupt:
        sys.exit(2)


def send_file(host, transf_file):
    """ Send a file with socket to client
        Transfer with socket because XMLRPC transfer very slower than socket

        host: tuple (ip, port)
        transf_file: object file that will  transfer
    """       

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("CHEGANDO NO SEND_FILE")
    client.connect(host)
    msg = transf_file.read(1024)
    while msg:
        client.send(msg)
        msg = transf_file.read(1024)
    client.close()

def recive_file(host, save_file):
    """ Recive a file with socket 
        Transfer with socket because XMLRPC transfer very slower than socket
        
        host: tuple (ip, port)
        save_file: object file that will  transfer
    """

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(host)
    server.listen(1)

    print("trhead recive, antes do accept")
    con, server_name  = server.accept()
    msg = con.recv(1024)
    while msg:
        save_file.write(msg)
        msg = con.recv(1024) 
    con.close() 


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
