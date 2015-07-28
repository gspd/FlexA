#!/usr/bin/env python3

"""Call servers to start services
Servers is implemented in package server
"""

from server_pkg import sync_server, cli_server, neighbor, server
import misc

if __name__ == '__main__':
    
    server = server.Server()

    #local network machines finder
    scanner = misc.Ping("255.255.255.255") 
    neighbor = neighbor.Neighbor(server)
    sync = sync_server.Sync_Server(server=server, neighbor=neighbor)
    cli = cli_server.Client_Server(server=server, neighbor=neighbor)

    scanner.start() #daemon
    sync.start() #daemon
    neighbor.start()
    cli.start()

    try:
        sync.join()
        cli.join()
    except:
        exit(0)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
