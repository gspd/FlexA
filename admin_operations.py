#!/usr/bin/env python3
'''
Created on 28/10/2015

@author: mario
'''

from admin import register_user

if __name__ == '__main__':

    print("Operations:")
    print("1-Register new user")

    op = int(input("\nType the operation needed: "))
    
    if(op==1):
        register_user.register_new_user()