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

class Config(object):
    '''
    Set every configs to client flexa
    '''
        
    __version__ = "1.0"


    #set where is client home
    _home = os.getenv("HOME")
    #file where put configurations
    _config_dir = _home + '/.flexa'
    #where directory flexa was called
    _dir_called = os.getcwd()
    #dir to save configs
    _config_path = _config_dir+'/flexa.ini'
    #mapped dir
    _flexa_dir = _home+"/drive/"
    #port connection server
    _PORT_SERVER = 5000
    #directory relative by system. directories of flexa
    _dir_current_relative = None


    #Every set args of parser
    args = None
    
    loaded_config = None


    def __init__(self):
        '''
        Constructor
        '''

        if not os.path.exists(Config._config_dir):
            print(Config._config_dir)
            #if don't exist diretory-flexa in user home then is your first time
            #is necessary create RSA and default directory
            self.first_time()
        else:
            if ( not Config._flexa_dir in Config._dir_called+'/'):
                #flexa was invoked outside of mapped directory
                sys.exit("You are calling FlexA outside your mapped directory.")

        Config._dir_current_relative = Config._dir_called.split(Config._flexa_dir[:-1])[1] + '/'
        if Config._dir_current_relative == '':
            Config._dir_current_relative = '/'


        parser = self.usage()
        Config.loaded_config = self.load_config()

        #If no option is given, show help and exit
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(2)
    
        #Parse the user choices
        Config.args = parser.parse_args()


    def usage(self):
        """Generate user help and parse user choices"""
    
        parser = argparse.ArgumentParser(
                description='A New Flexible and Distributed File System')
        #The following options are mutually exclusive
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-p', '--put', metavar='FILE', nargs='+', help='send file to server')
        group.add_argument('-g', '--get', metavar='FILE', nargs='+', help='receive file from server')
        group.add_argument('-l', '--list', action='count', default=0, help='list file from server')
        group.add_argument('-d', '--delete', metavar='FILE', nargs='+', help='delete file from server')
        group.add_argument('-n', '--newkey', action='store_true', help='generate new user key')
        #These options can be used in combination with any other
        parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
        version_info = '%(prog)s {}'.format(Config.__version__)
        parser.add_argument('--version', action='version', version=version_info)
    
        return parser
    
    def load_config(self):
        """Load default config and parse user config file
    
        Input parameters:
        _config_path -- path of the configuration file
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
        """

        config = configparser.SafeConfigParser()
    
        #This generate a list of default configs
        config.read_string(default_config)
    
        #If no file is found or is empty, this is ignored
        config.read(Config._config_path, encoding='utf-8')

        return config

    def first_time(self ):

        """ Create configurations file, folders and a new RSA key for user """

        print("First time you're running FlexA.\nSome configuration is necessary.")

        if(misc.query_yes_no('Do you want to configure FlexA now?')):
            #make dirs to map and save configurations

            # Create dir for store user file (MAPPED DIRECTORY)
            try:
                os.makedirs(Config._flexa_dir)
            except OSError:
                sys.exit("ERROR: Couldn't create folder at '" + Config._flexa_dir + "'.")

            # Create dir for store flexa config files
            try:
                os.makedirs(Config._config_dir)
            except OSError:
                sys.exit("ERROR: Couldn't create folder at '" + Config._config_dir+ "'.")

        else:
            print("FlexA startup was canceled by the user.")
            sys.exit(1)

        config = Config.load_config(Config._config_path)

        if (misc.query_yes_no('Do you want to create RSA key now?')):
            filename = self.generate_new_key()
            config.set('User', 'private key', filename)

            p = None
            try:
                p = getpass.getpass("Type your password to unlock key:")
            except KeyboardInterrupt:
                sys.exit(2)

            try:
                cryp = crypto.open_rsa_key(filename,p)
            except:
                sys.exit(1)

            hashe = hashlib.sha256()
            hashe.update(cryp.exportKey(format='DER'))

            config.set('User', 'hash client', hashe.hexdigest())
            print("Configurations done.")

            #Write configuration file          
            try:
                with open(Config._config_path, mode='w', encoding='utf-8') as outfile:
                    print("Your configuration file are at", Config._config_path)
                    config.write(outfile)
            except:
                print("Can not write config file.")
        else:
            print("Please, add path to your key in your flexa.ini manually")

        print("Run FlexA again, to start with system configured.")
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
        filepath = Config._config_dir + "/" + filename

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