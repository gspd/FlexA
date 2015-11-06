'''
Created on 23/11/2014

@author: mario
'''

from rpc import RPCThreadingServer
from rpc import RPCServerHandler
from multiprocessing import Process  # @UnresolvedImport
from server_pkg.RPC import RPC
import logging
from xmlrpc.client import ServerProxy
from entity import user
import database

class Sync_Server(Process):
    """
    Class that start server_pkg to sync with others server_pkg client updates
    """

    #this vars is responsable to save all primary users in memory, prevents search (query) unnecessary
    my_primary_users = []
    left_primary_user = []
    right_primary_user = []


    def __init__(self, server_conf):

        #execute constructor of Server (inheritance)
        super().__init__()
        self.server_conf = server_conf

    def run(self):
        """
            Like __init__()
            set attibutes of class sync_server and start xmlrpc server
        """

        connection = (self.server_conf.ip, self.server_conf.configs.sync_port)

        server = RPCThreadingServer(addr=connection, requestHandler=RPCServerHandler, allow_none=True, 
                                    logRequests=False)#self.server_info.logRequests)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("[Sync Server]")

        self.db = self.server_conf.db

        self.server_obj = RPC()

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
        server.register_function(self.get_primary_users)
        server.register_function(self.get_metadata_files_by_user)
        

    def still_alive(self):
        return 1

    def get_neighbor_map(self):
        addr = 'http://{}:{}'.format(self.server_conf.ip, 30000)
        server_conn = ServerProxy(addr)
        result = server_conn.get_neighbors()
        return result

    def update_neighbor(self):
        addr = 'http://{}:{}'.format(self.server_conf.ip, 30000)
        server_conn = ServerProxy(addr)
        server_conn.require_update()
        return 1


    #################################
    #### Synchronization - Begin ####
    #################################

    def get_primary_users(self):
        """
            Return my primary users
             ->actually every users that was added in database is primary user to this localhost 
               then return every users in database 
        """
        self.logger.info("[get_primary_users] invoked" )

        return [user.User(user_db=user_elem) for user_elem in self.db.get_all_users()]

    def get_metadata_files_by_user(self, user_id):

        files = self.db.get_all_files_by_user(user_id)

        parts = []
        for file_sing in files:
            parts.append( self.db.get_all_parts_file_by_vk(file_sing.verify_key) )

        return [files, parts]

    def scan_neighbor_primary_users(self):
        """
           Verify who is second users.
               Second users is the primary users of neighbor servers,
               if some neighbor server crash, this localhost will be the 
               first server to the crashed server primary users. 
        """

        server_conn = self.server_obj.set_server(self.left_neighbor[0][1])
        self.left_primary_user = server_conn.get_primary_users()

        server_conn = self.server_obj.set_server(self.right_neighbor[0][1])
        self.right_primary_user = server_conn.get_primary_users()

    def handling_error_left_neighbor(self):
        """
            Verify every user of crashed server (right or left) if this server
            is the primary server of it.
        """

        for user_xml in self.left_primary_user:

            user_obj = user.User(user_dict=user_xml)
            user_obj.set_server_hash()
            user_obj.find_server_by_hash()

            for list_ in user_obj.primary_servers:
                if self.server_conf.uid_hex in list_:
                    user_db = database.User(user_obj=user_obj)
                    self.db.add(user_db)

    def handling_error_right_neighbor(self):
        """
            Verify every user of crashed server (right or left) if this server
            is the primary server of it.
        """

        for user_xml in self.right_primary_user:

            user_obj = user.User(user_dict=user_xml)
            user_obj.set_server_hash()
            user_obj.find_server_by_hash()

            for list_ in user_obj.primary_servers:
                if self.server_conf.uid_hex in list_:
                    user_db = database.User(user_obj=user_obj)
                    self.db.add(user_db)

    def get_files_part_user(self):
        """
            Return every informations about user
            
        """ 
        pass



    #################################
    ##### Synchronization - End #####
    #################################
