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
    
    rpc = rpc_client.RPC()
    
    def __init__(self):
        '''
        Constructor
        '''
        self.configs = Config()
        
        
        args = Config.args

        # Generate a new user key
        if args.newkey:
            # Checks if the user already has a key
            if os.path.exists(self.configs.get('User', 'private key')):
                confirm = misc.query_yes_no("There is already a generated key, "
                        "generate another one?", default='no')
                if not confirm:
                    sys.exit(2)
    
            # createNewUserKey(self.configs)
    
        # Send a file to server
        if args.put:
            for names in args.put:
                self.send_file(names)
    
        # Get a file from server
        if args.get:
            for names in args.get:
                self.recive_file(names)
    
        if args.list:
            self.list_files()
        # Write configuration file
        with open(self.configs._config_path, mode='w', encoding='utf-8') as outfile:
            self.configs.loaded_config.write(outfile)




        
    def send_file(self, file_name):
        """
        send file from client to server
        """

        # name with your relative position (directory) in flexa system     
        file_name_complete_relative = self.configs._dir_current_relative + file_name

        local_file = self.configs._dir_called + "/" + file_name
        file_name_enc = file_name + ".enc"
        local_file_enc = self.configs._flexa_dir + file_name_enc

        # verify if exist file
        if not os.path.exists(local_file):
            sys.exit("File not found.\nTry again.")

        rsa = crypto.open_rsa_key(self.configs.loaded_config.get("User", "private key"),)

        user_id = self.configs.loaded_config.get("User", "hash client")
        # verify if this file exist (same name in this directory)
        dir_key = "/"  # FIXME set where is.... need more discussion

        total_parts_file = 1

        server, ip_server = self.rpc.rpc_server()
        # ask to server if is update or new file
        salt = server.get_salt(file_name_complete_relative, user_id)

        # generate every keys in string return vector:
        # [0 - verify, 1 - write, 2 - read, 3 - salt]
        keys = crypto.keys_string(salt, rsa)

        crypto.encrypt_file(keys[2][0:32], local_file, local_file_enc, 16)

        # verify if exist file
        if not (misc.split_file(local_file_enc, total_parts_file)):
            sys.exit("Problems with split file occurred.\nTry again.")

        type_file = "f"

        list_ports = []
        # if salt has a value then is update. because server return a valid salt
        if salt:
            for num_part in range(total_parts_file):
                list_ports.append(server.update_file(keys[0], keys[1], num_part))
        else:
            # server return port where will wait a file
            keys[2] = 0
            for num_part in range(total_parts_file):
                port_on_server = server.negotiate_store_part(user_id, file_name_complete_relative, keys[0], dir_key, keys[1], keys[3], num_part)
                list_ports.append(port_on_server)
                if not port_on_server:
                    sys.exit("Some error occurred. Maybe you don't have permission to \
                            write. \nTry again.")

        for num_part in range(total_parts_file):
            host = (ip_server, list_ports[num_part - 1])
            file_name_to_get = local_file_enc + '.' + str(num_part)
            # TODO: colocar um if no send_file para confirmar se o envio foi efetuado com sucesso
            misc.send_file(host, file_name_to_get)
            os.remove(file_name_to_get)

        # remove temp crypt file
        os.remove(local_file_enc)


    def recive_file(self, file_name):
        """
        recive file from server
        """
    
        # name with your relative position (directory) in flexa system 
        dir_file_relative = self.configs._dir_current_relative + file_name
        dir_file_local = self.configs._dir_called + '/' + file_name
        file_name_enc = file_name + '.enc'
        dir_file_local_enc = self.configs._dir_called + '/' + file_name_enc
    
        ip = misc.my_ip()
        port, sock = misc.port_using(4001)
        # make a thread that will recive file in socket
        thr = Thread(target=misc.receive_file, args=(sock, dir_file_local_enc))
    
        server, ip_server = self.rpc.rpc_server()
        user_id = self.configs.loaded_config.get("User", "hash client")
        salt = server.get_salt(dir_file_relative, user_id)
    
        if (salt == 0):
            print("This file can't be found")
            return
    
        rsa = crypto.open_rsa_key(self.configs.loaded_config.get('User', 'private key'))
        keys = crypto.keys_string(salt, rsa)
    
        thr.start()
        
        num_part = 0  # FIXME: colocar para descobrir automaticamante numero de partes
        # ask to server a file with name (keys[0] = hash)
        # client ip and your port to recive file
        if (server.give_file(ip, port, keys[0], num_part)):
            # exit with error and kill thread thr
            sys.exit("Some error occurs. Try again later.")
        thr.join()
    
        crypto.decrypt_file(keys[2][0:32], file_name_enc, dir_file_local , 16)
        # remove temp crypt file
        os.remove(dir_file_local_enc)

    def list_files(self):
        """
        Search every file from verify_key
            verify_key is directory where called this operation - answer is a dictionary of files and yours attributes 
        """
        server, ip = self.rpc.rpc_server()
    
        for dic_file in server.list_files(self.configs._dir_current_relative):
            print(dic_file['name'])
