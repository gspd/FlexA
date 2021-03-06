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
from entity import file
from client import rpc_client
from threading import Thread
from stat import S_ISREG
from hashlib import md5
from binascii import a2b_qp
from itertools import cycle

class ClientFile(object):
    filename = ''
    enc_filename = ''
    relative_filepath = ''
    absolute_filepath = ''
    absolute_enc_filepath = ''

class Client(object):
    '''
    classdocs
    '''
    
    # object that have every configs and parser
    configs = None

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

        args = self.configs.args

        self.user_id = self.configs.loaded_config.get("User", "hash client")

        #hash md5 -> 128 bits for each file chunk
        self.server_hash = []
        self.primary_server = []
        self.set_server_hash()
        self.find_server_by_hash()
        #self.organize_servers_by_state()

        # Send a file to server
        if args.put:
            for filename in args.put:
                file_info = ClientFile()
                # this can be either here or in the set_file_info function
                #file_info.filename = os.path.normpath(filename)
                if self.set_file_info_to_send(file_info, filename):
                    self.send_file(file_info)

        # Get a file from server
        if args.get:
            for filename in args.get:
                file_info = ClientFile()
                file_info.filename = os.path.normpath(filename)
                if self.set_file_info_to_receive(file_info):
                    self.receive_file(file_info)

        if args.list:
            if args.list == 1:
                self.list_files()
            else:
                self.list_files(more_info=True)

        if args.recursive_list:
            if args.recursive_list == 1:
                self.list_files(recursive=True)
            else:
                self.list_files(recursive=True, more_info=True)

        if args.delete:
            for filename in args.delete:
                self.delete_file(filename)
                
        # Write configuration file
        with open(self.configs._config_filepath, mode='w', encoding='utf-8') as outfile:
            self.configs.loaded_config.write(outfile)


    def set_file_info_to_receive(self, file_info):
        file_info.absolute_filepath = os.path.join(self.configs._current_local_dir, file_info.filename)
        file_info.absolute_filepath = os.path.normpath(file_info.absolute_filepath)
        file_info.relative_filepath = os.path.join(self.configs._current_relative_dir, file_info.filename)
        file_info.relative_filepath = os.path.normpath(file_info.relative_filepath)

        #verify if it's withing FlexA data directory
        if not self.configs._data_dir in file_info.absolute_filepath:
            print("Skipping '" + file_info.absolute_filepath + "'. "
                    "File can't be located outside mapped directory")
            return False

        file_info.enc_filename = file_info.filename + '.enc'
        file_info.absolute_enc_filepath = file_info.absolute_filepath + '.enc'
        return True

    def set_file_info_to_send(self, file_info, filename):
        """ If the given filename exists, is a regular file and is inside
            the mapped directory tracked by FlexA, this function:
             -Finds names relative to FlexA system and absolute pathnames
                for local file system

            Parameters:
                file_info - object to store some info about the path in
                    different environments (FlexA dir or local one)
                filename - name of file that will be process
        """
        # local full filepath
        file_info.absolute_filepath = os.path.abspath(filename)

        # verify if path exists
        if not os.path.exists(file_info.absolute_filepath):
            print("Skipping '" + file_info.absolute_filepath + "'. "
                  "File was not found.")
            return False
        # verify if it's a regular file
        elif not self.is_file(file_info.absolute_filepath):
            print("Skipping '" + file_info.absolute_filepath + "'. "
                  "It's not a path to a regular file.")
            return False
        #verify if it's withing FlexA data directory
        elif not self.configs._data_dir in file_info.absolute_filepath:
            print("Skipping '" + file_info.absolute_filepath + "'. "
                    "File can't be located outside mapped directory")
            return False

        # full filepath relative to FlexA file system
        file_info.relative_filepath = file_info.absolute_filepath.split(self.configs._current_local_dir)[1]

        file_info.filename = file_info.relative_filepath.split('/')[-1]

        # name of encrypted file
        file_info.enc_filename = file_info.filename + ".enc"

        # full local filepath for the encrypted file (temporary to send and receive)
        file_info.absolute_enc_filepath = file_info.absolute_filepath + ".enc"

        return True

    def send_file_part(self, num_part, ip_server, port_server, abs_enc_filepath):

        host = (ip_server, port_server)
        local_file_name_complete = abs_enc_filepath + '.' + str(num_part)
        # TODO: colocar um if no send_file para confirmar se o envio foi efetuado com sucesso
        misc.send_file(host, local_file_name_complete)
        os.remove(local_file_name_complete)

    def check_is_file(self, pathname):
        return S_ISREG(os.stat(pathname).st_mode)

    def is_file(self, pathname):
        return S_ISREG(os.stat(pathname).st_mode)

    def set_server_hash(self):
        """
            Compute hash of primary servers and find what is your ip
        """
        rsa_pub_dir = self.configs.loaded_config.get("User", "private key") + ".pub"
        rsa_pub = open(rsa_pub_dir, 'rb').read()

        hash = md5()
        hash.update(rsa_pub)
        for i in range(3):
            hash_chunk = hash.copy()
            #convert int->str->bin
            hash_chunk.update(a2b_qp(str(i)))
            self.server_hash.append(hash_chunk.hexdigest())

    def find_server_by_hash(self):
        """
            Scan network end set ip using hash as parameter
        """
        server_obj = rpc_client.RPC()
        server_conn = server_obj.get_next_server()

        mapp = server_conn.get_map()

        for current_hash in self.server_hash:
            #search the primary server
            while(True):
                #if this hash is lowest -> your primary server is in right
                if( (int(current_hash, 16) > int( mapp[len(mapp)-1][0], 16 )) and ( mapp[len(mapp)-1][1]) ):
                    server_conn = server_obj.set_server(mapp[len(mapp)-1][1])
                    mapp = server_conn.get_map()

                #if this hash is biggest -> your primary server is in left
                elif( int(current_hash, 16) < int( mapp[0][0], 16)):
                    server_conn = server_obj.set_server(mapp[0][1])
                    mapp = server_conn.get_map()

                #is in the middle of the mapp
                else:
                    index = 1
                    if(not mapp[0][1]):
                        #if first item is '0' (null)
                        index = index + 1
                        if(not mapp[1][1]):
                            #if second item is '0' (null)
                            index = index + 1

                    #find who is your primary server in this mapp
                    distance = int(current_hash, 16)-int(mapp[index-1][0], 16)
                    distance_aux = int(current_hash, 16)-int(mapp[index][0], 16)

                    #while that find the closer uid
                    while( abs(distance) > abs(distance_aux) ):
                        distance = distance_aux
                        index = index + 1
                        #verify if index is out of range
                        if(index == len(mapp)):
                            #primary server is in leftmost -> break
                            break
                        distance_aux = int(current_hash, 16)-int(mapp[index][0], 16)

                    index = index-1
                    self.primary_server.append(mapp[index])

                    #stop first while -> stop search the correct mapp
                    break

    def organize_servers_by_state(self):
        """
            Get the list map result of 'find_server_by_hash' and find the lazy server
            This function ask to the servers your state and organize in growing map based in your state
                first is the lazy server and last is busy server.
            This function is used to make load balacing.

            Use variable primary_server -> [ [uid,ip], [uid,ip] ... ]
        """

        server_obj = rpc_client.RPC()
        for server in self.primary_server:
            server_conn = server_obj.set_server(server[1])
            if(not server_conn):
                #set the high ocupation
                server.append(10)
                continue
            state = server_conn.get_state()
            server.append(state)
        self.primary_server = sorted(self.primary_server, key= lambda state:state[2])

