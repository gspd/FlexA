#!/usr/bin/env python3

"""Implements the server class and all it's supported functions"""

import os
import logging
import socket
import argparse
import configparser
from threading import Thread

from rpc import RPCThreadingServer
from rpc import RPCServerHandler

__version__ = '0.1'

def usage():
    """Generate user help and parse user choices"""

    parser = argparse.ArgumentParser(
            description='Server for a New Flexible and Distributed File \
                    System')
    parser.add_argument('-i', '--ip', nargs=1, help='define server IP')
    parser.add_argument('-p', '--port', nargs=1, help='define server port')
    parser.add_argument('-d', '--daemon', action='store_true',
            help='daemonize server')
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='increase output verbosity')
    version_info = '%(prog)s {}'.format(__version__)
    parser.add_argument('--version', action='version', version=version_info)

    return parser

def load_config(config_path = ''):
    """Load default config and parse user config file

    Input parameters:
    config_path -- path of the configuration file
    """

    default_config = """
    #Network related configuration
    [Network]
        host =
        port = 5500
    """

    config = configparser.SafeConfigParser()
    #This generate a list of default configs
    config.read_string(default_config)
    #If no file is found or is empty, this is ignored
    config.read(config_path, encoding='utf-8')

    return config

def main():
    """The function called when the program is executed on a shell"""

    #Parse the user choices
    parser = usage()
    args = parser.parse_args()

    #Name of the server config file
    config_path = 'flexa-ng.ini'
    config = load_config(config_path)

    #Parse args and set the user choices
    #Verbose -v show general information; -vv show debug information
    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)

    #Override default IP
    if args.ip:
        ip = args.ip[0]
    else:
        ip = config.get('Network','host')

    #Override default port
    if args.port:
        port = int(args.port[0])
    else:
        port = int(config.get('Network','port'))

    #Start server
    s=Server(ip,port)

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
        server.register_function(self.still_alive)

    def list_directory(self):
        """Example function to list a directory and return to the caller

        """
        return os.listdir('.')
    
    def still_alive(self):
        return 1

if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
