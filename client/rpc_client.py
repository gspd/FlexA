'''
Created on 16/12/2014

@author: mario
'''
from xmlrpc.client import ServerProxy
import misc
import sys

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
    PORT_SERVER = 5000

    list_online = []
    index_list_online = None
    ip_server = None

    #if have few servers, ask if user want to continue
    few_servers_continue = False

    def __init__(self):
        '''
        Start object with first scan
        '''
        
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

        print("searching servers", end='')
        #scan network until at least a minimun number of online servers are found
        #or to break the timeout -> any one server was find
        while len(scan_ping.online) < self.MIN_SERVER :
            print(".", end='', flush=True)
            scan_ping.scan()
            scan_ping.TIMEOUT_TO_ANSWER += self.TIME_ADD_PER_HOPE

            if scan_ping.TIMEOUT_TO_ANSWER > self.MAX_TIME_OUT_ANSWER :
                #if TIMEOUT stop the search
                break
        print()
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

        if len(self.list_online) < self.MIN_SERVER:
            #ask if want to continue.
            #if yes, set few_servers_continue and dont show query again.
            #if no exit program
            if len(self.list_online) == 0 :
                sys.exit("Couldn't find any server. Verify your connection.")
            elif(self.few_servers_continue or misc.query_yes_no("Couldn't find many servers, would you like to continue?")):
                self.few_servers_continue = True
            else:
                sys.exit(0)

        #get the next server of the list of servers online
        self.ip_server = self.list_online[self.index_list_online]
        self.index_list_online += 1
        #make the structure to connect rpc_server
        server_addr = 'http://{}:{}'.format(self.ip_server, self.PORT_SERVER)

        #return the object server_rpc
        return ServerProxy(server_addr)

    def set_server(self, ip):
        server_addr = 'http://{}:{}'.format(ip, self.PORT_SERVER)
        #return the object server_rpc
        return ServerProxy(server_addr)