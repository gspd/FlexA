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

        server = RPCThreadingServer(addr=connection, requestHandler=RPCServerHandler, 
                                    logRequests=Server.logRequests)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("[Sync Server]")

        self.server_obj = RPC()

        self.neighbor = Neighbor()
        self.neighbor.daemon()

        # register all functions
        self.register_operations(server)

        # create and init_server object
        try:
            self.logger.info("Listening on {}:{}".format(ip, port))
            server.serve_forever()
        except:
            server.shutdown()

    def register_operations(self, server):
        server.register_function(self.get_neighbor_map)
        server.register_function(self.update_neighbor)
        server.register_function(self.still_alive)

    def still_alive(self):
        return 1

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

    #interval between scans to verify if server is online (seconds)
    TIME_AUTO_SCAN =10

    #array to save neighbors - [[uid,ip]]
    left_neighbor = []
    right_neighbor = []

    def __init__(self):
        self.logger = logging.getLogger("[Sync Server - Neighbor]")

        self.server_obj = RPC()
        self.server_obj.scan_ping.LOCAL = True

        for _ in range(self.window_size//2):
            self.left_neighbor.append(["0",0])
            self.right_neighbor.append(["0",0])

    def daemon(self):
        """
            Resposable to start auto scan in network in new process
        """

        proc = Process(target=self.auto_scan, daemon=True)
        proc.start()

    def auto_scan(self):
        """
            Make scan in network to verify if servers is online
        """
        self.first_searcher()
        while True:
            self.verify_map()
            sleep(self.TIME_AUTO_SCAN)

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
        #return a growing list of [uid, ips]
        return (self.left_neighbor[::-1]+[[Server.uid_hex,Server.ip]]+self.right_neighbor)

    def first_searcher(self):
        """
            Search in system who is your neighbor
            Used when system start or is unstable
        """

        #searching servers with ping
        server_conn = self.server_obj.get_next_server()
        map = server_conn.get_neighbor_map()

        #using the first map go to the next server
        #stop when find a map whose id can be placed in the middle
        # only one of the following while(s) will be executed
        while( (int(map[0][0],16)<Server.uid_int) and (map[0][0]!='0') ):
            server_conn = self.server_obj.set_server(map[0][1])
            map = server_conn.get_neighbor_map()

        while( (int(map[len(map)-1][0],16)>Server.uid_int) and
               (map[len(map)-1][0]!='0') ):
            server_conn = self.server_obj.set_server(map[(len(map)//2)-1][1])
            map = server_conn.get_neighbor_map()

        if('0' in dict(map)):
            #this is a signal that all machines just started or something went wrong -> verify all servers with ping
            for _ in range( len(self.server_obj.list_online) ):
                server_conn = self.server_obj.get_next_server()
                map = server_conn.get_neighbor_map()
                if(int(map[len(map)//2][0],16) < Server.uid_int):
                    #then this server is in left
                    self.put_in_left(map[len(map)//2])
                elif(int(map[len(map)//2][0],16) > Server.uid_int):
                    self.put_in_right(map[len(map)//2])
        else:
            #if find a map that your id can put in the middle
            for server in map:
                if(int(server[0],16) < Server.uid_int):
                    #then this server is in left
                    self.put_in_left(server)
                elif(int(map[len(map)//2][0],16) > Server.uid_int):
                    self.put_in_right(server)

        self.logger.debug(" Neighbors map:\n {}".format( str(self.get_neighbors()) ) )

    def put_in_left(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

            exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.left_neighbor[i] == server):
                break
            if(int(self.left_neighbor[i][0],16)<int(server[0],16)):
                #start to change vector
                aux_next, self.left_neighbor[i] = self.left_neighbor[i], aux_next

    def put_in_right(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

                exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.right_neighbor[i] == server):
                break
            if( (self.right_neighbor[i][0]=='0') or (int(self.right_neighbor[i][0],16)>int(server[0],16)) ):
                #start to change vector
                aux_next, self.right_neighbor[i] = self.right_neighbor[i], aux_next
