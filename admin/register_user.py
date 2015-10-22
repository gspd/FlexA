#!/usr/bin/env python3
'''
Created on 19/10/2015

@author: mario
'''
from hashlib import md5, sha256
from binascii import a2b_qp
from xmlrpc.client import ServerProxy
import sys


#some server to first connection
ip='192.168.2.22'


def register_user():
    name_user = input("Enter user name: ")

    rsa_pub = ""
    aux = input("Paste the client rsa.pub: ") + "\n"
    while( not aux == "-----END PUBLIC KEY-----"+ "\n"):
        rsa_pub = rsa_pub + aux
        aux = input() + "\n"
    rsa_pub = rsa_pub+"-----END PUBLIC KEY-----"

    hash_ = sha256()
    hash_.update(a2b_qp(rsa_pub))
    uid_user = hash_.hexdigest()

    server_hashs = set_server_hash(rsa_pub)
    primary_server = find_server_by_hash(server_hashs)

    for server in primary_server:
        print("conectando em ", server)
        conn = set_server(server[1])
        if( conn.register_user(name_user, uid_user, rsa_pub) ):
            print("       ->Usuário adicionado com sucesso")
        else:
            print("       ->Algum problema aconteceu.    :(")


def set_server_hash(rsa_pub):
    """
        Compute hash of primary servers and find what is your ip
    """

    rsa_pub = a2b_qp(rsa_pub)
    server_hash = []

    hash = md5()
    hash.update(rsa_pub)
    for i in range(3):
        hash_chunk = hash.copy()
        #convert int->str->bin
        hash_chunk.update(a2b_qp(str(i)))
        server_hash.append(hash_chunk.hexdigest())
    
    return server_hash

def find_server_by_hash(server_hash):
    """
        Scan network end set ip using hash as parameter
    """
    server_conn = set_server(ip)
    mapp = server_conn.get_map()
    
    primary_server = []

    for current_hash in server_hash:
        #search the primary server
        while(True):
            #if this hash is lowest -> your primary server is in right
            if( (int(current_hash, 16) > int( mapp[len(mapp)-1][0], 16 )) and ( mapp[len(mapp)-1][1]) ):
                server_conn = set_server(mapp[len(mapp)-1][1])
                mapp = server_conn.get_map()

            #if this hash is biggest -> your primary server is in left
            elif( int(current_hash, 16) < int( mapp[0][0], 16)):
                server_conn = set_server(mapp[0][1])
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
                primary_server.append(mapp[index])

                #stop first while -> stop search the correct mapp
                break
            
    return primary_server

def set_server(ip):
    server_addr = 'http://{}:{}'.format(ip, 5000)
    server_conn = ServerProxy(server_addr)
    try:
        server_conn.still_alive()
    except:
        server_conn = 0

    #return the object server_rpc
    return server_conn

if __name__ == '__main__':
    register_user()