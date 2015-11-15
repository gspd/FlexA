#!/usr/bin/env python3

import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, exists, func, Column, Integer, String, ForeignKey, Sequence, DateTime
from threading import Lock, Thread
import time
import datetime

import logging

Base = declarative_base()

class User(Base):
    __tablename__= 'user'
    
    uid = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=False)
    rsa_pub = Column(String(100))

    def __init__(self, name=None, uid=None, rsa_pub=None, user_obj=None):
        if(name):
            self.uid = uid
            self.name = name
            self.rsa_pub = rsa_pub
        elif(user_obj):
            self.uid = user_obj.uid
            self.name = user_obj.name
            self.rsa_pub = user_obj.rsa_pub

    def __repr__(self):
        return '<User({},{})>'.format(self.uid, self.name)

class File(Base):
    __tablename__ = 'file'

    verify_key = Column(String, primary_key=True)
    salt = Column(String, nullable=False)
    write_key = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    num_parts = Column(Integer,nullable=False)
    user_id = Column(String, ForeignKey('user.uid'), nullable=False)

    size = Column(Integer)
    create_date = Column(DateTime)
    modify_date = Column(DateTime)

    def __init__(self, verify_key=0, salt=0, write_key=0, file_name=0, dir_key=0, user_id=0,
                    num_parts=0, size=0, file_obj = None):
        if(file_obj):
            self.verify_key = file_obj.verify_key
            self.salt = file_obj.salt
            self.write_key = file_obj.write_key
            self.file_name = file_obj.name
            self.user_id = file_obj.user_id
            self.num_parts = file_obj.num_parts
            self.create_date = datetime.datetime.now()
            self.modify_date = datetime.datetime.now()
            self.size = file_obj.size
        else:
            self.verify_key = verify_key
            self.salt = salt
            self.write_key = write_key
            self.file_name = file_name
            self.user_id = user_id
            self.num_parts = num_parts
            self.create_date = datetime.datetime.now()
            self.modify_date = datetime.datetime.now()
            self.size = size

    def __repr__(self):
        return '<File(vfk "{}", salt "{}", wtk "{}", name "{}", user "{}",\
            num_parts "{}")>'.format(self.verify_key, self.salt, self.write_key, self.file_name,
            self.user_id, self.num_parts)


class Parts(Base):
    __tablename__ = 'parts'

    uid = Column(Integer, Sequence('parts_id_seq'), primary_key=True)
    verify_key = Column(String(100), ForeignKey('file.verify_key'), nullable=False)
    server_id = Column(String(40), ForeignKey('server.uid'))
    num_part = Column(Integer, nullable=False)

    def __init__(self, verify_key, server_id, num_part):
        self.verify_key = verify_key
        self.server_id = server_id
        self.num_part = num_part

    def __repr__(self):
        return '<Part({})>'.format(self.num_part, self.server_id)

class Server(Base):
    __tablename__ = 'server'

    uid = Column(String(40), nullable=False, primary_key=True)
    ip = Column(String(15), nullable=False)
    last_seen = Column(DateTime)

    def __init__(self, uid, ip, last_seen):
        self.uid = uid
        self.ip = ip
        self.last_seen = last_seen

    def __repr__(self):
        return '<Server({} {} {})>'.format(self.id, self.ip, self.last_seen)

