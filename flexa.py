#!/usr/bin/env python3

"""Implements a client and a command line interface"""

import argparse
import sys
import os
import getpass
import configparser
import hashlib
from threading import Thread
from xmlrpc.client import ServerProxy

import crypto
import misc
from file.file import File

__version__ = "0.1"

#******* CONFIGS ************#

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

#******* CONFIGS ************#

def usage():
    """Generate user help and parse user choices"""

    parser = argparse.ArgumentParser(
            description='A New Flexible and Distributed File System')
    #The following options are mutually exclusive
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--put', metavar='FILE', nargs='+', help='send file to server')
    group.add_argument('-g', '--get', metavar='FILE', nargs='+', help='receive file from server')
    group.add_argument('-l', '--list', action='count', default=0, help='list file from server')
    group.add_argument('-n', '--newkey', action='store_true', help='generate new user key')
    #These options can be used in combination with any other
    parser.add_argument('-v', '--verbose', action='count', default=0, help='increase output verbosity')
    version_info = '%(prog)s {}'.format(__version__)
    parser.add_argument('--version', action='version', version=version_info)

    return parser

def load_config(_config_path = ''):
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
    config.read(_config_path, encoding='utf-8')

    return config

def generate_new_key(dir_config):
    """Generate a new RSA key and returns it's filename

    Input parameters:
    """

    #Ask the desired name and password to the file
    try:
        filename = input('Filename? (default: id_rsa) ')
        if not filename:
            filename = "id_rsa"
    except KeyboardInterrupt:
        sys.exit(2)
    filename = dir_config + "/" + filename
    try:
        password = getpass.getpass('Password? ')
    except KeyboardInterrupt:
        sys.exit(2)
    #Generate the RSA key and store it's path on config file
    crypto.generate_rsa_key(filename, password)
    print('RSA key generated!')

    return filename

def send_file(file_name, rsa_dir):
    """
    send file from client to server
    """

    local_file = _flexa_dir + file_name
    file_name_enc = file_name+".enc"
    local_file_enc = _flexa_dir + file_name_enc

    server, ip_server = rpc_server()
    rsa = crypto.open_rsa_key(rsa_dir,)

    user_id = 1 #FIXME get a real user id
    #verify if this file exist (same name in this directory)
    dir_key = "home" #FIXME set where is.... need more discussion
    #ask to server if is update or new file
    salt = server.get_salt(file_name, user_id)

    #generate every keys in string return tuple:
    #(0 - verify, 1 - write, 2 - read, 3 - salt)
    keys = crypto.keys_string(salt, rsa)
    try:
        print(local_file)
        f = open(local_file, "rb") #verify if exist file
        crypto.encrypt_file(keys[0][0:32], local_file, local_file_enc, 16)
        f = open(local_file_enc, "rb") #verify if create file crypted
        f.close()
    except FileNotFoundError:
        sys.exit("File not found.\nTry again.")

    type_file = "f"

    #if salt has a value then is update. because server return a valid salt
    if salt:
        port = server.update_file(keys[0], keys[1])
    else:
        #server return port where will wait a file
        port = server.get_file(file_name, keys, dir_key, user_id, type_file)

    if not port:
        sys.exit("Some error occurred. Maybe you don't have permission to \
                write. \nTry again.")

    host = (ip_server, port)
    misc.send_file(host, local_file_enc)
    #remove temp crypt file
    os.remove(local_file_enc)

def recive_file(file_name, rsa_dir):
    """
    recive file from server
    """

    file_name_enc = file_name + '.enc'
    local_file = _flexa_dir + file_name
    local_file_enc = _flexa_dir + file_name_enc

    ip = misc.my_ip()
    port, sock = misc.port_using(4001)
    #make a thread that will recive file in socket
    thr = Thread(target = misc.recive_file, args = (sock, local_file_enc))

    server = rpc_server()
    print(server)
    user_id = 1
    dir_key = "home"
    salt = server.get_salt(file_name, user_id)

    if (salt == 0):
        print("This file can't be found")
        return

    rsa = crypto.open_rsa_key(rsa_dir)
    keys = crypto.keys_string(salt, rsa)

    thr.start()
    #ask to server a file with name (keys[0] = hash)
    #client ip and your port to recive file
    print(server.give_file(ip, port, keys[0]))
    thr.join()

    crypto.decrypt_file(keys[0][0:32], file_name_enc, local_file,16)
    #remove temp crypt file
    os.remove(local_file_enc)

