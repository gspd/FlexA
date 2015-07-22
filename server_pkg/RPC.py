'''
Created on 20/07/2015

@author: mario
'''

from xmlrpc.client import ServerProxy
import misc
import sys
from server_pkg.config import Config

class RPC(object):
    '''
    Class responsible for scanning network, finding servers online
        and making connection to rpc server
    '''

    TIME_OUT_ANSWER = 0.3
    TIME_ADD_PER_HOPE = 0.3
    MASK_SCAN = '255.255.255.255'
    MIN_SERVER = 1
    MAX_TIME_OUT_ANSWER = 1.5

    list_online = []
    index_list_online = None
    ip_server = None
    
    config = Config()

    #if have few servers, ask if user want to continue
    few_servers_continue = False

    def __init__(self):
        '''
        Start object with first scan
        '''
        
        self.index_list_online = 0
        self.scan_ping = misc.Ping(self.MASK_SCAN)

        return

    def scan_online_servers(self):
        """
        Scan network searching online nodes and running FlexA

        modify self.list_online
        return None
        """

        #set object and its configurations
        
        self.scan_ping.TIMEOUT_TO_ANSWER = self.TIME_OUT_ANSWER

        #scan network until at least a minimun number of online servers are found
        #or to break the timeout -> any one server was find
        while len(self.scan_ping.online) < self.MIN_SERVER :
            self.scan_ping.scan()
            self.scan_ping.TIMEOUT_TO_ANSWER += self.TIME_ADD_PER_HOPE

            if self.scan_ping.TIMEOUT_TO_ANSWER > self.MAX_TIME_OUT_ANSWER :
                #if TIMEOUT stop the search
                break

        #get list of servers online
        self.list_online = self.scan_ping.online

        #set index to 0 - return to init of list
        self.index_list_online = 0

        return

    def get_next_server(self):
        """
        Get the next server online

        return rpc server object
        """

        #if index is out of list range, scan network again
        if self.index_list_online >= len(self.list_online):
            self.scan_online_servers()

        if len(self.list_online) == 0 :
            sys.exit("Couldn't find any server. Verify your connection.")


        #get the next server of the list of servers online
        self.ip_server = self.list_online[self.index_list_online]
        self.index_list_online += 1
        #make the structure to connect rpc_server
        server_addr = 'http://{}:{}'.format(self.ip_server, self.config.sync_port)

        #return the object server_rpc
        return ServerProxy(server_addr)
    
    def get_next_server_not_me(self):
        """
        Get the next server online

        return rpc server object
        """
        self.scan_ping.LOCAL=False

        #if index is out of list range, scan network again
        if self.index_list_online >= len(self.list_online):
            self.scan_online_servers()

        if len(self.list_online) == 0 :
            sys.exit("Couldn't find any server. Verify your connection.")


        #get the next server of the list of servers online
        self.ip_server = self.list_online[self.index_list_online]
        self.index_list_online += 1
        #make the structure to connect rpc_server
        server_addr = 'http://{}:{}'.format(self.ip_server, self.config.sync_port)

        #return the object server_rpc
        return ServerProxy(server_addr)

    def set_server(self, ip):
        server_addr = 'http://{}:{}'.format(ip, self.config.sync_port)
                #return the object server_rpc
        return ServerProxy(server_addr)