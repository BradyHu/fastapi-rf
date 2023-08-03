from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CoreModel(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    __table_args__ = {'mysql_engine': 'InnoDB'}
    __mapper_args__ = {'always_refresh': True}

    @declared_attr
    def id(self):
        return Column(Integer, primary_key=True, comment='主键')

    @declared_attr
    def created_at(self):
        return Column(DateTime(), server_default=func.now(), comment='创建时间')

    @declared_attr
    def updated_at(self):
        return Column(DateTime, server_default=func.now(), server_onupdate=func.now(), comment='更新时间')
