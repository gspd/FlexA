#!/usr/bin/env python3

"""Provide general tools to FlexA."""

import sys
import socket
import time
from threading import Thread
from distutils.util import strtobool

class Ping(object):
    """ Times to scan network
        the time between one scan and next is
        TIMEOUT_TO_ANSWER + TIME_AUTO_SCAN
    """
    TIMEOUT_TO_ANSWER = 2
    TIME_AUTO_SCAN = 3
    MYPORT = 51400

    online = None

    #flag to enable local servers - default: enable 
    LOCAL = True

    def __init__(self, broadcast):
        """ receive broadcast of network
            String like `192.168.2.255`
        """
        self.broadcast = broadcast
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
        try:
            s.sendto(b'Alive?', (self.broadcast, self.MYPORT))
        except:
            print("An error occurs. Could't send broadcast message.") 

        online = []
        while True:
            try:
                message, address = s.recvfrom(4096)
                if (message == b'I am here'):
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
                if (message == b'Alive?') and (address[0] != myip):
                    s.sendto(b"I am here", address)
                elif message == b'Alive?' and (address[0] == myip) and (self.LOCAL):
                    s.sendto(b"I am here", address)
            except:
                print("Náo consegui responder o ping!")


def split_file(file_name, nparts):
    """
        split file in nparts and save it with ".n"
        where n is number of part
    """

    with open(file_name, "rb") as file_pointer:
        #config size of file
        size = file_pointer.seek(0,2)
        #set in initial of file
        file_pointer.seek(0)
        #size of parts
        chucksize = size//nparts

        try:
            #get parts but not the last
            for i in range(nparts-1):
                file_part = open( file_name + '.' + str(i), 'wb' )
                file_part.write( file_pointer.read(chucksize) )
                file_part.close()

            #save last part
            file_part = open(file_name + '.' + str(nparts-1), 'wb')
            #get the last part that can has size<chucksize
            file_part.write( file_pointer.read( size - file_pointer.tell() ) )
            file_part.close()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return False

    return True

def join_file(name_parts, name_merged):
    """
        Join parts of file and save in name_merged 
        receive:
            name_parts - list of files name to join
            name_merged - file name where will save merged 
    """

    try:
        with open(name_merged, "wb") as merged:
            for part in name_parts:
                with open(part, "rb") as file_part:
                    merged.write( file_part.read() )
    except:
        return False

    return True

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


def send_file(host, file_name):
    """ Send a file with socket to client
        Transfer with socket because XMLRPC transfer very slower than socket

        host: tuple (ip, port)
        transf_file: name of file
    """

    transf_file = open(file_name,"rb")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #try connect but if serve don't create a sockt yet wait 1 sec.
    #after 10 errors, cancel connection
    attempt = 0
    while 1:
        try:
            client.connect(host)
            break
        except ConnectionRefusedError:
            print('Try connect to transfer file. ', attempt, flush = True)
            attempt+=1
            if attempt == 10:
                return 1
            time.sleep(1)

    sended = 0
    msg = transf_file.read(1024)
    readed = len(msg)
    while msg:
        sended += client.send(msg)
        if sended != readed:
            print('Readed: {}, Sended: {}'.format(readed, sended))
            print('ERRO: Conexão falhou ao enviar o arquivo.\n port:{}'.format(host[1]))
            return 1
        msg = transf_file.read(1024)
        readed += len(msg)

    client.close()
    transf_file.close()

    return 0

def receive_file(sock, file_name):
    """ Recive a file with socket
        Transfer with socket because XMLRPC transfer very slower than socket

        sock: a socket object where is instance that will receive file
        file_name: str with name, verify_key or name of file
    """

    sock.listen(1)

    file_save = open(file_name, "wb")
    con, server_name  = sock.accept()
    msg = con.recv(1024)
    received = len(msg)
    while msg:
        file_save.write(msg)
        msg = con.recv(1024)
        received += len(msg)
    file_save.close()

def my_ip():
    """ this function create a socket connection
    to get a real ip address.
    return - string with ip
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('1.1.1.1', 0))
    except:
        sys.exit("Error in Network interface")
    address = s.getsockname()[0]
    s.close()
    return address

def port_using(port):
    """
    test if port is in using if not return number of port and your socket opening 
    if in using return the next port (port+1) to port_using - recursive
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
