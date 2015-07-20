'''
Created on 23/11/2014

This module make every configurations and parsers on variables to system
The main class is Config that concentrates the vars and set it with others def

TO IMPORT:   package = server_pkg
             module = config
             configs = Config() -> end of this module
therefor 
from server_pkg.config import configs
Then configs is the object that has every configuration.

@author: mario
'''


import os
import logging
import argparse
import configparser
import database
import uuid

import misc



class Config(object):
    '''
    Start every config vars to system
    ''' 

    #where directory flexa was called
    _dir_called = os.getcwd()
    _dir_file = _dir_called + "/data/"
    __version__ = '0.1'

    #configs to start server_cli
    ip = None
    cli_port = None
    sync_port = None
    uid = None

    def __init__(self):
        '''
        Constructor
        '''

        self.parser()




    def usage(self):
        """Generate user help and parse user choices"""
    
        parser = argparse.ArgumentParser(
                description='Server for a New Flexible and Distributed File \
                        System')
        parser.add_argument('-i', '--ip', nargs=1, help='define server IP')
        parser.add_argument('-p', '--cliport', nargs=1, help='define client server port')
        parser.add_argument('-ps', '--syncport', nargs=1, help='define sync server port')
        parser.add_argument('-d', '--daemon', action='store_true', help='daemonize server_pkg')
        parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
        parser.add_argument('-L', '--LOCAL', action='count', default=0, help='disable local server_pkg [ default: enable]')
        version_info = '%(prog)s {}'.format(self.__version__)
        parser.add_argument('--version', action='version', version=version_info)
    
        return parser




    def load_config(self, config_path = ''):
        """Load default config and parse user config file
    
        Input parameters:
        config_path -- path of the configuration file
        """
    
        default_config = """
        #Metadata of Servers
        [General]
            uid =
            host =

        [Client]
            port = 5000

        [Sync]
            port = 15000
        """
    
        config = configparser.SafeConfigParser()
        #This generate a list of default configs
        config.read_string(default_config)
        #If no file is found or is empty, this is ignored
        config.read(config_path, encoding='utf-8')
    
        return config




    def parser(self):
        #Parse the user choices
        parser = self.usage()
        args = parser.parse_args()
    
        #Name of the server_pkg config file
        config_path = 'flexa-server.ini'
        config = self.load_config(config_path)
    
        #directory to save file
        if not os.path.exists(self._dir_file):
            os.makedirs(self._dir_file)
    
        #Parse args and set the user choices
        #Verbose -v show general information; -vv show debug information
        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
            database.DataBase._echo_db = True
    
        #Override default IP
        if args.ip:
            ip = args.ip[0]
            config.set('General', 'host', ip)
        else:
            ip = config.get('General','host')
            if not ip:
                ip = misc.my_ip()

        #Override default port
        if args.cliport:
            cli_port = int(args.cliport[0])
            config.set('Client', 'port', args.cliport[0])
        else:
            cli_port = int(config.get('Client','port'))

        if args.syncport:
            sync_port = int(args.port[0])
            config.set('Sync', 'port', args.port[0])
        else:
            sync_port = int(config.get('Sync','port'))

        #cat id of server_pkg
        self.uid = config.get('General', 'uid')
        if not self.uid:
            self.uid = uuid.uuid4().hex
            config.set('General', 'uid', self.uid)

        if args.LOCAL:
            misc.Ping.LOCAL = False


        self.ip = ip
        self.cli_port = cli_port
        self.sync_port = sync_port

        #Write new configuration file
        with open(config_path, mode='w', encoding='utf-8') as outfile:
            config.write(outfile)
