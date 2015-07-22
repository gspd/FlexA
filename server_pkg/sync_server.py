'''
Created on 23/11/2014

@author: mario
'''

from server_pkg.server import Server
from rpc import RPCThreadingServer
from rpc import RPCServerHandler
from multiprocessing import Process
from server_pkg.RPC import RPC
import logging
from time import sleep

class Sync_Server(Process, Server):
    """
    Class that start server_pkg to sync with others server_pkg client updates
    """

    def run(self):
        """
            Like __init__()
            set attibutes of class sync_server and start xmlrpc server
        """

        connection = (self.configs.ip, self.configs.sync_port)

        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("[Sync Server]")
        self.logger.info("Listening on {}:{}".format(ip, port))

        self.server_obj = RPC()

        self.neighbor = Neighbor()
        proc = Process(target=self.neighbor.initialize)
        proc.start()

        # register all functions
        self.register_operations(server)

        # create and init_server object
        try:
            server.serve_forever()
        except:
            print("\nSomething made init_server stop.")
            server.shutdown()

    def register_operations(self, server):
        server.register_function(self.get_neighbor_map)
        server.register_function(self.update_neighbor)

    def get_neighbor_map(self):
        return self.neighbor.get_neighbors()

    def update_neighbor(self):
        pass


class Neighbor():
    """
    Class dedicate to monitoring neighbors servers
    """

    #indicate how many machines will be observed -> 2 in right and 2 in left
    window_size = 4

    #array to save neighbors - [[uid,ip]]
    left_neighbor = []
    right_neighbor = []

    def __init__(self):
        self.logger = logging.getLogger("[Sync Server - Neighbor]")

        self.server_obj = RPC()
        self.server_obj.scan_ping.LOCAL = False

        for _ in range(self.window_size//2):
            self.left_neighbor.append([0,0])
            self.right_neighbor.append([0,0])

    def get_neighbors(self):
        #return a growing list of [uid, ips]
        return (self.left_neighbor[::-1]+[[Server.uid_hex,Server.ip]]+self.right_neighbor)

    def scan_neighbor(self):
        #first verification - verify list of saved servers - if list is empty try broadcast
        for i in range(self.window_size//2):
            if(self.left_neighbor[i][0] != 0):
                server_conn = self.server_obj.set_server(self.left_neighbor[i][1])
                break
            elif( self.right_neighbor[i][0] != 0):
                server_conn = self.server_obj.set_server(self.right_neighbor[i][1])
                break
        else:
            #will try broadcast
            server_conn = self.server_obj.get_next_server()
            map = server_conn.get_neighbor_map()
            self.organize_neighbors(map)

        while True:
            map = server_conn.get_neighbor_map()
            self.logger.debug(" Recived neighbor map: {}".format(map))

            if not(map[2][0]<Server.ip and map[3][0]>Server.ip):
                pass #reorganização

            sleep(10)

    def initialize(self):
        server_conn = self.server_obj.get_next_server()
        map = server_conn.get_neighbor_map()
        print(map)
        for server in map:
            if(server[0]==0):
                pass
            elif(int(server[0],16) < Server.uid_int):
                #then this server is in left
                self.put_in_left(server)
            else:
                self.put_in_right(server)
        print("o mapa atualizado é", self.get_neighbors())

    def put_in_left(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

            exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.left_neighbor[i][0]<int(server[0],16)):
                #start to change vector
                aux_current = self.left_neighbor[i]
                self.left_neighbor[i] = aux_next
                aux_next = aux_current

    def put_in_right(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

                exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.right_neighbor[i][0]>int(server[0],16)):
                #start to change vector
                aux_next, self.right_neighbor[i] = self.right_neighbor[i], aux_next
