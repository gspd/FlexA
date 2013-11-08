#!/usr/bin/env python3

"""Implements a client and a command line interface"""

import argparse
import sys
import os
import getpass
import configparser

try:
    import fuse
    _FUSE_AVAILABLE = True
except ImportError:
    _FUSE_AVAILABLE = False
    print('Package "fuse.py" not found, --mount option will not be '
            'available', file=sys.stderr)

import crypto
import misc

__authors__ = ["Thiago Kenji Okada"]
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
    if _FUSE_AVAILABLE:
        group.add_argument('-m', '--mount', metavar='PATH', nargs=1,
               help='mount remote filesystem')

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
    """

    config = configparser.SafeConfigParser()
    #This generate a list of default configs
    config.read_string(default_config)
    #If no file is found or is empty, this is ignored
    config.read(config_path, encoding='utf-8')

    return config

def generate_new_key(check_file = ''):
    """Generate a new RSA key and returns it's filename

    Input parameters:
    check_file -- name of the file to check if it already exists
    """

    if os.path.exists(check_file):
        confirm = misc.query_yes_no("There is already a generated key, "
                "generate another one?", default='no')
        if not confirm:
            sys.exit(2)

    #Ask the desired name and password to the file
    try:
        filename = input('Filename? ')
    except KeyboardInterrupt:
        sys.exit(2)
    if not filename:
        sys.exit('Needs a filename!')
    filename = os.path.abspath(filename)
    try:
        password = getpass.getpass('Password? ')
    except KeyboardInterrupt:
        sys.exit(2)
    #Generate the RSA key and store it's path on config file
    crypto.generate_rsa_key(filename, password)
    print('RSA key generated!')

    return filename

def main():
    """The function called when the program is executed on a shell"""

    #If no option is given, show help and exit
    parser = usage()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)
    #Parse the user choices
    args = parser.parse_args()

    #Name of the user config file
    config_path = 'flexa-ng.ini'
    config = load_config(config_path)

    #Generate a new user key
    if args.newkey:
        #Checks if the user already has a key
        filename = generate_new_key(config.get('User', 'private key'))
        config.set('User', 'private key', filename)

    #Write configuration file
    with open(config_path, mode='w', encoding='utf-8') as outfile:
        config.write(outfile)

if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
