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
                 salt=0, checksum=0, file_db = None, dictinary = None, parse_to_str=False):
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
            self.verify_key = file_db.verify_key
            self.write_key = file_db.write_key
            self.checksum = file_db.checksum
        elif(dictinary):
            self.name = dictinary["name"]
            self.size = dictinary["size"]
            self.create_date = dictinary["create_date"]
            self.modify_date = dictinary["modify_date"]
            self.user_id = dictinary["user_id"]
            self.num_parts = dictinary["num_parts"]
            self.salt = dictinary["salt"]
            self.verify_key = dictinary["verify_key"]
            self.write_key = dictinary["write_key"]
            self.checksum = dictinary["checksum"]
        elif(name):
            self.name = name
            self.size = size
            self.create_date = create_date
            self.modify_date = modify_date
            self.user_id = user_id
            self.num_parts = num_parts
            self.checksum = checksum

        # Parses numeric and datetime types to string
        #     * used by list_files
        if(parse_to_str):
            self.size = str(self.size)
            self.num_parts = str(file_db.num_parts)

    def set_keys(self, rsa_private, salt):
        """
            Create keys and set in object
                if salt is zero, a new salt is generate

                ps: don't set read_key -> security key, but return your value to cipher file
        """
        # generate every keys in string return vector:
        # [0 - verify, 1 - read, 2 - write, 3 - salt] -> read_key is secret
        keys = crypto.keys_generator(rsa_private, salt)
        self.salt = keys[3]
        self.verify_key = keys[0]
        self.write_key = keys[2]

        return keys[1][0:32]

    def __repr__(self):
        return '<name: "{}", size: "{}", create_date: "{}", modify_date: "{}", owner: "{}">'.format(self.name, self.size, self.create_date, self.modify_date, self.user_id)
