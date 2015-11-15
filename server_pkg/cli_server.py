#!/usr/bin/env python3

'''
Created on 23/11/2014

@author: mario
'''

from rpc import RPCThreadingServer
from rpc import RPCServerHandler
from threading import Thread
from itertools import cycle
import misc
import database
import logging
from entity import file
from multiprocessing import Process  # @UnresolvedImport
from xmlrpc.client import ServerProxy

class Client_Server(Process):
    """Class that make rpc server_pkg

        your constructor make configs to start server_pkg

        functions:
            register_operations
                register all functions that client can call by rpc

    """

    def __init__(self, server_conf):

        super().__init__()

        self.server_info = server_conf

        #connect database
        self.db = server_conf.db

    def run(self):

        connection = (self.server_info.ip, self.server_info.configs.cli_port)
        server = RPCThreadingServer(connection, requestHandler=RPCServerHandler,
                                    logRequests=False)#self.server_info.logRequests)
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
        server.register_function(self.get_salt)
        server.register_function(self.update_file)
        server.register_function(self.negotiate_store_part)
        server.register_function(self.delete_file)
        server.register_function(self.get_map)
        server.register_function(self.get_state)
        server.register_function(self.still_alive)
        server.register_function(self.register_user)
        server.register_function(self.update_neighbor)
        server.register_function(self.get_current_version)

    def still_alive(self):
        return 1

    def get_map(self):
        addr = 'http://{}:{}'.format(self.server_info.ip, 30000)
        sync_server_conn = ServerProxy(addr)
        result = sync_server_conn.get_neighbors()
        return result

    def update_neighbor(self):
        addr = 'http://{}:{}'.format(self.server_info.ip, 30000)
        sync_server_conn = ServerProxy(addr)
        result = sync_server_conn.update_neighbor()
        return result

    def delete_file(self):
        pass

    def list_files(self, dirname, user_id):
        """
            Show every file in that directory
                verify_key - verify_key of current directory
        """

        self.logger.info("list_files invoked")

        files_db = self.db.get_all_files_by_dir(dirname, user_id)

        list_file = []
        for file_obj in files_db:
            #create a list of objects to transmit in xmlrpc
            list_file.append(file.File(file_db = file_obj, parse_to_str = True))

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

    def give_file(self, ip, port, verify_key, num_part, version):
        """ give file to client
            ip: string with ip, address of client
            file_name: in a future this is a hash of file
        """

        self.logger.info("give_file invoked")

        host = (ip, port)
        file_name_part = self.server_info.configs._dir_file + verify_key + '.v' + str(version) + '.' + str(num_part)
        misc.send_file(host, file_name_part)
        #FIXME every rpc call return something - put sent confirmation
        return 0

    def get_salt(self, file_name, user_id):
        """make a call in data base to find file
            if exist file return your salt
            else return 0
        """
        self.logger.info("get_salt invoked")
        return self.db.salt_file(file_name, user_id)
    
    def get_current_version(self, verify_key):
        # discovers which version should be created
        self.logger.info("get_current_version invoked")
        vk = verify_key
        return self.db.get_current_version(vk)

    def update_file(self, file_dict, part_number, server_receive_file, version):
        """
            if exist file, and client wanna send the same file (reference in db)
            the server_pkg update file in system
        """

        self.logger.info("update_file invoked")

        file_obj = file.File(dictinary=file_dict)
        up_file_obj = self.db.update_file(file_obj)
        if not up_file_obj:
            return False
        
        '''
         update date info calculated by the object,
         it'll be used to create the new version with
         its creation date equal to this file modification
         date
        '''
        file_dict['modify_date'] = up_file_obj.modify_date

        # compare the current stored file checksum with new file checksum
        stored_file_cs = self.db.get_file_checksum(file_dict['verify_key'])
        new_file_cs = file_dict['checksum']
        if new_file_cs == stored_file_cs:
            # file hasn't changed
            port = b"do not write"
        else:
            # it has changed.

            # calls method that does the actual storing.
            port = self.actual_file_storing(file_dict, part_number, server_receive_file, version)

        return port
        #TODO: set timout to thread

    def negotiate_store_part(self, file_dict, part_number, server_receive_file, version=1):
        """
            Negotiate with client to server_pkg receive file part
            
            server_receive_file -> is the list with all servers that receive this file
                                   [ [uid, ip], [uid, ip]] ... ]
        """

        self.logger.info("negotiate_store_part invoked")

        file_obj = file.File(dictinary=file_dict)

        #verify if user is okay
        if(not self.db.get_user_rsa_pub(file_obj.user_id)):
            #if return 0, this user ins't registered
            return 0

        new_file = database.File(file_obj=file_obj)
        self.db.add(new_file)
        # update date info calculated at the creation of object
        file_dict['create_date'] = new_file.create_date
        file_dict['modify_date'] = new_file.modify_date
        
        # first version to be created
        version = 1
        
        # calls method that does the actual storing
        port = self.actual_file_storing(file_dict, part_number, server_receive_file, version)

        return port
        #TODO: set timout to thread

    def actual_file_storing(self, file_dict, part_number, server_receive_file, version):
        '''
            This method is called by negotiate_store_part and update_file

            It's responsible for the actual storing of file and metadata management

            It'll update file parts metadata cycling throught the list of servers
            then it'll wait for the data retrieving
        '''

        #add in database where is the parts in system
        servers_iterable = cycle([item[1] for item in server_receive_file])
        for num_part in range(1, file_dict['num_parts']+1):
            # create new metadata entry only if it doesn't exist
            server = next(servers_iterable)
            if not self.db.get_if_part_exists(file_dict['verify_key'], server, num_part, version):
                #it's a new version, log to the system
                self.logger.info("Creating part {} version @ {}".format(num_part, server))
            
                part_obj = database.Part(verify_key=file_dict['verify_key'],
                                      create_date=file_dict['modify_date'],
                                      server_id=server,
                                      num_part=num_part,
                                      version=version)
                self.db.add(part_obj)
            else:
                self.logger.info("Metadata is already at the database @ {}".format(server))

        #get a unusage port and mount a socket
        port, sockt = misc.port_using(5001)

        # here is when it really stores the part
        self.logger.info("Storing part {} @ {}".format(part_number, next(servers_iterable)))
        file_name_to_get = self.server_info.configs._dir_file + file_dict['verify_key'] +\
                                '.v' + str(version) +\
                                '.' + str(part_number)
        thread = Thread(target = misc.receive_file, args = (sockt, file_name_to_get))
        thread.start()

        return port        

    def get_state(self):
        """
            Return status to client
                if lazy -> small number
                if buzy -> big number
        """
        return 1


###############################################################
#####          Implementação técnica temporária           #####
##### Resumindo não tive tempo de implementar isso melhor #####
###############################################################
#  As funções de admin_operations inseridas aqui não estão passando      #
# por autenticação. Portanto esses códigos não deveriam estar #
# aqui acessiveis para qualquer um.                           #
###############################################################

    def register_user(self, name, user_id, rsa_pub):

        self.logger.info("Register_user involked, user name: {}".format(name) )

        new_user = database.User(name, user_id, rsa_pub)

        print("O objeto user", new_user)


        return self.db.add(new_user)
