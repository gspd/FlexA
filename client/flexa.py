'''
Created on 15/12/2014

@author: mario
'''
# import class that set every configs
from client.config import Config
import crypto
import sys
import misc
import os
from file import file
from client import rpc_client
from threading import Thread
from stat import S_ISREG

class Client():
    '''
    classdocs
    '''
    
    # object that have every configs and parser
    configs = None
    
    #variables of control - Described in set_relative_local_filepath()
    relative_filepath = None
    local_filepath = None
    enc_filename = None
    local_enc_filepath = None

    rpc = rpc_client.RPC()
    user_id = None


########################################################
########  CONTROLLING METHODS  #########################
########################################################


    def __init__(self):
        '''
        Constructor
        '''
        self.configs = Config()

        args = Config.args

        self.user_id = self.configs.loaded_config.get("User", "hash client")

        # Send a file to server
        if args.put:
            for filename in args.put:
                self.set_relative_local_filepath(filename)
                self.send_file()

        # Get a file from server
        if args.get:
            for filename in args.get:
                self.set_relative_local_filepath(filename)
                self.receive_file()

        if args.list:
            self.list_files()

        if args.delete:
            for filename in args.delete:
                self.delete_file(filename)
                
        # Write configuration file
        with open(self.configs._config_path, mode='w', encoding='utf-8') as outfile:
            self.configs.loaded_config.write(outfile)


    def set_relative_local_filepath(self, filename):
        """ Function that make names relative to file in FlexA system and
            our real directory in workstation

            Parameters:
                filename - name of file that will be process
        """
        # full filepath relative to FlexA file system
        self.relative_filepath = os.path.join(self.configs._dir_current_relative, filename)

        # local full filepath
        self.local_filepath = os.path.join(self.configs._dir_called, filename)

        # name of encrypted file
        self.enc_filename = filename + ".enc"

        # full local filepath for the encrypted file (temporary to send and receive)
        self.local_enc_filepath = self.configs._dir_called + self.enc_filename


    def send_file_part(self, num_part, ip_server, port_server):

        host = (ip_server, port_server)
        local_file_name_complete = self.local_enc_filepath + '.' + str(num_part)
        # TODO: colocar um if no send_file para confirmar se o envio foi efetuado com sucesso
        misc.send_file(host, local_file_name_complete)
        os.remove(local_file_name_complete)


########################################################
#########   OPERATIONS METHODS   #######################
########################################################

        
    def send_file(self):
        """
        send file from client to server
        """

        # verify if file exists
        if not os.path.exists(self.local_filepath):
            print("Skipping '" + self.local_filepath + "'."
                  "File was not found.")
            return
        # verify if it's a regular file
        elif not self.is_file(self.local_filepath):
            print("Skipping '" + self.local_filepath + "'."
                  "It's not a path to a regular file.")
            return

        # verify if this file exist (same name in this directory)
        dir_key = "/"  # FIXME set where is.... need more discussion
        file_obj = file.File(name=self.relative_filepath, user_id=self.user_id, 
                             num_parts=3)

        server_obj = rpc_client.RPC()
        server_conn = server_obj.get_next_server()
        # ask to server if is update or new file

        salt = server_conn.get_salt( file_obj.name, file_obj.user_id )
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        crypto.encrypt_file(read_key, self.local_filepath, self.local_enc_filepath, 16)
        # verify if exist file

        if not ( misc.split_file(self.local_enc_filepath, file_obj.num_parts) ):
            sys.exit("Problems while splitting file.\nTry again.")

        # if salt has a value then is update. because server return a valid salt
        if salt:
            for num_part in range( file_obj.num_parts ):
                server_conn = server_obj.get_next_server( )
                port_server = server_conn.update_file( file_obj, num_part )
                self.send_file_part( num_part, server_obj.ip_server, port_server )
        else:
            # server return port where will wait a file
            for num_part in range(file_obj.num_parts):
                server_conn = server_obj.get_next_server( )
                port_server = server_conn.negotiate_store_part(file_obj, dir_key, num_part)
                self.send_file_part(num_part, server_obj.ip_server, port_server)
                if not port_server:
                    sys.exit("Some error occurred. Maybe you don't have permission to \
                            write. \nTry again.")

        # remove temp crypt file
        os.remove(self.local_enc_filepath)


    def receive_file(self):
        """
        receive file from server
        """

        port, sock = misc.port_using(4001)


        server_obj = rpc_client.RPC()
        server_conn = server_obj.get_next_server()
        salt = server_conn.get_salt(self.relative_filepath, self.user_id)

        if (salt == 0):
            print("This file can't be found")
            return

        file_obj = file.File()
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        total_parts_file = 3  # FIXME: colocar para descobrir automaticamante numero de partes
        name_parts_file = []
        
        for num_part in range(total_parts_file):
            name_file = self.local_enc_filepath + '.' + str(num_part)
            name_parts_file.append(name_file)
            # make a thread that will receive file in socket
            thr = Thread(target=misc.receive_file, args=(sock, name_file))
            thr.start()
            # ask to server a file with name (keys[0] = hash)
            # client ip and your port to receive file
            if ( server_conn.give_file( misc.my_ip(),port, file_obj.verify_key, num_part) ):
                # exit with error and kill thread thr
                sys.exit("Some error occurs. Try again later.")
            thr.join()

        misc.join_file(name_parts_file, self.enc_filename)

        crypto.decrypt_file(read_key, self.enc_filename, self.local_filepath, 16)

        #remove temp files from  workstation -> parts
        for files_to_del in name_parts_file:
            os.remove(files_to_del)
        #remove temp files from  workstation -> complete
        os.remove(self.local_enc_filepath)

    def list_files(self):
        """
        Search every file from verify_key
            verify_key is directory where called this operation - answer is a dictionary of files and yours attributes 
        """
        server_conn = self.rpc.get_next_server()
    
        for dic_file in server_conn.list_files(self.configs._dir_current_relative):
            print(dic_file['name'])

    def delete_file(self, name_file):
        """
            Delete files in flexa system

            Parameters:
                name_file - name of file
        """

        pass