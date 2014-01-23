#!/usr/bin/env python3

import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Sequence, DateTime

Base = declarative_base()

class User(Base):
	__tablename__= 'user'
	
	id = Column(String(64), primary_key=True)
	name = Column(String(100), nullable=False)
	home_key = Column(String(100))
	
	def __init__(self, name, home_key, rsa_pub):
		self.name = name
		self.home_key = home_key
		self.rsa_pub = rsa_pub
	
	def __repr__(self):
		return '<File({},{})>'.format(self.id, self.name)
	
class File(Base):
	__tablename__ = 'file'

	verify_key = Column(String(100), primary_key=True)
	#in some documentation key = salt
	salt = Column(Integer, nullable=False)
	write_key = Column(String(100), nullable=False)
	read_key = Column(String(100), nullable=False)
	file_name = Column(String(255), nullable=False)
	dir_key = Column(String(100), nullable=False)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	type = Column(String(1))

	def __init__(self, verify_key, salt, write_key, read_key, file_name, dir_key, user_id, type):
		self.verify_key = verify_key
		self.salt = salt
		self.write_key = write_key
		self.read_key = read_key
		self.file_name = file_name
		self.dir_key = dir_key
		self.user_id = user_id
		self.type = type

	def __repr__(self):
		return '<File({}>'.format(self.filename)

class Parts(Base):
	__tablename__ = 'parts'
	
	id = Column(Integer, Sequence('parts_id_seq'), primary_key=True)
	verify_key = Column(String(100), ForeignKey('file.verify_key'), nullable=False)
	local = Column(String(40), ForeignKey('server.id'))
	num_part = Column(Integer, nullable=False)
	
	def __init__(self, verify_key, local, num_part):
		self.verify_key = verify_key
		self.local = local
		self.num_part = num_part

	def __repr__(self):
		return '<File({})>'.format(self.num_part, self.local)

class Server(Base):
	__tablename__ = 'server'
	
	id = Column(String(40), nullable=False, primary_key=True)
	ip = Column(String(15), nullable=False)
	last_seen = Column(DateTime)

	def __init__(self, id, ip, last_seen):
		self.id = id
		self.ip = ip
		self.last_seen = last_seen

	def __repr__(self):
		return '<File({} {} {})>'.format(self.id, self.ip, self.last_seen)

def init_db(file_db='flexa.sqlite3'):
    engine = create_engine('sqlite:///{}'.format(file_db), echo=True)
    if not os.path.exists(file_db):
        Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    return Session()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
