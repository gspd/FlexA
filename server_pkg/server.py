'''
Created on 28/06/2015

@author: mario
'''

from server_pkg import config
import database

class Server(object):
    '''
    Initialize Synchronism Server and Client Server
    '''

    configs = None
    uid_hex = None
    uid_int = None
    ip = None

    logRequests = None

    db = None

    def __init__(self):
        '''
        Sets configurations
        '''
        self.configs = config.Config()
        self.uid_hex = self.configs.uid.hex
        self.uid_int = self.configs.uid.int
        self.ip = self.configs.ip
        self.logRequests = self.configs.logRequests_servers

        self.db = database.DataBase("/tmp/flexa.sqlite3")

