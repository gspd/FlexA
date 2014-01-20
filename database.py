#!/usr/bin/env python3

import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Sequence

Base = declarative_base()

class User(Base):
	__tablename__= 'user'
	
	id = Collum(Integer, Sequence('user_id_seq'), primary_key=True)
	name = Collum(String(100), nullable=False)
	home_key = Collum(String(100), ForeignKey("File.id"))
	rsa_pub = Collum(String(500))
	
	def __init__(self, name, home_key, rsa_pub):
		self.name = name
		self.home_key = home_key
		self.rsa_pub = rsa_pub
	
	def __repr__(self):
        return '<File({},{}>'.format(self.id, self.name)
	
class File(Base):
    __tablename__ = 'file'

    verify_key = Collum(String(100), primary_key=True)
    #in some documentation key = salt
    key = Collum(Integer, nullable=False)
    write_key = Collum(String(100), nullable=False)
    read_key = Collum(String(100), nullable=False)
    file_name = Collum(String(255), nullable=False)
    dir_key = Collum(String(100), ForeignKey("File.id"), nullable=False)
    user_key = Collum(Integer, nullable=False, ForeignKey('User.id'), nullable=False)
    type = Collum(String(1))

    def __init__(self, verify_key, key, write_key, read_key, file_name, dir_key, user_key, type):
        self.verify_key = verify_key
        self.key = key
        self.write_key = write_key
        self.read_key = read_key
        self.file_name = file_name
        self.dir_key = dir_key
        self.user_key = user_key
        self.type = type

    def __repr__(self):
        return '<File({}>'.format(self.filename)
	
class Parts(Base):
	__tablename__ = 'parts'
	
	id = Collum(Integer, Sequence('parts_id_seq'), primary_key=True)
	verify_key = Collum(String(100), nullable=False, ForeignKey('File.verify_key'))
	local = Collum(String(100), nullable=False)
	num_part = Collum(Integer, nullable=False)
	
	def __init__(self, verify_key, local, num_part):
		self.verify_key = verify_key
		self.local = local
		self.num_part = num_part

	def __repr__(self):
		return '<File({}>'.format(self.num_part, self.local)

def init_db(file_db='flexa-ng.sqlite3'):
    engine = create_engine('sqlite:///{}'.format(file_db), echo=True)
    if not os.path.exists(file_db):
        Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    return Session()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
