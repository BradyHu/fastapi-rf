from sqlalchemy import Boolean, Column, Integer, String

from core.models import CoreModel, Base


class User(CoreModel, Base):
    __tablename__ = 'user_user'
    id = Column(Integer(), primary_key=True, index=True)
    username = Column(String(length=20), unique=True, index=True)
    nickname = Column(String(length=12))
    password = Column(String(length=255), nullable=True)
    # 账户信息
    email = Column(String(length=64), nullable=True)
    mobile = Column(String(length=32), nullable=True)

    is_active = Column(Boolean, default=True)


class VerifyCode(CoreModel, Base):
    __tablename__ = 'user_verifycode'
    id = Column(Integer(), primary_key=True, index=True)
    mobile = Column(String(length=15), index=True)
    code = Column(String(length=4))
    action = Column(String(length=10))
