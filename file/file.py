'''
Created on 04/12/2014

@author: mario
'''

class File(object):
    '''
    classdocs
    '''

    file_name = 0
    size = 0
    create_date = 0
    modify_date = 0
    owner = 0

    def __init__(self, name = 0, size = 0, create_date = 0, modify_date = 0, owner = 0, file_db = None):
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
            self.owner = file_db.user_id  #FIXME: search in db name of owner
        elif(name):
            self.name = name
            self.size = size
            self.create_date = create_date
            self.modify_date = modify_date
            self.owner = owner
        else:
            pass

    def __repr__(self):
        return '<name: "{}", size: "{}", create_date: "{}", modify_date: "{}", owner: "{}"'.format(self.file_name, self.size, self.create_date, self.modify_date, self.owner)