########################################################
#########   OPERATIONS METHODS   #######################
########################################################

        
    def send_file(self, file_info):
        """
        send file from client to server
        """

        # verify if this file exist (same name in this directory)
        dir_key = "/"  # FIXME set where is.... need more discussion
        file_obj = file.File(name=file_info.relative_filepath, user_id=self.user_id, 
                             num_parts=3)

        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.primary_server])

        #Use variable primary_server -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))
        # ask to server if is update or new file

        salt = server_conn.get_salt( file_obj.name, file_obj.user_id)
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        crypto.encrypt_file(read_key, file_info.absolute_filepath, file_info.absolute_enc_filepath, 16)
        # verify if exist file

        if not ( misc.split_file(file_info.absolute_enc_filepath, file_obj.num_parts) ):
            sys.exit("Problems while splitting file.\nTry again.")

        # if salt has a value then is update. because server return a valid salt
        if salt:
            for num_part in range( file_obj.num_parts ):
                port_server = server_conn.update_file( file_obj, num_part )
                print("enviando o arquivo para ", self.rpc.ip_server, " parte ", num_part)
                if port_server == False:
                    sys.exit("Some error occurred. Maybe you don't have permission to \
                            write. \nTry again.")
                self.send_file_part( num_part, self.rpc.ip_server, port_server, file_info.absolute_enc_filepath )
                server_conn = self.rpc.set_server(next(server_cycle))
        else:
            # server return port where will wait a file
            for num_part in range(file_obj.num_parts):
                port_server = server_conn.negotiate_store_part(file_obj, dir_key, num_part)
                if not port_server:
                    sys.exit("Some error occurred. Maybe you don't have permission to write. \nTry again.")
                print("[sem salt] enviando o arquivo para ", self.rpc.ip_server, " parte ", num_part)
                self.send_file_part(num_part, self.rpc.ip_server, port_server, file_info.absolute_enc_filepath)
                server_conn = self.rpc.set_server(next(server_cycle))

        # remove temp crypt file
        os.remove(file_info.absolute_enc_filepath)


    def receive_file(self, file_info):
        """
        receive file from server
        """

        port, sock = misc.port_using(4001)

        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.primary_server])
        #Use variable primary_server -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))

        salt = server_conn.get_salt(file_info.relative_filepath, self.user_id)

        if (salt == 0):
            print("This file can't be found")
            return

        file_obj = file.File()
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        total_parts_file = 3  # FIXME: colocar para descobrir automaticamante numero de partes
        name_parts_file = []
        
        for num_part in range(total_parts_file):
            name_file = file_info.absolute_enc_filepath + '.' + str(num_part)
            name_parts_file.append(name_file)
            # make a thread that will receive file in socket
            thr = Thread(target=misc.receive_file, args=(sock, name_file))
            thr.start()
            # ask to server a file with name (keys[0] = hash)
            # client ip and your port to receive file
            if ( server_conn.give_file( misc.my_ip(),port, file_obj.verify_key, num_part) ):
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

    def list_files(self, recursive=False, more_info=False):
        """
        Search every file from verify_key
            verify_key is directory where called this operation - answer is a dictionary of files and yours attributes 
        """
        server_conn = self.rpc.get_next_server()

        # just to clean a bit this huge var name
        cur_dir = self.configs._current_relative_dir
        for dic_file in server_conn.list_files(cur_dir, self.user_id):
            if not recursive: # check if it's within directory
                if cur_dir != os.path.dirname(dic_file['name']):
                    continue
            else: # check if current dir is substring at the beginning
                if not os.path.dirname(dic_file['name']).startswith(cur_dir):
                    continue
            # TODO print more info if more_info == True
            print(dic_file['name'])

    def delete_file(self, name_file):
        """
            Delete files in flexa system

            Parameters:
                name_file - name of file
        """

        pass
