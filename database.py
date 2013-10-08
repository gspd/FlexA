#!/usr/bin/env python3

import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String

Base = declarative_base()

class File(Base):
    __tablename__ = 'file'

    id = Column(String(100), primary_key=True)
    valid_write = Column(String(100), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    crc32 = Column(String(8), nullable=False)
    posix_properties = Column(Integer)

    def __init__(self, id, valid_write, filename, crc32,
            posix_properties=None):
        self.id = id
        self.valid_write = valid_write
        self.filename = filename
        self.crc32 = crc32
        self.posix_properties = posix_properties

    def __repr__(self):
        return '<File({},{},{},{},{}>'.format(self.id, self.valid_write,
                self.filename, self.crc32, self.posix_properties)

def init_db(file_db='flexa-ng.sqlite3'):
    engine = create_engine('sqlite:///{}'.format(file_db), echo=True)
    if not os.path.exists(file_db):
        Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    return Session()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
