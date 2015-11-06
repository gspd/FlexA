#!/usr/bin/env python3
'''
Created on 19/10/2015

@author: mario
'''

from entity import user
from client import rpc_client
from binascii import a2b_qp

#some server to first connection
ip='192.168.2.110'


def register_new_user():
    name_user = input("Enter user name: ")

    rsa_pub = ""
    aux = input("Paste the client rsa.pub: ") + "\n"
    while( not aux == "-----END PUBLIC KEY-----"+ "\n"):
        rsa_pub = rsa_pub + aux
        aux = input() + "\n"
    rsa_pub = rsa_pub+"-----END PUBLIC KEY-----"

    user_obj = user.User(name=name_user, rsa_pub=a2b_qp(rsa_pub))
    user_obj.set_server_hash()
    user_obj.set_uid_user()
    user_obj.find_server_by_hash()
    
    server_obj = rpc_client.RPC()

    for server in user_obj.primary_servers:
        print("conectando em ", server)
        conn = server_obj.set_server(server[1])
        if( conn.register_user(name_user, user_obj.uid, rsa_pub) ):
            print("       ->Usuário adicionado com sucesso")
        else:
            print("       ->Algum problema aconteceu.    :(")



