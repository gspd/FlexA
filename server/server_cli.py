#!/usr/bin/env python3

'''
Created on 23/11/2014

@author: mario
'''

from rpc import RPCThreadingServer
from rpc import RPCServerHandler
from threading import Thread
import misc
import database
import logging
from file import file

from server.config import configs


class Server(object):
    """Class that make rpc server
    
        your constructor make configs to start server
        
        functions:
            register_operations
                register all functions that client can call by rpc
            
    """


    def __init__(self):

        """
        """

        #connect database
        self.db = database.DataBase()

        connection = (configs.ip, configs.port)
        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("init_server")
        self.logger.info("Listening on {}:{}".format(ip, port))
        # register all functions
        self.register_operations(server)
        # create and init_server object
        try:
            scanner = misc.Ping("255.255.255.255")
            scanner.daemon()
            server.serve_forever()
        except KeyboardInterrupt as error:
            print("\nSignal of interrupt received.")
        except :
            print("\nSomething made init_server stop.")
        finally:
            server.shutdown()
            print("\nServer stopped!")

    def register_operations(self, server):
        """Register all operations supported by the init_server in the init_server
        objects
        """
        server.register_function(self.list_files)
        server.register_function(self.still_alive)
        server.register_function(self.give_file)
        server.register_function(self.get_file)
        server.register_function(self.get_salt)
        server.register_function(self.update_file)

    def list_files(self, verify_key):
        """
            Show every file in that directory
                verify_key - verify_key of current directory
        """

        files_db = self.db.list_files(verify_key)
        list_file = []
        for file_obj in files_db:
            list_file.append(file.File(file_db = file_obj ))

        return list_file

    def still_alive(self):
        return 1

    def give_file(self, ip, port, verify_key):
        """ give file to client
            ip: string with ip, address of client
            file_name: in a future this is a hash of file
        """
        host = (ip, port)
        misc.send_file(host, configs._dir_file + verify_key)
        #FIXME every rpc call return something - put sent confirmation
        return 0


    def get_file(self, file_name, keys, dir_key, user_id, type_file):
        """get file from client
           file_name: name of file that will save in init_server - verify_key
           keys: tupĺe (0 verify_key, 1 write_key, 2 read_key, 3 salt) strings
        """

        new_file = database.File(keys[0], keys[3], keys[1], keys[2], file_name, dir_key, user_id, type_file)
        self.db.add(new_file)

        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        print('name do arquivo: {}'.format(file_name), flush = True)
        thread = Thread(target = misc.receive_file, args = (sockt, configs._dir_file + keys[0]))
        thread.start()
        #TODO: set timout to thread

        return port

    def update_file(self, verify_key, write_key):
        """get file from client
           keys: tupĺe (0 verify_key, 1 read_key, 2 write_key, 3 salt) strings
        """
        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        if not (self.db.update_file(verify_key, write_key)):
            return False

        thread = Thread(target = misc.receive_file, args = (sockt, configs._dir_file + verify_key))
        thread.start()
        #TODO: set timout to thread

        return port

    def get_salt(self, file_name, user_id):
        """make a call in data base to find file
            if found return your salt
            else return 0
        """ 
        return self.db.salt_file(file_name, user_id)


###############################################################################
###############################################################################
##  NEW FUNCTIONS IMPLEMENTATION - WORKING HERE - WARNING - BIOLOGICAL RISK  ##
###############################################################################
###############################################################################

    def who_has_parts(verify_key):

        """ Query database and return a list of tuples with ordered pair:
        (server_ip,num_part) of requested file by verify_key """

        return self.db.get_servers_with_file_parts(verify_key)




        






