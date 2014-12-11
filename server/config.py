'''
Created on 23/11/2014

This module make every configurations and parsers on variables to system
The main class is Config that concentrates the vars and set it with others def

TO IMPORT:   package = server
             module = config
             configs = Config() -> end of this module
therefor 
from server.config import configs

@author: mario
'''


import os
import logging
import argparse
import configparser
import database

import misc



class Config():
    '''
    Start every config vars to system
    ''' 

    #where directory flexa was called
    _dir_called = os.getcwd()
    _dir_file = _dir_called + "/data/"
    _port_sync = 53000
    __version__ = '0.1'

    #configs to start server_cli
    ip = None
    port = None

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
        parser.add_argument('-p', '--port', nargs=1, help='define server port')
        parser.add_argument('-d', '--daemon', action='store_true', help='daemonize server')
        parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
        parser.add_argument('-L', '--LOCAL', action='count', help='enable local server')
        version_info = '%(prog)s {}'.format(self.__version__)
        parser.add_argument('--version', action='version', version=version_info)
    
        return parser




    def load_config(self, config_path = ''):
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




    def parser(self):
        #Parse the user choices
        parser = self.usage()
        args = parser.parse_args()
    
        #Name of the server config file
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

        if args.LOCAL:
            misc.Ping.LOCAL = False
    
    
        self.ip = ip
        self.port = port



#object that have every configurations vars
configs = Config()