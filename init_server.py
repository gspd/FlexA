#!/usr/bin/env python3

"""Implements the server class and all it's supported functions"""

from server.server_cli import Server




##########################################################################################

def main():
    """
    The function called when the program is executed on a shell
    """

    #FIXME interface da rede
    #broadcast = '192.168.1.255'
    #from server.config import configs
    #connection = (ip, configs._port_sync)
    #th = Thread(target = server.server_sync.Sync, args = (connection, broadcast), daemon = True)
    #th.start()

    #Start server_cli
    Server()


if __name__ == '__main__':
    main()
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
