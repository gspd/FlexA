'''
Created on 24/07/2015

@author: mario
'''

import hashlib
from time import sleep
import binascii
from multiprocessing import Process, Event
from server_pkg.RPC import RPC
import logging

from rpc import RPCThreadingServer
from rpc import RPCServerHandler
from threading import Thread

class Neighbor(Process):
    """
    Class dedicate to monitoring neighbors servers
    """

    #indicate how many machines will be observed -> 2 in right and 2 in left
    window_size = 4

    #interval between scans to verify if server is online (seconds)
    TIME_AUTO_SCAN =15

    #array to save neighbors - [[uid,ip]]
    left_neighbor = []
    right_neighbor = []

    #array to save neighbors - [[uid,ip]] -> auxiliar
    left_neighbor_aux = []
    right_neighbor_aux = []

    TIMES_TO_UPDATE_MAP = 10
    UPDATE = Event()

    def __init__(self, server):

        super().__init__(daemon=True)

        self.logger = logging.getLogger("[Neighbor]")

        self.server_obj = RPC()
        self.server_obj.scan_ping.LOCAL = True

        self.left_neighbor = []
        self.right_neighbor = []
        for _ in range(self.window_size//2):
            self.left_neighbor.append(["0",0])
            self.right_neighbor.append(["0",0])

        self.zero_map_aux()

        self.server = server

    def run(self):
        """
            Resposable to start auto scan in network in new process
        """

        connection = (self.server.ip, 30000)
        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler,
                                    logRequests=self.server.logRequests)
        ip, port = server.server_address
        # Create local logging object
        self.logger.info("Listening on {}:{}".format(ip, port))

        thr_auto = Thread(target=self.auto_scan, daemon=True)
        thr_auto.start()

        self.register_operations(server)
        server.serve_forever()

    def register_operations(self, server):
        """Register all operations supported by the init_server in the init_server
        objects
        """
        server.register_function(self.get_neighbors)
        server.register_function(self.require_update)

    def require_update(self):
        self.logger.debug("require_update called" )
        self.UPDATE.set()

    def zero_map_aux(self):
        self.left_neighbor_aux = []
        self.right_neighbor_aux = []
        for _ in range(self.window_size//2):
            self.left_neighbor_aux.append(["0",0])
            self.right_neighbor_aux.append(["0",0])

    def replace_aux(self):
        self.left_neighbor = self.left_neighbor_aux
        self.right_neighbor = self.right_neighbor_aux

    def auto_scan(self):
        """
            Make scan in network to verify if servers is online
        """
        self.first_searcher()
        self.update_all()
        self.replace_aux()
        self.logger.debug(" Neighbors map:\n {}".format( str(self.get_neighbors()) ) )
        last_hash=b'0'
        count=self.TIMES_TO_UPDATE_MAP
        while True:
            self.verify_map()
            count-=1
            if(count<=0 or self.UPDATE.is_set()):
                self.UPDATE.clear()
                count=self.TIMES_TO_UPDATE_MAP
                self.first_searcher()
                hash_ = hashlib.md5()
                hash_.update( binascii.a2b_qp(str(self.get_neighbors())) )
                if(last_hash != hash_.digest()):
                    self.logger.debug("Update map all servers")
                    self.replace_aux()
                    self.update_all()
                    last_hash=hash_.digest()
                self.logger.debug(" Neighbors map:\n {}".format( str(self.get_neighbors()) ) )
            sleep(self.TIME_AUTO_SCAN)

    def update_all(self):
        for server in (self.left_neighbor+self.right_neighbor):
            if(server[1]!=0):
                server_conn = self.server_obj.set_server(ip=server[1])
                try:
                    server_conn.update_neighbor()
                except:
                    self.count=0

    def verify_map(self):
        """
            Make a verify if servers is online in current map, if some one is offline try to find next
        """

        for server in self.get_neighbors():
            server_conn = self.server_obj.set_server(ip=server[1])
            try:
                server_conn.still_alive()
            except:
                self.first_searcher()
                break

    def get_neighbors(self):
        self.logger.debug("get_neighbors called" )
        #return a growing list of [uid, ips]
        return (self.left_neighbor[::-1]+[[self.server.uid_hex,self.server.ip]]+self.right_neighbor)

    def first_searcher(self):
        """
            Search in system who is your neighbor
            Used when system start or is unstable
        """
        #searching servers with ping
        server_conn = self.server_obj.get_next_server()
        map_ = server_conn.get_neighbor_map()

        #using the first map go to the next server
        #stop when find a map whose id can be placed in the middle
        # only one of the following while(s) will be executed
        while( (int(map_[0][0],16)<self.server.uid_int) and (map_[0][0]!='0') ):
            server_conn = self.server_obj.set_server(map_[0][1])
            map_ = server_conn.get_neighbor_map()

        while( (int(map_[len(map_)-1][0],16)>self.server.uid_int) and
               (map_[len(map_)-1][0]!='0') ):
            server_conn = self.server_obj.set_server(map_[(len(map_)//2)-1][1])
            map_ = server_conn.get_neighbor_map()

        if('0' in dict(map_)):
            self.zero_map_aux()
            self.server_obj.scan_online_servers()
            #this is a signal that all machines just started or something went wrong -> verify all servers with ping
            for _ in range( len(self.server_obj.list_online) ):
                server_conn = self.server_obj.get_next_server()
                map_ = server_conn.get_neighbor_map()
                if(int(map_[len(map_)//2][0],16) < self.server.uid_int):
                    #then this server is in left
                    self.put_in_left(map_[len(map_)//2])
                elif(int(map_[len(map_)//2][0],16) > self.server.uid_int):
                    self.put_in_right(map_[len(map_)//2])
        else:
            #if find a map that your id can put in the middle
            for server in map_:
                if(int(server[0],16) < self.server.uid_int):
                    #then this server is in left
                    self.put_in_left(server)
                elif(int(map_[len(map_)//2][0],16) > self.server.uid_int):
                    self.put_in_right(server)


    def put_in_left(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

            exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.left_neighbor_aux[i] == server):
                break
            if(int(self.left_neighbor_aux[i][0],16)<int(server[0],16)):
                #start to change vector
                aux_next, self.left_neighbor_aux[i] = self.left_neighbor_aux[i], aux_next

    def put_in_right(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

                exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.right_neighbor_aux[i] == server):
                break
            if( (self.right_neighbor_aux[i][0]=='0') or (int(self.right_neighbor_aux[i][0],16)>int(server[0],16)) ):
                #start to change vector
                aux_next, self.right_neighbor_aux[i] = self.right_neighbor_aux[i], aux_next
