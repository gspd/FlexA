'''
Created on 15/12/2014

@author: mario
'''

import argparse
import misc
import os
import crypto
import getpass
import sys
import hashlib
import configparser
import logging

class Config(object):
    '''
    Set every configs to client flexa
    '''

    __version__ = "1.0"

    #set where is client home
    _home = None
    
    #mapped directory
    _data_dir = None
    
    #directory where configurations are stored
    _config_dir = None
    
    #file where configurations are stored
    _config_filepath = None
    
    #where directory flexa was called
    _current_local_dir = None
    
    #directory relative by system. directories of flexa
    _current_relative_dir = None
    
    #port connection server
    #_PORT_SERVER = None

    #Every set args of parser
    args = None
    
    loaded_config = None


    def __init__(self):
        '''
        Constructor
        '''
        self._home = os.getenv("HOME")
        self._data_dir = os.path.join(self._home, 'drive')
        self._config_dir = os.path.join(self._home, '.flexa')
        self._config_filepath = os.path.join(self._config_dir, 'flexa.ini')
        self._current_local_dir = os.getcwd()
        self._current_relative_dir = None
        
        #port connection server
        #self._PORT_SERVER = 5000

        if not os.path.exists(self._config_dir):
            #if don't exist diretory-flexa in user home then is your first time
            #is necessary create RSA and default directory
            self.first_time()
        else:
            if ( not self._data_dir in self._current_local_dir):
                #flexa was invoked outside of mapped directory
                sys.exit("You are calling FlexA outside your mapped directory.")

        self._current_relative_dir = self._current_local_dir.split(self._data_dir)[1]
        self._current_relative_dir = os.path.join('/', self._current_relative_dir)

        parser = self.usage()
        self.loaded_config = self.load_config()

        #If no option is given, show help and exit
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(2)
    
        #Parse the user choices
        self.args = parser.parse_args()

        #Parse args and set the user choices
        #Verbose -v show general information; -vv show debug information
        if self.args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif self.args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)

    def usage(self):
        """Generate user help and parse user choices"""
    
        parser = argparse.ArgumentParser(
                description='A New Flexible and Distributed File System')
        #The following options are mutually exclusive
        mxg = parser.add_mutually_exclusive_group()
        mxg.add_argument('-p', '--put', metavar='FILE', nargs='+', help='send file to server')
        mxg.add_argument('-g', '--get', metavar='FILE', nargs='+', help='receive file from server')
        mxg.add_argument('-d', '--delete', metavar='FILE', nargs='+', help='delete file from server')
        mxg.add_argument('-s', '--snapshots', metavar='FILE', nargs='+', help="shows history of file snapshots")
        mxg.add_argument('-r', '--recover', metavar=('FILE','VERSION'), nargs=2, help='recovers snapshot VERSION of FILE')
        mxg.add_argument('-l', '--list', action='count', default=0, help="list current directory content at the server")

        #These options can be used in combination with any other
        parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
        version_info = '%(prog)s {}'.format(self.__version__)
        parser.add_argument('--version', action='version', version=version_info)
    
        return parser
    
    def load_config(self):
        """Load default config and parse user config file
    
        Input parameters:
        _config_filepath -- path of the configuration file
        """

        default_config = """
        #All network configuration goes here
        [Network]
            interface =
            hostname =
            port =
            netmask =
        #User related configuration
        [User]
            private key =
            hash client =
            enable snapshots =
        """

        config = configparser.SafeConfigParser()
    
        #This generate a list of default configs
        config.read_string(default_config)
    
        #If no file is found or is empty, this is ignored
        config.read(self._config_filepath, encoding='utf-8')

        return config

    def first_time(self ):

        """ Create configurations file, folders and a new RSA key for user """

        print("First time you're running FlexA.\nSome configuration is necessary.")

        if(misc.query_yes_no('Do you want to configure FlexA now?')):
            #make dirs to map and save configurations

            # Create dir for store user file (MAPPED DIRECTORY)
            try:
                os.makedirs(self._data_dir)
            except OSError:
                sys.exit("ERROR: Couldn't create folder at '" + self._data_dir + "'.")

            # Create dir for store flexa config files
            try:
                os.makedirs(self._config_dir)
            except OSError:
                sys.exit("ERROR: Couldn't create folder at '" + self._config_dir+ "'.")

        else:
            print("FlexA startup was canceled by the user.")
            sys.exit(1)

        config = self.load_config()

        if (misc.query_yes_no('Do you want to enable file snapshots?\
                                This will require more storage space at the servers')):
            config.set('User', 'enable snapshots', "1")
        else:
            config.set('User', 'enable snapshots', "0")

        if (misc.query_yes_no('Do you want to create RSA key now?')):
            key_filename = self.generate_new_key()
            config.set('User', 'private key', key_filename)

            p = None
            try:
                p = getpass.getpass("Type your password to unlock key:")
            except KeyboardInterrupt:
                sys.exit(2)

            try:
                cryp = crypto.open_rsa_key(key_filename, p)
            except:
                sys.exit(1)

            hashe = hashlib.sha256()
            hashe.update(cryp.publickey().exportKey('PEM'))

            config.set('User', 'hash client', hashe.hexdigest())
            print("Configurations done.")
        else:
            print("Please add the path to your private key in flexa.ini")
        
        #Write configuration file
        try:
            with open(self._config_filepath, mode='w', encoding='utf-8') as outfile:
                print("FlexA configuration file is at ", self._config_filepath)
                config.write(outfile)
        except:
            print("Couldn't write configuration file.")
            

        print("Run FlexA again, to start with the system configured.")
        sys.exit(0)


    def generate_new_key(self):
        """Generate a new RSA key and returns it's filename
        Input parameters:
        """

        #Ask the desired name and password to the file
        filename=""
        if (misc.query_yes_no("Filename is currently 'id_rsa', do you want to change it?", default="no")):
            try:
                filename = input('New filename: ')
            except KeyboardInterrupt:
                sys.exit(2)
        if not filename:
            filename = "id_rsa"
        filepath = os.path.join(self._config_dir, filename)

        password = ""
        if (misc.query_yes_no('Do you want to add a password?', default="no")):
            try:
                password = getpass.getpass('Password: ')
            except KeyboardInterrupt:
                sys.exit(2)

        #Generate the RSA key, its file and store file path on config file
        crypto.generate_rsa_key(filepath, password)
        print('RSA key generated!')

        return filepath
