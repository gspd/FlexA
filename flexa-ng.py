#!/usr/bin/env python3

import argparse
import sys

def usage():
    """Generate user help and parser user choices"""

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
    #This option can be used in combination with any other
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='increase output verbosity')

    return parser

if __name__ == '__main__':
    #If no option is given, show help and exit
    parser = usage()
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit

    #Parse the user choices
    args = parser.parse_args()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
