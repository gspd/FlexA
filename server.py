#!/usr/bin/env python3

"""Implements the server class and all it's supported functions"""

import os
import logging
import socket
from threading import Thread

from rpc import RPCThreadingServer
from rpc import RPCServerHandler

class Server(object):
    """Class to receive messages from hosts"""

    def __init__(self, host=None, port=5500):
        """
        Variables:
        host -- ip address or hostname to listen
        port -- port to listen to requests

        """

        if not host:
            host = socket.gethostname()

        server = RPCThreadingServer((host, port),
                                    requestHandler=RPCServerHandler)
        ip, port = server.server_address

        # Create local logging object
        self.logger = logging.getLogger("server")

        self.logger.info("Listening on {}:{}".format(ip, port))

        # register all functions
        self.register_operations(server)

        # create and server object
        server.serve_forever()

    def register_operations(self, server):
        """Register all operations supported by the server in the server
        objects

        """

        server.register_function(self.list_directory)


    def list_directory(self):
        """Example function to list a directory and return to the caller

        """

        return os.listdir('.')

if __name__ == '__main__':
    # TODO: handle cli arguments to change server parameters

    # Enable -v: set logging to level=INFO
    # need to implement -vv to level=DEBUG
    logging.basicConfig(level=logging.INFO)

    s = Server()
