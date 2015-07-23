'''
Created on 28/06/2015

@author: mario
'''

from server_pkg import config
import misc

class Server(object):
    '''
    Initialize Synchronism Server and Client Server
    '''

    configs = None
    uid_hex = None
    uid_int = None
    ip = None

    logRequests = None

    def __init__(self):
        '''
        Sets configurations
        '''

        Server.configs = config.Config()
        Server.uid_hex = Server.configs.uid.hex
        Server.uid_int = Server.configs.uid.int
        Server.ip = Server.configs.ip
        Server.logRequests = Server.configs.logRequests_servers

    def start_services(self):

            #DON'T TOUCH IN THIS LINE. DON'T MOVE TO THE BEGINNING
            #If put this line in the beginning circular imports will occurs
            from server_pkg import sync_server, cli_server

            #local network machines finder
            scanner = misc.Ping("255.255.255.255")
            scanner.daemon()

            sync = sync_server.Sync_Server()
            cli = cli_server.Client_Server()
            sync.start()
            #cli.start()

            try:
                sync.join()
                #cli.join()
            except:
                exit(0)
