'''
Created on 15/12/2014

@author: mario
'''
#import class that set every configs
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
    
    #object that have every configs and parser
    configs = None
    
    rpc = rpc_client.RPC()
    
    def __init__(self):
        '''
        Constructor
        '''
        self.configs = Config()
        
        
        args = Config.args

        #Generate a new user key
        if args.newkey:
            #Checks if the user already has a key
            if os.path.exists(self.configs.get('User', 'private key')):
                confirm = misc.query_yes_no("There is already a generated key, "
                        "generate another one?", default='no')
                if not confirm:
                    sys.exit(2)
    
            #createNewUserKey(self.configs)
    
        #Send a file to server
        if args.put:
            for names in args.put:
                self.send_file(names)
    
        #Get a file from server
        if args.get:
            for names in args.get:
                self.recive_file(names)
    
        if args.list:
            self.list_files()
        #Write configuration file
        with open(self.configs._config_path, mode='w', encoding='utf-8') as outfile:
            self.configs.loaded_config.write(outfile)
        
        
        
        
        
    def send_file(self, file_name):
        """
        send file from client to server
        """
        
        #name with your relative position (directory) in flexa system     
        file_name_complete_relative = self.configs._dir_current_relative + file_name
    
        local_file = self.configs._dir_called + "/" + file_name
        file_name_enc = file_name+".enc"
        local_file_enc = self.configs._flexa_dir + file_name_enc
    
        server, ip_server = self.rpc.rpc_server()
        print(self.configs.loaded_config.get("User","private key"))
        rsa = crypto.open_rsa_key(self.configs.loaded_config.get("User","private key"),)
    
        user_id = self.configs.loaded_config.get("User","hash client")
        #verify if this file exist (same name in this directory)
        dir_key = "/" #FIXME set where is.... need more discussion
        #ask to server if is update or new file
        salt = server.get_salt(file_name_complete_relative, user_id)
    
        #generate every keys in string return tuple:
        #(0 - verify, 1 - write, 2 - read, 3 - salt)
        keys = crypto.keys_string(salt, rsa)
        try:
            print(local_file)
            f = open(local_file, "rb") #verify if exist file
            crypto.encrypt_file(keys[0][0:32], local_file, local_file_enc, 16)
            f = open(local_file_enc, "rb") #verify if create file crypted
            f.close()
        except FileNotFoundError:
            sys.exit("File not found.\nTry again.")
    
        type_file = "f"
    
        #if salt has a value then is update. because server return a valid salt
        if salt:
            port = server.update_file(keys[0], keys[1])
        else:
            #server return port where will wait a file
            port = server.get_file(file_name_complete_relative, keys, dir_key, user_id, type_file)
    
        if not port:
            sys.exit("Some error occurred. Maybe you don't have permission to \
                    write. \nTry again.")
    
        host = (ip_server, port)
        misc.send_file(host, local_file_enc)
        #remove temp crypt file
        os.remove(local_file_enc)



    def recive_file(self, file_name):
        """
        recive file from server
        """
    
        #name with your relative position (directory) in flexa system 
        dir_file_relative = self.configs._dir_current_relative + file_name
        dir_file_local = self.configs._dir_called + '/' + file_name
        file_name_enc = file_name + '.enc'
        dir_file_local_enc = self.configs._dir_called + '/' + file_name_enc
    
        ip = misc.my_ip()
        port, sock = misc.port_using(4001)
        #make a thread that will recive file in socket
        thr = Thread(target = misc.receive_file, args = (sock, dir_file_local_enc))
    
        server, ip_server = self.rpc.rpc_server()
        user_id = self.configs.loaded_config.get("User","hash client")
        salt = server.get_salt(dir_file_relative, user_id)
    
        if (salt == 0):
            print("This file can't be found")
            return
    
        rsa = crypto.open_rsa_key(self.configs.loaded_config.get('User', 'private key'))
        keys = crypto.keys_string(salt, rsa)
    
        thr.start()
        #ask to server a file with name (keys[0] = hash)
        #client ip and your port to recive file
        if ( server.give_file(ip, port, keys[0]) ):
            #exit with error and kill thread thr
            sys.exit("Some error occurs. Try again later.")
        thr.join()
    
        crypto.decrypt_file(keys[0][0:32], file_name_enc, dir_file_local ,16)
        #remove temp crypt file
        os.remove(dir_file_local_enc)

    def list_files(self):
        """
        Search every file from verify_key
            verify_key is directory where called this operation - answer is a dictionary of files and yours attributes 
        """
        server, ip = self.rpc.rpc_server()
    
        for dic_file in server.list_files(self.configs._dir_current_relative):
            print(dic_file['name'])
