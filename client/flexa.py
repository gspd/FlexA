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
from client import rpc_client
from threading import Thread

class Client():
    '''
    classdocs
    '''
    
    # object that have every configs and parser
    configs = None
    
    #variables of control - Described in create_relatives_names_directory()
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
                self.create_relatives_names_directory(filename)
                self.send_file()

        # Get a file from server
        if args.get:
            for filename in args.get:
                self.create_relatives_names_directory(filename)
                self.receive_file()

        if args.list:
            self.list_files()

        if args.delete:
            for filename in args.delete:
                self.delete_file(filename)
        # Write configuration file
        with open(self.configs._config_path, mode='w', encoding='utf-8') as outfile:
            self.configs.loaded_config.write(outfile)

    def create_relatives_names_directory(self, filename):
        """ Function that make names relatives to file in FlexA system and
            our real directory in workstation

            Parameters:
                filename - name of file that will be process
        """
        # full filepath relative to FlexA file system
        self.relative_filepath = self.configs._dir_current_relative + filename

        # local full filepath
        self.local_filepath = self.configs._dir_called + filename

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

        # verify if exist file
        if not os.path.exists(self.local_filepath):
            sys.exit("File not found.\nTry again.")

        user_id = self.configs.loaded_config.get( "User", "hash client" )
        # verify if this file exist (same name in this directory)
        dir_key = "/"  # FIXME set where is.... need more discussion
        total_parts_file = 3

        server_obj = rpc_client.RPC()
        server_conn = server_obj.get_next_server()
        # ask to server if is update or new file
        salt = server_conn.get_salt( self.relative_filepath, user_id )

        # generate every keys in string return vector:
        # [0 - verify, 1 - write, 2 - read, 3 - salt]
        keys = crypto.keys_generator( self.configs.loaded_config.get("User", "private key"), salt ) 
        crypto.encrypt_file(keys[2][0:32], self.local_filepath, self.local_enc_filepath, 16)
        # verify if exist file
        if not ( misc.split_file(self.local_enc_filepath, total_parts_file) ):
            sys.exit("Problems while splitting file.\nTry again.")

        # if salt has a value then is update. because server return a valid salt
        if salt:
            for num_part in range( total_parts_file ):
                server_conn = server_obj.get_next_server( )
                port_server = server_conn.update_file( keys[0], keys[1], num_part )
                self.send_file_part( num_part, server_obj.ip_server, port_server )
        else:
            # server return port where will wait a file
            keys[2] = 0
            for num_part in range(total_parts_file):
                server_conn = server_obj.get_next_server( )
                port_server = server_conn.negotiate_store_part(user_id, self.relative_filepath, keys[0], dir_key, keys[1], keys[3], num_part)
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

        keys = crypto.keys_generator( self.configs.loaded_config.get("User", "private key"), salt )



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
            if ( server_conn.give_file( misc.my_ip(),port,keys[0],num_part) ):
                # exit with error and kill thread thr
                sys.exit("Some error occurs. Try again later.")
            thr.join()

        misc.join_file(name_parts_file, self.enc_filename)

        crypto.decrypt_file(keys[2][0:32], self.enc_filename, self.local_filepath, 16)

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