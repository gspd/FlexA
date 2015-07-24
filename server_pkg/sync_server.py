'''
Created on 23/11/2014

@author: mario
'''

from server_pkg.server import Server
from server_pkg import neighbor
from rpc import RPCThreadingServer
from rpc import RPCServerHandler
import multiprocessing
from server_pkg.RPC import RPC
import logging

class Sync_Server(multiprocessing.Process, Server):
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
                                    logRequests=Server.logRequests, allow_none=True)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("[Sync Server]")

        self.server_obj = RPC()

        self.neighbor = neighbor.Neighbor()
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
        self.neighbor.UPDATE.set()

