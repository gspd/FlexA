'''
Created on 16/12/2014

@author: mario
'''
from xmlrpc.client import ServerProxy
import misc
import sys
import client.config

class RPC(object):
    '''
    Set object that connect with server with xmlrpc
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
    def rpc_server(self):
        """
        Find a servers online and make connection
        """
    
        host = misc.Ping('255.255.255.255')
        host.TIMEOUT_TO_ANSWER = 0.3
        host.scan()
        while not host.online:
            host.TIMEOUT_TO_ANSWER += 0.3
            host.scan()
            if host.TIMEOUT_TO_ANSWER > 1.5:
                print("Can't found servers. \n Time out.")
                sys.exit(0)
    
        #online[0] is the first server that answer
        ip_server = host.online[0]
        server_addr = 'http://{}:{}'.format(ip_server, client.config.Config._PORT_SERVER)
        return ServerProxy(server_addr), ip_server