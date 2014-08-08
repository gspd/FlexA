#!/usr/bin/env python3

import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Sequence, DateTime
from threading import Lock
import time

Base = declarative_base()

class User(Base):
	__tablename__= 'user'
	
	uid = Column(String(64), primary_key=True)
	name = Column(String(100), nullable=False)
	home_key = Column(String(100))
	rsa_pub = Column(String(100))
	
	def __init__(self, uid, name, home_key, rsa_pub):
		self.uid = uid
		self.name = name
		self.home_key = home_key
		self.rsa_pub = rsa_pub
	
	def __repr__(self):
		return '<File({},{})>'.format(self.uid, self.name)
	
class File(Base):
	__tablename__ = 'file'

	verify_key = Column(String, primary_key=True)
	salt = Column(String, nullable=False)
	write_key = Column(String(100), nullable=False)
	read_key = Column(String(100), nullable=False)
	file_name = Column(String(255), nullable=False)
	dir_key = Column(String(100), nullable=False)
	user_id = Column(String, ForeignKey('user.uid'), nullable=False)
	types = Column(String(1))

	def __init__(self, verify_key, salt, write_key, read_key, file_name, dir_key, user_id, types):
		self.verify_key = verify_key
		self.salt = salt
		self.write_key = write_key
		self.read_key = read_key
		self.file_name = file_name
		self.dir_key = dir_key
		self.user_id = user_id
		self.types = types

	def __repr__(self):
		return '<File(vfk "{}", salt "{}", wtk "{}", rdk "{}", name "{}", dir "{}", user "{}", type "{}")>'.format(self.verify_key, self.salt, self.write_key, self.read_key, self.file_name, self.dir_key, self.user_id, self.types)

class Parts(Base):
	__tablename__ = 'parts'
	
	uid = Column(Integer, Sequence('parts_id_seq'), primary_key=True)
	verify_key = Column(String(100), ForeignKey('file.verify_key'), nullable=False)
	local = Column(String(40), ForeignKey('server.uid'))
	num_part = Column(Integer, nullable=False)
	
	def __init__(self, verify_key, local, num_part):
		self.verify_key = verify_key
		self.local = local
		self.num_part = num_part

	def __repr__(self):
		return '<File({})>'.format(self.num_part, self.local)

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
		return '<File({} {} {})>'.format(self.id, self.ip, self.last_seen)

class DataBase():
	"""class responsible for make every change and query in data base
	"""

	#variable to control max changes in data base before commit
	_max_modifies = 30
	#set interval to make commit by time in seconds
	_time_to_commit = 25

	def __init__(self, file_db='flexa.sqlite3'):
		engine = create_engine('sqlite:///{}'.format(file_db), connect_args={'check_same_thread':False}, echo=True)
		if not os.path.exists(file_db):
			Base.metadata.create_all(engine)
		Session = sessionmaker(bind=engine)
		self.session = Session()

		#Semaphores to control concurrence in data base
		#save_db is used to commit, put in hd every changes - slow
		self.save_db = Lock()
		#modify_db is used to add, modify, flush in :memory: database - fast
		self.modify_db = Lock()
		#modifies start in 0
		self.num_modifies = 0

	def commit_db(self):
		"""This function make commit in data base.
		   It can't call in anywhere, this function is controled by Semaphores (save_db, modify_db, num_modifies) 
		"""
		self.save_db.acquire()
		self.session.commit()
		self.save_db.release()

	def daemon(self):
		while True:
			time.sleep(self._time_to_commit)
			self.commit_db()

	def add(self, new_obj):
		"""Put a new object in database
		Use Semaphores to control concurrence
		When there are more then  modifies execute commit_db()
		"""

		#block semaphore
		self.modify_db.acquire()

		#try add new object in database, if don't have success rollback
		try:
			self.session.add(new_obj)
			self.session.flush()

			#verify if have more then 10 modifies
			if self.num_modifies < self._max_modifies:
				self.num_modifies+= 1
			else:
				self.num_modifies = 0
				self.commit_db()
		except:
			#TODO: implement rollback
			pass

		#unblock semaphore
		self.modify_db.release()

	def  exist_file(self, file_name, dir_key, user_id):

		file = self.session.query(File)
		file = file.filter(File.file_name == "foto1.jpg")
		file = file.filter(File.user_id == "1")
		result = file.all()
		if result == [] :
			print("arquivo não encontrado")
			return 0
		else:
			print("arquivo encontrado")
			print("resultado da pesquisa",result)
			return result[0].salt

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