class DataBase():
    """
        Class responsible for make every change and query in data base
        
            This class is respossible to control access in database, then to control the 
           concurrency this class has one session shared by every process. 
    """

    #variable to control max changes in data base before commit
    _max_modifies = 30
    #set interval to make commit by time in seconds
    _time_to_commit = 25
    #set echo in class database, if == True -> show every change in db; if == False -> don't show any thing
    #to set True, execute init_server.py with -vv (two verbose)
    _echo_db = False

    def __init__(self, file_db='flexa.sqlite3'):

        # Create local logging object
        self.logger = logging.getLogger("[DataBase]")

        self.flushed_added_obj_list = []
        self.flushed_updated_obj_list = []

        #model to connect database 'driver://user:pass@host/database'
        engine = create_engine('sqlite:///{}'.format(file_db), connect_args={'check_same_thread':False}, echo= self._echo_db)
        if not os.path.exists(file_db):
            self.logger.info("Make database {}".format(file_db))
            Base.metadata.create_all(engine)
        self.logger.info("Connecting database")
        Session = sessionmaker(bind=engine)
        self.session = Session()

        #Semaphores to control concurrence in data base
        #save_db is used to commit, put in hd every changes - slow
        self.save_db = Lock()
        #modify_db is used to add, modify, flush in :memory: database - fast
        self.modify_db = Lock()
        #modifies start in 0 -> auto commit if have modifies
        self.num_modifies = 0

        thr_daemon = Thread(target = self.daemon_commit, daemon = True)
        thr_daemon.start()

    def commit_db(self):
        """This function make commit in data base.
           It can't call in anywhere, this function is controlled by Semaphores (save_db, modify_db, num_modifies) 
        """
        self.logger.info("Storing last changes into database")
        self.save_db.acquire()
        self.session.commit()
        self.num_modifies = 0
        self.flushed_added_obj_list = []
        self.flushed_updated_obj_list = []
        self.save_db.release()

    def handling_rollback(self, error="unidentified"):
        """
            Rollback the database and commit all before changes
            *it's implements to be called protect by modify_db*
        """

        self.logger.debug("Error on commit:{}".format(error))
        self.session.rollback()

        #verify if list is not empty
        if(not self.flushed_added_obj_list == []):
            self.session.add_all(self.flushed_added_obj_list)
            self.flushed_added_obj_list = []

        for update_vk in self.flushed_updated_obj_list:
            file = self.session.query(File).filter(File.verify_key == update_vk)
            file.update({"modify_date":datetime.datetime.now()})

        self.flushed_updated_obj_list = []

        self.commit_db()

    def daemon_commit(self):
        while True:
            time.sleep(self._time_to_commit)
            if(self.modify_db):
                self.commit_db()

    def add(self, new_obj):
        """Put a new object in database
        Use Semaphores to control concurrence
        When there are more then  modifies execute commit_db()
        """

        self.logger.info("add invoked")

        #block semaphore
        self.modify_db.acquire()

        #try add new object in database, if don't have success rollback
        try:
            self.session.add(new_obj)
            self.session.flush()
            #if don't have problem add on list
            self.flushed_added_obj_list.append(new_obj)

            #verify if have more then 10 modifies
            if self.num_modifies < self._max_modifies:
                self.num_modifies+= 1
            else:
                self.commit_db()
        except Exception as error:
            self.logger.debug("->erro in add func: try to rollback and add again")
            self.handling_rollback(error)
            self.modify_db.release()
            return 0
            
        #unblock semaphore
        self.modify_db.release()

        return 1

    def update_file(self, file_obj):

        self.logger.info("update_file invoked")

        #block semaphore
        self.modify_db.acquire()

        file = self.session.query(File).filter(File.verify_key == file_obj.verify_key)

        try:
            if (file.one().write_key != file_obj.write_key):
                #don't have permition to write
                return False
        except:
            #can't find file.one() return except
            return False

        #have permission to write
        try:
            file.update({"modify_date":datetime.datetime.now(),
                         "size":file_obj.size})
            self.flushed_updated_obj_list.append(file_obj.verify_key)
            #verify if have more then 10 modifies
            if self.num_modifies < self._max_modifies:
                self.num_modifies+= 1
                self.session.flush()
            else:
                self.commit_db()
        except Exception as error:
            self.handling_rollback(error)
            self.modify_db.release()
            return 0

        #unblock semaphore
        self.modify_db.release()

        return True

    def get_user_rsa_pub(self, user_id):

        user_rsa = self.session.query(User).filter(User.uid == user_id)

        try:
            return user_rsa.one().rsa_pub
        except:
            return 0

    def salt_file(self, file_name, user_id):
        """this function search in data base a file
        and return your salt
        if don't find return 0
        """

        self.logger.info("salt_file invoked")

        file = self.session.query(File)
        file = file.filter(File.file_name == file_name)
        file = file.filter(File.user_id == user_id)
        result = file.all()
        if result == [] :
            return 0
        else:
            return result[0].salt
        
    def get_all_files_by_dir(self, dirname, user_id):

        self.logger.info("get_all_files_by_dir invoked")

        files = self.session.query(File).\
                filter(File.user_id == user_id).\
                filter(File.file_name.like(dirname+'%')).\
                order_by(File.file_name)
        """
         this returns everything that has the dirname as substring of its
         file_name, so beware, it's not just the files within it but also
         subdirectories and files.
         eg: dirname = '/foo'
         can return
            '/foo.txt'
            '/football'
            /foo/* < which is correct
            /foo/subfoo/*
        """
        return files.all()

    def get_all_users(self):
        """
            Query all users and return a LIST of USERS with your attr
        """

        self.logger.info("get_all_users invoked")

        return self.session.query(User).all()

    def get_all_files_by_user(self, user_id):
        """
            Query all metadata of files from a user
        """
        
        self.logger.info("get_all_files_by_user")
        
        return self.session.query(File).filter(File.user_id == user_id).all()
        
    def get_all_parts_file_by_vk(self, verify_key):
        """
            Query all metadata of parts (file)
        """
        
        self.logger.info("get_all_parts_file_by_vk")
        
        return self.session.query(Parts).filter(Parts.verify_key == verify_key).all()

    def get_if_part_exists(self, vk, server, part_number):
        '''
            Returns True if part's metadata already exists
            Returns False if it doesn't so it can be created
        '''
        self.logger.info("get_if_part_exists")

        (ret, ), = self.session.query(exists().
                                      where(Parts.verify_key == vk).
                                      where(Parts.server_id == server).
                                      where(Parts.num_part == part_number))
        return ret

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
