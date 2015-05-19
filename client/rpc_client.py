'''
Created on 16/12/2014

@author: mario
'''
from xmlrpc.client import ServerProxy
import misc
import sys
from client.config import Config

class RPC(object):
    '''
    Class responsible for scanning network, finding servers online
        and making connection to rpc server
    '''

    TIME_OUT_ANSWER = 0.3
    TIME_ADD_PER_HOPE = 0.3
    MASK_SCAN = '255.255.255.255'
    MIN_SERVER = 3
    MAX_TIME_OUT_ANSWER = 1.5

    list_online = None
    index_list_online = None
    ip_server = None

    def __init__(self):
        '''
        Start object with first scan
        '''
        
        self.scan_online_servers()
        self.index_list_online = 0

        return

    def scan_online_servers(self):
        """
        Scan network searching online nodes and running FlexA

        modify self.list_online
        return None
        """

        #set object and its configurations
        scan_ping = misc.Ping(self.MASK_SCAN)
        scan_ping.TIMEOUT_TO_ANSWER = self.TIME_OUT_ANSWER

        #scan network until at least a minimun number of online servers are found
        #or to break the timeout -> any one server was find
        while len(scan_ping.online) < self.MIN_SERVER :
            scan_ping.scan()
            scan_ping.TIMEOUT_TO_ANSWER += self.TIME_ADD_PER_HOPE

            if scan_ping.TIMEOUT_TO_ANSWER > self.MAX_TIME_OUT_ANSWER :
                print("Couldn't find servers.\n Timed out.")
                sys.exit(0)

        #get list of servers online
        self.list_online = scan_ping.online

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

        #get the next server of the list of servers online
        self.ip_server = self.list_online[self.index_list_online]
        self.index_list_online += 1
        #make the structure to connect rpc_server
        server_addr = 'http://{}:{}'.format(self.ip_server, Config._PORT_SERVER)

        #return the object server_rpc
        return ServerProxy(server_addr)


    def rpc_server(self):
        """
        Find a servers online and make connection

        FIXME: this method will be deleted. It will be replaced by scan_online_servers and get_next_server
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
        server_addr = 'http://{}:{}'.format(ip_server, Config._PORT_SERVER)
        return ServerProxy(server_addr), ip_server