def list_files():
    """
    Search every file from verify_key
        verify_key is directory where called this operation - answer is a dictionary of files and yours attributes 
    """
    server, ip = rpc_server()

    dir_current = _dir_called.split(_flexa_dir[:-1])[1]
    if dir_current == '':
        dir_current = '/'
    print(dir_current)

    for dic_file in server.list_files("home"):
        print(dic_file['name'])

def rpc_server():
    """
    Find a servers online and make connection
    """

    host = misc.Ping('255.255.255.255')
    host.TIMEOUT_TO_ANSWER = 0.3
    host.scan()
    while not host.online:
        host.TIMEOUT_TO_ANSWER += 0.3
        host.scan()
        if host.TIMEOUT_TO_ANSWER > 1.5:
            print("Can't found servers. \n Time out.")
            sys.exit(0)

    #online[0] is the first server that answer
    ip_server = host.online[0]
    server_addr = 'http://{}:{}'.format(ip_server, _PORT_SERVER)
    return ServerProxy(server_addr), ip_server

def first_time():

    """ Create configurations file, folders and a new RSA key for user """

    print("First time you use it.\nSome configuration is necessary.")

    if(misc.query_yes_no("Do you want create flexa configurations?")):
        #make dirs to map and save configurations

        # Create dir for store user file (MAPPED DIR)
        try:
            os.makedirs(_flexa_dir)
        except OSError:
            sys.exit("ERROR: Can not create folder at '" + _flexa_dir + "'.")

        # Create dir for store flexa config files
        try:
            os.makedirs(_config_dir)
        except OSError:
            sys.exit("ERROR: Can not create folder at '" + _config_dir+ "'.")


    else:
        print("Starting in Flexa was canceled.")
        sys.exit(1)

    config = load_config(_config_path)

    if (misc.query_yes_no("Do you want creat RSA key now?")):
        filename = generate_new_key(_config_dir)
        config.set('User', 'private key', filename)

        p = None
        try:
            p = getpass.getpass("Enter with your password to unlock key:")
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

            with open(_config_path, mode='w', encoding='utf-8') as outfile:
                print("Your configuration file are at", _config_path)
                config.write(outfile)
        except:
            print("Can not write config file.")
    else:
        print("Please, add path to your key in your flexa.ini manually")
    
    
    print("Run FlexA again, to start with system configured.")
    sys.exit(0)


def createNewUserKey(config):

    """ Create new RSA key for user and add it to config """
    filename = generate_new_key()
    config.set('User', 'private key', filename)
    cryp = crypto.open_rsa_key(filename)
    hashe = hashlib.sha256()
    hashe.update(cryp.exportKey(format='DER'))
    config.set('User', 'hash client', hashe.hexdigest())

########################

def main():
    """The function called when the program is executed on a shell"""

    if not os.path.exists(_config_dir):
        #if don't exist diretory-flexa in user home then is your first time
        #is necessary create RSA and default directory
        first_time()
    else:
        if ( not _flexa_dir in _dir_called+'/'):
            #flexa was invoked outside of mapped directory
            sys.exit("You are calling flexa outside your mapped directory.")

    parser = usage()
    #If no option is given, show help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)

    #Parse the user choices
    args = parser.parse_args()

    config = load_config(_config_path)

    #Generate a new user key
    if args.newkey:
        #Checks if the user already has a key
        if os.path.exists(config.get('User', 'private key')):
            confirm = misc.query_yes_no("There is already a generated key, "
                    "generate another one?", default='no')
            if not confirm:
                sys.exit(2)

        createNewUserKey(config)

    #Send a file to server
    if args.put:
        for names in args.put:
            send_file(names, config.get('User', 'private key'))

    #Get a file from server
    if args.get:
        for names in args.get:
            recive_file(names, config.get('User', 'private key'))

    if args.list:
        list_files()
    #Write configuration file
    with open(_config_path, mode='w', encoding='utf-8') as outfile:
        config.write(outfile)


if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
