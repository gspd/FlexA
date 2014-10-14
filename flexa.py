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

__version__ = "0.1"

def usage():
    """Generate user help and parse user choices"""

    parser = argparse.ArgumentParser(
            description='A New Flexible and Distributed File System')
    #The following options are mutually exclusive
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--put', metavar='FILE', nargs='+',
            help='send file to server')
    group.add_argument('-g', '--get', metavar='FILE', nargs='+',
            help='receive file from server')
    group.add_argument('-l', '--list', metavar='PATH', nargs='?',
            help='list files from server')
    group.add_argument('-n', '--newkey', action='store_true',
            help='generate new user key')
    #These options can be used in combination with any other
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
    config.read(config_path, encoding='utf-8')

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
    #make a server "connection" (stateless, rpc)
    ip_server = misc.my_ip() #FIXME find a server
    server_addr = 'http://{}:5000'.format(ip_server)
    server = ServerProxy(server_addr)

    rsa = crypto.open_rsa_key(rsa_dir)
    user_id = 1 #FIXME get a real user id
    #verify if this file exist (same name in this directory)
    dir_key = "home" #FIXME set where is.... need more discussion
    #ask to server if is update or new file
    salt = server.get_salt(file_name, dir_key, user_id)

    #generate every keys in string return tuple (0 - verify, 1 - write, 2 - read, 3 - salt)
    keys = crypto.keys_string(salt, rsa)
    try:
        f = open(file_name, "rb") #verify if exist file
        crypto.encrypt_file(keys[2][0:32], file_name, None, 32)
        f = open(file_name+".enc", "rb")
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
        sys.exit("Some error occurred. Maybe you don't have permission to write. \nTry again.")

    host = (ip_server, port)
    misc.send_file(host, file_name)
    os.remove(file_name+'.enc')

def recive_file(file_name, rsa_dir):
    """
    recive file from server
    """

    ip = misc.my_ip()
    port, sock = misc.port_using(4001)
    #make a thread that will recive file in socket
    thr = Thread(target = misc.recive_file, args = (sock, file_name))

    ip_server = misc.my_ip() #FIXME find a server
    server_addr = 'http://{}:5000'.format(ip_server)
    server = ServerProxy(server_addr)

    user_id = 1
    dir_key = "home"
    salt = server.get_salt(file_name, dir_key, user_id)

    if (salt == 0):
        print("This file can't be found")
        return

    #TODO: achar o diretorio sozinho
    rsa = crypto.open_rsa_key(rsa_dir)
    keys = crypto.keys_string(salt, rsa)

    thr.start()
    #ask to server a file with name (keys[0] = hash)
    #client ip and your port to recive file
    print(server.give_file(ip, port, keys[0]))
    thr.join()

########################

def main():
    """The function called when the program is executed on a shell"""

    #set where is client home
    _home = os.getenv("HOME")
    #file where put configurations
    _config_dir = _home + '/.flexa'
    #where directory flexa was called
    dir_called = os.getcwd()
    #dir to save configs
    config_path = _config_dir+'/flexa.ini'
    #mapped dir
    flexa_dir = _home+"/directory-flexa"

    parser = usage()

    if not os.path.exists(flexa_dir):
        #if don't exist diretory-flexa in user home then is your first time
        #is necessary create RSA and default directory
        print("First time you use it.\nSome configuration is necessary.")

        if(misc.query_yes_no("Do you want creat flexa configurations?")):
            #make dirs to map and save configurations
            os.makedirs(flexa_dir)
            os.makedirs(_config_dir)
        else:
            print("Starting in Flexa was canceled")
            sys.exit(1)

        config = load_config(config_path)

        if (misc.query_yes_no("Do you want creat RSA key now?")):
            filename = generate_new_key(_config_dir)
            config.set('User', 'private key', filename)
            cryp = crypto.open_rsa_key(filename)
            hashe = hashlib.sha256()
            hashe.update(cryp.exportKey(format='DER'))
            config.set('User', 'hash client', hashe.hexdigest())
            print("Configurations done.\n How to use flexa:")
            parser.print_help()


            #Write configuration file
            with open(config_path, mode='w', encoding='utf-8') as outfile:
                print("gravando", config_path)
                config.write(outfile)

            sys.exit(0)
    else:
        if ((not dir_called in flexa_dir) or (os.getenv("HOME") == dir_called)):
            #flexa was invoked outside of mapped directory
            sys.exit("You are calling flexa outside your mapped directory.")

    #If no option is given, show help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)

    #Parse the user choices
    args = parser.parse_args()

    config = load_config(config_path)

    #Generate a new user key
    if args.newkey:
        #Checks if the user already has a key
        if os.path.exists(config.get('User', 'private key')):
            confirm = misc.query_yes_no("There is already a generated key, "
                    "generate another one?", default='no')
            if not confirm:
                sys.exit(2)

        filename = generate_new_key()
        config.set('User', 'private key', filename)
        cryp = crypto.open_rsa_key(filename)
        hashe = hashlib.sha256()
        hashe.update(cryp.exportKey(format='DER'))
        config.set('User', 'hash client', hashe.hexdigest())

    #Send a file to server
    if args.put:
        for names in args.put:
            send_file(names, config.get('User', 'private key'))

    #Get a file from server
    if args.get:
        for names in args.get:
            recive_file(names, config.get('User', 'private key'))

    #Write configuration file
    with open(config_path, mode='w', encoding='utf-8') as outfile:
        config.write(outfile)


if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
