#!/usr/bin/env python3

"""Call servers to start services
Servers is implemented in package server
"""

from server_pkg import server

if __name__ == '__main__':

    local_server = server.Server()

    local_server.start_services()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
