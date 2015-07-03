'''
Created on 28/06/2015

@author: mario
'''

from server_pkg import config

class Server(object):
    '''
    Initialize Synchronism Server and Client Server
    '''

    configs = None

    def __init__(self):
        '''
        Sets configurations
        '''

        Server.configs = config.Config()

    def start_services(self):

            #DON'T TOUCH IN THIS LINE. DON'T MOVE TO THE BEGINNING
            #If put this line in the beginning circular imports will occurs
            from server_pkg import sync_server, cli_server

            sync = sync_server.Sync_Server()
            cli = cli_server.Client_Server()
            sync.start()
            cli.start()

            try:
                sync.join()
                cli.join()
            except:
                exit(0)
