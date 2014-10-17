#!/usr/bin/env python3

"""Implements the server class and all it's supported functions"""

import os
import logging
import argparse
import configparser
import database
from threading import Thread

from rpc import RPCThreadingServer
from rpc import RPCServerHandler
import misc

__version__ = '0.1'

#where directory flexa was called
_dir_called = os.getcwd()
_dir_file = _dir_called + "/files/"
_port_sync = 53000


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
        port = 5000
    """

    config = configparser.SafeConfigParser()
    #This generate a list of default configs
    config.read_string(default_config)
    #If no file is found or is empty, this is ignored
    config.read(config_path, encoding='utf-8')

    return config

def parser():
    #Parse the user choices
    parser = usage()
    args = parser.parse_args()

    #Name of the server config file
    config_path = 'flexa-server.ini'
    config = load_config(config_path)

    #directory to save files
    if not os.path.exists(_dir_file):
        os.makedirs(_dir_file)

    #Parse args and set the user choices
    #Verbose -v show general information; -vv show debug information
    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)

    #Override default IP
    if args.ip:
        ip = args.ip[0]
        config.set('Network', 'host', ip)
        #Write new configuration file
        with open(config_path, mode='w', encoding='utf-8') as outfile:
            config.write(outfile)
    else:
        ip = config.get('Network','host')
        if not ip:
            ip = misc.my_ip()

    #Override default port
    if args.port:
        port = int(args.port[0])
        config.set('Network', 'port', args.port[0])
        #Write new configuration file
        with open(config_path, mode='w', encoding='utf-8') as outfile:
            config.write(outfile)
    else:
        port = int(config.get('Network','port'))

    return ip, port


class Server(object):
    """Class to receive messages from hosts"""


    def __init__(self, connection):

        """
        Variables:
        connection (tuple)
            host -- ip address or hostname to listen
            port -- port to listen to requests

        """

        #connect database
        self.db = database.DataBase()


        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("server")
        self.logger.info("Listening on {}:{}".format(ip, port))
        # register all functions
        self.register_operations(server)
        # create and server object
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nSignal of interrupt recived.")
        except:
            print("\nSomething made server stop.")
        finally:
            server.shutdown()
            print("\nServer stopped!")

    def register_operations(self, server):
        """Register all operations supported by the server in the server
        objects
        """
        server.register_function(self.list_files)
        server.register_function(self.still_alive)
        server.register_function(self.give_file)
        server.register_function(self.get_file)
        server.register_function(self.get_salt)
        server.register_function(self.update_file)

    def list_files(self, home_key):
        """Show every files in that directory
        """
        return os.listdir('.')

    def still_alive(self):
        return 1

    def give_file(self, ip, port, verify_key):
        """ give files to client
            ip: string with ip, address of client
            file_name: in a future this is a hash of file
        """
        host = (ip, port)
        misc.send_file(host, verify_key)
        #FIXME every rpc call return something - put sent confirmation
        return 0


    def get_file(self, file_name, keys, dir_key, user_id, type_file):
        """get file from client
           file_name: name of file that will save in server - verify_key
           keys: tupĺe (0 verify_key, 1 write_key, 2 read_key, 3 salt) strings
        """

        new_file = database.File(keys[0], keys[3], keys[1], keys[2], file_name, dir_key, user_id, type_file)
        self.db.add(new_file)

        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        print('name do arquivo: {}'.format(file_name), flush = True)
        thread = Thread(target = misc.recive_file, args = (sockt, _dir_file + keys[0]))
        thread.start()
        #TODO: set timout to thread

        return port

    def update_file(self, verify_key, write_key):
        """get file from client
           keys: tupĺe (0 verify_key, 1 read_key, 2 write_key, 3 salt) strings
        """
        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        if not (self.db.update_file(verify_key, write_key)):
            return False

        thread = Thread(target = misc.recive_file, args = (sockt, _dir_file + verify_key))
        thread.start()
        #TODO: set timout to thread

        return port

    def get_salt(self, file_name, dir_key, user_id):
        """make a call in data base to find file
        if found return your salt
        else return 0
        """ 
        return self.db.salt_file(file_name, dir_key, user_id)

class Sync(object):

    def __init__(self, connection, broadcast):
        #run a daemon to find hosts online
        find_hosts = misc.Ping(broadcast)
        find_hosts.daemon()

        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("server")
        self.logger.info("Listening on {}:{}".format(ip, port))
        # register all functions
        server.register_function(self.still_alive)
        # create and server object
        try:
            server.serve_forever()
        except:
            print("Fechando o modulo de sincronismo")
            server.shutdown()

    def still_alive(self):
        return 1

    def send_update(self):
        pass

    def update(self):
        pass

##########################################################################################

def main():
    """
    The function called when the program is executed on a shell
    """

    ip, port = parser()

    #FIXME interface da rede
    broadcast = '192.168.0.255'

    connection = (ip, _port_sync)
    th = Thread(target = Sync, args = (connection, broadcast), daemon = True)
    th.start()

    #Start server
    connection = (ip, port)
    Server(connection)


if __name__ == '__main__':
    main()
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
