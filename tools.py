#!/usr/bin/env python3

"""Provide general tools to FlexA."""

import os
import sys
import re
import string
import subprocess
import logging
from threading import Thread
from distutils.util import strtobool

# Create local logging object
logger = logging.getLogger(__name__)

__authors__ = ["Thiago Kenji Okada", "Leandro Moreira Barbosa"]

class Ping(Thread):
    """Class to send Ping messages to network nodes

    Public variables:
    received -- count of received packages
    minimum -- minimum RTT from Ping
    average -- average RTT from Ping
    maximum -- maximum RTT from Ping
    jitter -- RTT variation from Ping

    """

    received = None
    minimum = None
    average = None
    maximum = None
    jitter = None

    def __init__(self, host, count=4):
        """Ping constructor

        Input parameters:
        host -- hostname/IP address of the target node
        count -- number of ping messages; default is 4

        """
        Thread.__init__(self)
        self.__host = host
        self.__count = count

    def run(self):
        """Runs the ping thread, if there is no answer the thread is finished.

        """

        # Only Linux platform for now, using ping from iputils
        if sys.platform == 'linux' or sys.platform == 'linux2':
            lifeline = r'(\d) received'
            ping_regex = r'(\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)'

        ping = subprocess.Popen(
            ["ping", "-c", str(self.__count), self.__host],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        while True:
            try:
                out, err = ping.communicate()
            except ValueError:
                break
            # Get the number of received packages from ping
            matcher = re.compile(lifeline)
            self.received = re.findall(lifeline, str(out))
            # Get the rest of information
            matcher = re.compile(ping_regex)
            self.minimum, self.average, self.maximum, self.jitter = \
            matcher.search(str(out)).groups()

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    question -- is a string that is presented to the user.
    default -- is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no" or None (meaning an answer is
    required of the user).

    The "answer" return value is one of "yes" or "no".

    """
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    try:
        while True:
            print(question + prompt)
            choice = input().lower()
            try:
                if default is not None and choice == '':
                    return strtobool(default)
                elif choice:
                    return strtobool(choice)
            except ValueError:
                print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
    except KeyboardInterrupt:
        sys.exit(2)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
