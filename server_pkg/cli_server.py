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

from server_pkg.server import Server
from multiprocessing import Process  # @UnresolvedImport


class Client_Server(Process, Server):
    """Class that make rpc server_pkg

        your constructor make configs to start server_pkg

        functions:
            register_operations
                register all functions that client can call by rpc

    """


    def run(self):
        #connect database
        self.db = database.DataBase()

        connection = (self.configs.ip, self.configs.cli_port)
        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler,
                                    logRequests=Server.logRequests)
        ip, port = server.server_address
        # Create local logging object
        self.logger = logging.getLogger("[Server Cli]")
        self.logger.info("Listening on {}:{}".format(ip, port))
        # register all functions
        self.register_operations(server)
        # create and init_server object
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nSignal of interrupt received.")
        except:
            print("\nSomething made init_server stop.")
        finally:
            server.shutdown()
            print("\nServer stopped!")

    def register_operations(self, server):
        """Register all operations supported by the init_server in the init_server
        objects
        """
        server.register_function(self.list_files)
        server.register_function(self.give_file)
        server.register_function(self.get_file)
        server.register_function(self.get_salt)
        server.register_function(self.update_file)
        server.register_function(self.negotiate_store_part)
        server.register_function(self.delete_file)

    def delete_file(self):
        pass

    def list_files(self, verify_key):
        """
            Show every file in that directory
                verify_key - verify_key of current directory
        """

        self.logger.info("list_files invoked")

        files_db = self.db.list_files(verify_key)

        list_file = []
        for file_obj in files_db:
            list_file.append(file.File(file_db = file_obj ))

        return list_file


    def get_server_status(self):
        """
            Analyze status of server_pkg with:
                - how many disc is free
                - how many connections is alive
                - how many memory is in using
            return a array of indices 
        """

        self.logger.info("get_server_status invoked")

        return [1]


    def give_file(self, ip, port, verify_key, num_part):
        """ give file to client
            ip: string with ip, address of client
            file_name: in a future this is a hash of file
        """

        self.logger.info("give_file invoked")

        host = (ip, port)
        file_name_part = self.configs._dir_file + verify_key + '.' + str(num_part)
        misc.send_file(host, file_name_part)
        #FIXME every rpc call return something - put sent confirmation
        return 0


    def get_file(self, file_name, keys, dir_key, user_id, type_file, num_part):
        """get file from client
           file_name: name of file that will save in init_server - verify_key
           keys: tupĺe (0 verify_key, 1 write_key, 2 read_key (None), 3 salt) strings
        """

        self.logger.info("get_file invoked")

        new_file = database.File(keys[0], keys[3], keys[1], file_name, dir_key, user_id, type_file, num_part)
        self.db.add(new_file)

        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        file_name_to_get = self.configs._dir_file + keys[0] + '.' + str(num_part)
        thread = Thread(target = misc.receive_file, args = (sockt, file_name_to_get))
        thread.start()
        #TODO: set timout to thread

        return port



    def update_file(self, file_dict, num_part):
        """
            if exist file, and client wanna send the same file (reference in db)
            the server_pkg update file in system
        """

        self.logger.info("update_file invoked")

        file_obj = file.File(dict=file_dict)

        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        if not (self.db.update_file(file_obj.verify_key, file_obj.write_key)):
            return False

        filename_to_save = self.configs._dir_file + file_obj.verify_key + '.' + str(num_part)
        thread = Thread(target = misc.receive_file, args = (sockt, filename_to_save ))
        thread.start()
        #TODO: set timout to thread

        return port



    def get_salt(self, file_name, user_id):
        """make a call in data base to find file
            if exist file return your salt
            else return 0
        """ 

        self.logger.info("get_salt invoked")

        return self.db.salt_file(file_name, user_id)


    def negotiate_store_part(self, file_dict, directory_key, part_number):
        """
            Negotiate with client to server_pkg receive file part
            (0 verify_key, 1 write_key, 2 read_key (None), 3 salt)
        """

        self.logger.info("negotiate_store_part invoked")

        file_obj = file.File(dict=file_dict)

        new_file = database.File(file_obj=file_obj)
        self.db.add(new_file)

        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        file_name_to_get = self.configs._dir_file + file_obj.verify_key + '.' + str(part_number)
        thread = Thread(target = misc.receive_file, args = (sockt, file_name_to_get))
        thread.start()

        return port
        #TODO: set timout to thread
