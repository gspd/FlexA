#!/usr/bin/env python3

"""Provide communication functionality between each host"""

import os
import sys
import socket
import socketserver
import logging
import pickle
from threading import Thread, Condition

# Create local logging object
logger = logging.getLogger(__name__)

__authors__ = ["Thiago Kenji Okada", "Leandro Moreira Barbosa"]

_BUFFER_SIZE = 4096

class Types(object):
    SEND_FILE = 0x1
    LIST_FILES = 0x2
    REQUEST_FILE = 0x4
    EXCEPTION = 0x8
    ERROR = 0x10
    EXIT = 0x20

    strtypes_dict = {SEND_FILE: "Send a file to a host.",
                     LIST_FILES: "List available files.",
                     REQUEST_FILE: "Request file download.",
                     EXCEPTION: "Exeception ocurred.",
                     ERROR: "Error ocurred.",
                     EXIT: "Disconnected from remote host."}

    def strtypes(mtype):
        try:
            return Types.strtypes_dict[mtype]
        except KeyError:
            return "Unknown message type."

class Error(object):
    UNKNOWN_ERROR = 0x1
    NOT_IMPLEMENTED = 0x2

    strerror_dict = {UNKNOWN_ERROR: "Unknown error.",
                     NOT_IMPLEMENTED: "Request not implemented."}

    def strerror(error):
        try:
            return Error.strerror_dict[error]
        except KeyError:
            return "Unknown error code"

class InvalidMessageException(Exception):
    pass

def encode(mtype, data):
    """Encode a message and return an object to be send through a socket.

    Variables:
    mtype -- type of the message to be sent. This type has DOES have influency
    on the kind of data to be sent over.
    data -- object containing data to be sent to the remote host. The data will
    be serialized to be sent through the network using the Pickle module.

    The encoding process of this function is always compatible with the
    decoding process supplied in the same version of the system.

    So:
    decode(encode(mtype,data)) == (type, data)

    """

    return pickle.dumps((mtype, data))

def decode(message):
    """Decode a message and return a tuple (mtype, data). See
    encode(mtype, data) for more information.

    Variables:
    message -- message previously encoded using the encode(mtype, data) function

    The decoding process of this function is always compatible with the
    encoding process supplied in the same version of the system.

    So:
    encode(decode(msg)) == msg

    """

    return pickle.loads(message)


class ReceiveHandler(socketserver.BaseRequestHandler):
    """Class that defines the server behavior for each connection"""

    def setup(self):
        logger.info('{}:{} connected'.format(*self.client_address))

    def handle(self):
        while True:
            try:
                data = decode(self.request.recv(_BUFFER_SIZE))
            except EOFError:
                break

            logger.debug('Data received: {}'.format(data))

            # The first member of the tuple is always the type of the message
            if data[0] == Types.SEND_FILE:
                answ_type = Types.ERROR
                answ_data = Error.NOT_IMPLEMENTED
            elif data[0] == Types.LIST_FILES:
                answ_type = data[0]
                answ_data = ",".join(
                    [f for f in os.listdir('.') if os.path.isfile(f)])
            elif data[0] == Types.REQUEST_FILE:
                answ_type = Types.ERROR
                resp_data = Error.NOTIFY
            elif data[0] == Types.EXCEPTION:
                answ_type = Types.ERROR
                answ_data = Error.NOT_IMPLEMENTED
            elif data[0] == Types.ERROR:
                answ_type = Types.ERROR
                answ_data = Error.NOT_IMPLEMENTED
            elif data[0] == Types.EXIT:
                break
            else:
                # Return an error if the type is not found
                answ_type = Types.ERROR
                answ_data = Error.UNKNOWN_ERROR

            answer = encode(answ_type, answ_data)
            self.request.sendall(answer)

    def finish(self):
        logger.info('{}:{} disconnect'.format(*self.client_address))

class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Class to create the server"""
    pass

class Receive(object):
    """Class to receive messages from hosts"""

    def __init__(self, host=None, port=5500):
        """
        Variables:
        host -- ip address or hostname to listen
        port -- port to listen to requests

        """

        if not host:
            host = socket.gethostname()

        server = Server((host, port), ReceiveHandler)
        ip, port = server.server_address
        logger.info("Listening on {}:{}".format(ip, port))
        # server thread
        t_server = Thread(target=server.serve_forever)
        t_server.daemon = True
        t_server.start()

class Send(object):
    """Class to send messages to hosts"""

    def __init__ (self, ip=None, port=5500):
        """
        Variables:
        ip -- destination ip address
        port -- destination port

        """

        if not ip:
            ip = socket.gethostname()

        try:
            dest = (ip, port)
            self.__sock = socket.create_connection(dest, timeout=10)
        except IOError:
            err = ('Failed to create socket {}:{}.'.format(*dest))
            logger.critical(err)
            sys.exit(err)

    def send(self, mtype, data):
        self.__sock.sendall(encode(mtype, data))
        try:
            answer = decode(self.__sock.recv(_BUFFER_SIZE))
        except EOFError:
            logger.warning('Conection closed by the remote host.')
            return

        logger.debug(answer)

        if answer[0] == Types.ERROR:
            logger.warning(Error.strerror(answer[1]))

    def close(self):
        self.__sock.close()

class SendThread(Thread):
    """Send message to a remote host asynchronously"""

    def __init__ (self, ip=None, port=5500):
        """
        Variables:
        ip -- destination ip address
        port -- destination port

        """

        Thread.__init__(self)

        if not ip:
            ip = socket.gethostname()

        try:
            dest = (ip, port)
            self.__sock = socket.create_connection(dest, timeout=10)
        except IOError:
            err = ('Failed to create socket {}:{}.'.format(*dest))
            logger.critical(err)
            sys.exit(err)

        self.__lock = Condition()
        self.__finish = False
        self.__data = None
        self.__type = None

    def __enter__(self):
        self.start()
        return self

    def run(self):
        """Function to run when the Thread starts"""

        while True:
            self.__lock.acquire()
            # Wait for data or finish command
            while not (self.__data or self.__finish):
                self.__lock.wait()

            # Only finish when data is gone
            if self.__finish and not self.__data:
                self.__lock.release()
                break

            self.__sock.sendall(encode(self.__type, self.__data))
            answer = decode(self.__sock.recv(_BUFFER_SIZE))

            logger.debug(answer)

            if answer[0] == Types.ERROR:
                logger.warning(Error.strerror(answer[1]))

            self.__type = None
            self.__data = None
            self.__lock.release()

        self.__sock.close()

    def send(self, mtype, data):
        """Send new message to the remote server
        """

        self.__lock.acquire()

        if self.__finish:
            logger.info("Thread already finished.")
        if not self.__data:
            self.__type = mtype
            self.__data = data
        else:
            logger.warning("Previous message not sent.")

        self.__lock.notify()
        self.__lock.release()

    def __exit__(self, exc_type, exc_value, traceback):
        """Join the main thread before exiting with statement"""

        self.disconnect()
        self.join()

    def disconnect(self):
        # TODO: warn the server before EXIT
        self.__lock.acquire()
        self.__finish = True
        self.__lock.notify()
        self.__lock.release()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
