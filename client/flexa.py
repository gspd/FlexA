'''
Created on 15/12/2014

@author: mario
'''
# import class that set every configs
from client.config import Config
import client.path_parser as Path
import crypto
import misc
import os
import sys
from entity import file
from client import rpc_client
from threading import Thread
from itertools import cycle
from entity import user
import time
import logging

class ClientFile(object):
    filename = ''
    enc_filename = ''
    relative_filepath = ''
    absolute_filepath = ''
    absolute_enc_filepath = ''
    checksum = ''
    size=0

class Client(object):
    '''
    classdocs
    '''
    
    # object that have every configs and parser
    configs = None

    inicio = time.time()

    rpc = rpc_client.RPC()


########################################################
########  CONTROLLING METHODS  #########################
########################################################


    def __init__(self):
        '''
        Constructor
        '''
        self.configs = Config()

        args = self.configs.args

        self.user = user.User()
        self.user.set_attr()

        # Send a file to server
        if args.put:
            self.logger = logging.getLogger("[Flexa_cli - send_file]")
            for filename in args.put:
                file_info = ClientFile()
                # this can be either here or in the set_file_info function
                #file_info.filename = os.path.normpath(filename)
                if Path.set_file_info_to_send(file_info, filename, self.configs._data_dir):
                    if self.send_file(file_info):
                        print(filename, " was sent succesfully.")
                    else:
                        print(filename, " couldn't be sent.")
                    

        # Get a file from server
        if args.get:
            self.logger = logging.getLogger("[Flexa_cli - recv_file]")
            for filename in args.get:
                file_info = ClientFile()
                file_info.filename = os.path.normpath(filename)
                if Path.set_file_info_to_receive(file_info,
                                                 self.configs._current_local_dir,
                                                 self.configs._current_relative_dir,
                                                 self.configs._data_dir):
                    self.receive_file(file_info)

        if args.list:
            self.logger = logging.getLogger("[Flexa_cli - list_file]")
            self.list_files()
        
        if args.snapshots:
            self.logger = logging.getLogger("[Flexa_cli - history_file]")
            for filename in args.snapshots:
                self.list_file_snapshots(filename)

        if args.recover:
            self.logger = logging.getLogger("[Flexa_cli - recover_file]")
            '''
                args.recover[0] - filename
                args.recover[1] - version of file to be recovered
            '''
            file_info = ClientFile()
            file_info.filename = os.path.normpath(args.recover[0])
            if Path.set_file_info_to_receive(file_info,
                                             self.configs._current_local_dir,
                                             self.configs._current_relative_dir,
                                             self.configs._data_dir):
                self.receive_file(file_info, args.recover[1])

        if args.delete:
            for filename in args.delete:
                self.delete_file(filename)
                
        # Write configuration file
        with open(self.configs._config_filepath, mode='w', encoding='utf-8') as outfile:
            self.configs.loaded_config.write(outfile)

        fim = time.time()
        
        print(fim - self.inicio)

    def send_file_part(self, num_part, ip_server, port_server, abs_enc_filepath, version=1):

        host = (ip_server, port_server)
        local_file_name_complete = abs_enc_filepath + '.' + str(num_part)
        misc.send_file(host, local_file_name_complete)
        os.remove(local_file_name_complete)


