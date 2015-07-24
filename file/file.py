'''
Created on 04/12/2014

@author: mario
'''

import crypto

class File(object):
    '''
    classdocs
    '''

    name = 0
    size = 0
    create_date = 0
    modify_date = 0
    user_id = 0

    num_parts = None
    salt = None
    verify_key = None
    write_key = None

    def __init__(self, name=0, size=0, create_date=0, modify_date=0, user_id=0, num_parts=1,
                 salt=0, file_db = None, dict = None):
        '''
        Constructor
        You can make obj File put your attributes or put a fatabase.File obj.
        '''
        if(file_db):
            #make file with database.file informations
            self.name = file_db.file_name
            self.size = file_db.size
            self.create_date = file_db.create_date
            self.modify_date = file_db.modify_date
            self.user_id = file_db.user_id
            self.num_parts = file_db.num_parts
        elif(dict):
            self.name = dict["name"]
            self.size = dict["size"]
            self.create_date = dict["create_date"]
            self.modify_date = dict["modify_date"]
            self.user_id = dict["user_id"]
            self.num_parts = dict["num_parts"]
            self.salt = dict["salt"]
            self.verify_key = dict["verify_key"]
            self.write_key = dict["write_key"]
        elif(name):
            self.name = name
            self.size = size
            self.create_date = create_date
            self.modify_date = modify_date
            self.user_id = user_id
            self.num_parts = num_parts

    def set_keys(self, rsa_private, salt):
        """
            Create keys and set in object
                if salt is zero, a new salt is generate

                ps: don't set read_key -> security key, but return your value to cipher file
        """
        # generate every keys in string return vector:
        # [0 - verify, 1 - read, 2 - write, 3 - salt] -> read_key unsued
        keys = crypto.keys_generator(rsa_private, salt)
        self.salt = salt
        self.verify_key = keys[0]
        self.write_key = keys[2]

        return keys[1][0:32]

    def __repr__(self):
        return '<name: "{}", size: "{}", create_date: "{}", modify_date: "{}", owner: "{}">'.format(self.name, self.size, self.create_date, self.modify_date, self.user_id)
