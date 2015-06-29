'''
Created on 28/06/2015

@author: mario
'''

from server_pkg import cli_server
from server_pkg import sync_server
from server_pkg.config import configs

class Server():   
    '''
    Initialize Synchronism Server and Client Server
    '''

    _uid = None
    
    def __init__(self):
        '''
        Constructor
        '''
        
        self._uid = configs.uid
        
        
        sync_server.Sync_Server()
        cli_server.Client_Server()