'''
Created on 23/11/2014

@author: mario
'''

from rpc import RPCThreadingServer
from rpc import RPCServerHandler
from xmlrpc.client import ServerProxy
import misc
import logging


class Sync(object):

    def __init__(self, connection, broadcast):
        #run a daemon to find hosts online
        hosts_online = misc.Ping(broadcast)
        hosts_online.daemon()
        

        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("sync_server")
        self.logger.info("Listening on {}:{}".format(ip, port))
        # register all functions
        server.register_function(self.still_alive)
        # create and init_server object
        try:
            server.serve_forever()
        except:
            print("Problems to up sync init_server.")
            server.shutdown()

    def register_operations(self):
        self.server.register_function(self.still_alive)
        self.server.register_function(self.send_update)
        self.server.register_function(self.update)

    def still_alive(self):
        #TODO: return situation of init_server, if is free or busy
        return 1

    def send_update(self):
        pass

    def update(self):
        pass

    def verify_service(self):
        ip_server = misc.my_ip() #FIXME find a init_server
        server_addr = 'http://{}:5000'.format(ip_server)
        server = ServerProxy(server_addr)
