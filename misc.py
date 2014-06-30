#!/usr/bin/env python3

"""Provide general tools to FlexA."""

import sys
import re
import subprocess
import socket
import binascii
import time
import signal
import os
from threading import Thread
from distutils.util import strtobool
from xmlrpc.client import ServerProxy

class Ping(object):
    """ Times to scan network
        the time between one scan and next is
        TIMEOUT_TO_ANSWER + TIME_AUTO_SCAN
    """
    TIMEOUT_TO_ANSWER = 2
    TIME_AUTO_SCAN = 3
    MYPORT = 51400

    def __init__(self, interface):
        """ recive interface of network
            String like `192.168.2.255`
        """
        self.interface = interface
        self.online = []

    def daemon(self):
        #thread answer_scan
        answer = Thread(target = self.answer_scan, daemon = True)
        answer.start()

        #thread to auto scan
        scan = Thread(target = self.auto_scan, daemon=True)
        scan.start()

    def auto_scan(self):
        while True:
            self.scan()
            print(self.online)
            time.sleep(self.TIME_AUTO_SCAN)

    def scan(self):
        """
           send mensage in broadcast and wait answers
           wait no more then TIMEOUT_TO_ANSWER
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(self.TIMEOUT_TO_ANSWER)

        #Send mensage in Broadcast
        s.sendto(b'Alive?', ('192.168.0.255', self.MYPORT))

        online = []
        while True:
            try:
                message, address = s.recvfrom(4096)
                if message == b'I am here':
                    online.append(address[0])
            except socket.timeout:
                self.online = online
                break

    def answer_scan(self):
        """
        """
        host = ''                               # Bind to all interfaces

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind((host, self.MYPORT))

        myip = my_ip()
        while True:
            try:
                message, address = s.recvfrom(4096)
                #if message == b'Alive?' and address[0] != myip :
                    # Acknowledge it.
                s.sendto(b"I am here", address)
            except:
                pass

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
    print("Estabelecendo conexão {}".format(host[1]), flush = True)
    #try connect but if serve don't create a sockt yet wait 1 sec.
    while 1:
        try:
            client.connect(host)
            break
        except ConnectionRefusedError:
            print('.', flush = True)
            time.sleep(1)
    print("Conectado, \ntransferindo arquivo", flush = True)

    sended = 0
    msg = transf_file.read(1024)
    readed = len(msg)
    while msg:
        sended += client.send(msg)
        if sended != readed:
            print('Readed: {}, Sended: {}'.format(readed, sended))
            print('ERRO: Conexão falhou ao enviar o arquivo.\n port:{}'.format(host[1]))
            return
        msg = transf_file.read(1024)
        readed += len(msg)

    #confirm if send is correct
    #TODO if not correct resend
    #size = client.recv(16)
    #print('--------------------> {}'.format(int(size)))

    print('--------------------------------> port: {}'.format(host[1]))
    client.close()

def recive_file(server, file_name):
    """ Recive a file with socket
        Transfer with socket because XMLRPC transfer very slower than socket

        host: tuple (str ip, int port)
        file_name: str with name, verify_key or name of file
    """

    server.listen(1)

    file_save = open(file_name, "wb")
    con, server_name  = server.accept()
    print("Conexão estabelecidada, \nrecebendo arquivo.", flush = True)
    msg = con.recv(1024)
    recived = len(msg)
    while msg:
        file_save.write(msg)
        msg = con.recv(1024)
        recived += len(msg)
    file_save.close()
    con.send(bytes(recived))
    con.close()
    print("Arquivo recebido.", flush = True)

def my_ip():
    """ this function create a socket connection
    to get a real ip address.
    return - string with ip
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('1.1.1.1', 0))
    address = s.getsockname()[0]
    s.close()
    return address

def file_name_storage(verify_key):
    """
    keep only a name string in hex
    """
    hexa = binascii.b2a_hex(verify_key)
    name = str(hexa)[2:-1]
    return name

def port_using(port):
    """
    test if port is in using in other transfer (thread)
    return the next port not using
    """
    sockt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip = my_ip()
    try:
        sockt.bind((ip,port))
        return port, sockt
    except OSError:
        sockt.close()
        return port_using(port+1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
