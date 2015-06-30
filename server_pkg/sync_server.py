'''
Created on 23/11/2014

@author: mario
'''

from server_pkg.server import Server
from rpc import RPCThreadingServer
from rpc import RPCServerHandler
import logging

class Sync_Server(Server):
    
    """
    Class that start server_pkg to sync with others server_pkg client updates
    """

    #indicate how many machines will be observed -> 2 in right and 2 in left
    size_window = 4



    def __init__(self):
        
        #self.uid = self.configs.uid
        
        connection = (self.configs.ip, self.configs.port)

        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("sync_server")
        self.logger.info("Listening on {}:{}".format(ip, port))

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

        pass

    def update_neighbor(self):

        pass