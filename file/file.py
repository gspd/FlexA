'''
Created on 04/12/2014

@author: mario
'''

class File(object):
    '''
    classdocs
    '''

    name = None
    size = None
    create_date = None
    modify_date = None
    owner = None

    def __init__(self, name = None, size = None, create_date = None, modify_date = None, owner = None, file_db = None):
        '''
        Constructor
        '''
        if(file_db):
            #make file with database.file informations
            self.name = file_db.name
            self.size = file_db.size
            self.create_date = file_db.create_date
            self.modify_date = file_db.modify_date
            self.owner = file_db.owner  #FIXME: search in db name of owner
        elif(name):
            self.name = name
            self.size = size
            self.create_date = create_date
            self.modify_date = modify_date
            self.owner = owner
        else:
            pass

    def __repr__(self):
        return '<name: "{}", size: "{}", create_date: "{}", modify_date: "{}", owner: "{}"'.format(self.name, self.size, self.create_date, self.modify_date, self.user_id)