########################################################
#########   OPERATIONS METHODS   #######################
########################################################

        
    def send_file(self, file_info):
        """
        send file from client to server
        """

        # verify if this file exist (same name in this directory)
        dir_key = "/"  # FIXME set where is.... need more discussion

        file_obj = file.File(name=file_info.relative_filepath,
                             size=file_info.size,
                             checksum=file_info.checksum,
                             user_id=self.user.uid,
                             num_parts=3)

        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.user.primary_servers])

        #Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))

        # ask to server if it's an update or a new file
        salt = server_conn.get_salt( file_obj.name, file_obj.user_id)
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        # encrypt file
        crypto.encrypt_file(read_key, file_info.absolute_filepath, file_info.absolute_enc_filepath, 16)
        # and split it
        if not ( misc.split_file(file_info.absolute_enc_filepath, file_obj.num_parts) ):
            sys.exit("Problems while splitting file.\nTry again.")

        # if salt has a value then is update. because server return a valid salt
        if salt:
            # next version to be created
            version = server_conn.get_current_version(file_obj.verify_key)+1
            for part_number in range(1, file_obj.num_parts+1):
                port_server = server_conn.update_file( file_obj, part_number, self.user.primary_servers, version )
                self.logger.info("Updating part {} metadata @ {}:{}".format(part_number, self.rpc.ip_server, port_server))
                if port_server == b"do not write":
                    # it means that the file hasn't changed
                    #  so it only updates the metadata, without transfering the file
                    self.logger.info("No data transfer due to no changes on the file content")
                    continue
                elif not port_server:
                    sys.exit("Some error occurred. Maybe you don't have permission to write. \nTry again.")
                self.send_file_part( part_number, self.rpc.ip_server, port_server, file_info.absolute_enc_filepath, version )
                server_conn = self.rpc.set_server(next(server_cycle))
        else:
            # server return port where will wait a file
            for part_number in range(1, file_obj.num_parts+1):
                port_server = server_conn.negotiate_store_part(file_obj, part_number, self.user.primary_servers)
                self.logger.info("Sending new file part {} @ {}:{}".format(part_number, self.rpc.ip_server, port_server))
                if not port_server:
                    sys.exit("Some error occurred. Maybe you don't have permission to write. \nTry again.")
                self.send_file_part(part_number, self.rpc.ip_server, port_server, file_info.absolute_enc_filepath)
                server_conn = self.rpc.set_server(next(server_cycle))

        # remove temp crypt file
        os.remove(file_info.absolute_enc_filepath)
        return True


    def receive_file(self, file_info, version=0):
        """
        receive file from server
        """

        port, sock = misc.port_using(4001)

        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.user.primary_servers])
        #Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))

        salt = server_conn.get_salt(file_info.relative_filepath, self.user.uid)

        if (salt == 0):
            print("This file can't be found")
            return

        file_obj = file.File()
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        if version == 0:
            # discover is which version the file is at the moment
            version = server_conn.get_current_version(file_obj.verify_key)

        total_parts_file = 3 # TODO discover how many parts
        name_parts_file = []
        for num_part in range(1, total_parts_file+1):
            name_file = file_info.absolute_enc_filepath + '.' + str(num_part)
            name_parts_file.append(name_file)

            # make a thread that will receive file in socket
            thr = Thread(target=misc.receive_file, args=(sock, name_file))
            thr.start()

            # ask to server a file with name (keys[0] = hash)
            # client ip and your port to receive file
            if ( server_conn.give_file( misc.my_ip(),port, file_obj.verify_key, num_part, version) ):
                # exit with error and kill thread thr
                sys.exit("An error occured. Try again later.")
            thr.join()
            server_conn = self.rpc.set_server(next(server_cycle))

        misc.join_file(name_parts_file, file_info.enc_filename)

        crypto.decrypt_file(read_key, file_info.enc_filename, file_info.absolute_filepath, 16)

        #remove temp files from  workstation -> parts
        for file_to_rm in name_parts_file:
            os.remove(file_to_rm)
        #remove temp files from  workstation -> complete
        os.remove(file_info.absolute_enc_filepath)


    def list_files(self):
        #server_conn = self.rpc.get_next_server()
        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.user.primary_servers])
        #Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))

        # just to clean a bit these huge var names
        cur_dir = self.configs._current_relative_dir
        file_dictionaries = server_conn.list_files(cur_dir, self.user.uid)
        
        Path.print_file_list(file_dictionaries, cur_dir)

    def list_file_snapshots(self, filename):
        #server_conn = self.rpc.get_next_server()
        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.user.primary_servers])
        #Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))

        # join current directory and filename
        relative_filepath = os.path.join(self.configs._current_relative_dir, filename)

        version_list = server_conn.get_snapshots_list(relative_filepath, self.user.uid)

        nv = len(version_list)
        if nv == 0:
            sys.exit("No snapshots of "+filename+" were found.")
        elif nv == 1:
            print("1 snapshot of "+filename+" was found")
        else:
            print(str(len(version_list)) + " snapshots of "+filename+" were found.")

        widths = [len("9999-99-99 99:99:99"), len("Snapshot number"), 10]
        print("Created on".ljust(widths[0]), end="  ")
        print("Snapshot number".ljust(widths[1]), end="  ")
        print("Size".ljust(widths[2]))
        print("  ".join(version[label].ljust(widths[label]) for version in version_list for label in range(nv)))

    def delete_file(self, name_file):
        """
            Delete files in flexa system

            Parameters:
                name_file - name of file
        """

        pass
