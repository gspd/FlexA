'''
Created on 24/07/2015

@author: mario
'''

from client.config import Config
from hashlib import md5
from binascii import a2b_qp
from client import rpc_client

class User(object):

    uid = None
    name = None
    rsa_pub = None
    primary_servers = []
    #hash md5 -> 128 bits for each file chunk
    server_hashes = []

    def __init__(self, uid=None, name=None, rsa_pub=None, primary_server=None, user_dict=None):

        if(user_dict):
            self.uid = user_dict["user_id"]
            self.name = user_dict["name"]
            self.rsa_pub = user_dict["rsa_pub"]
            self.primary_servers = user_dict["primary_servers"]
        elif(uid):
            self.user_id = uid
            self.name = name
            self.rsa_pub = rsa_pub
            self.primary_servers = primary_server

    def set_attr(self):
        configs = Config()
        self.uid = configs.loaded_config.get("User", "hash client")

        self.server_hash = []
        self.primary_servers = []
        self.set_server_hash(configs)
        self.find_server_by_hash()
        #self.organize_servers_by_state()




    def set_server_hash(self, configs):
        """
            Compute hash of primary servers and find what is your ip
        """
        rsa_pub_dir = configs.loaded_config.get("User", "private key") + ".pub"
        rsa_pub = open(rsa_pub_dir, 'rb').read()

        hash_ = md5()
        hash_.update(rsa_pub)
        for i in range(3):
            hash_chunk = hash_.copy()
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
                    self.primary_servers.append(mapp[index])

                    #stop first while -> stop search the correct mapp
                    break

    def organize_servers_by_state(self):
        """
            Get the list map result of 'find_server_by_hash' and find the lazy server
            This function ask to the servers your state and organize in growing map based in your state
                first is the lazy server and last is busy server.
            This function is used to make load balacing.

            Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        """

        server_obj = rpc_client.RPC()
        for server in self.primary_servers:
            server_conn = server_obj.set_server(server[1])
            if(not server_conn):
                #set the high ocupation
                server.append(10)
                continue
            state = server_conn.get_state()
            server.append(state)
        self.primary_servers = sorted(self.primary_servers, key= lambda state:state[2])
