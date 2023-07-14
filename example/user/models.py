from __future__ import annotations
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from fastapi_rf.models import CoreModel, Base
import uuid


class User(CoreModel, Base):
    """用户"""
    __tablename__ = 'user_user'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(length=64), default=lambda: str(uuid.uuid4()), nullable=False)
    username: Mapped[str | None] = mapped_column(String(length=20), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String())
    password: Mapped[str | None] = mapped_column(String(length=255))
    # 账户信息
    email: Mapped[str | None] = mapped_column(String(length=64))
    mobile: Mapped[str | None] = mapped_column(String(length=32))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    social_authes: Mapped[list[UserSocialAuth]] = relationship(back_populates='user')


class VerifyCode(CoreModel, Base):
    """验证码"""
    __tablename__ = 'user_verifycode'
    id: Mapped[int] = mapped_column(Integer(), primary_key=True, index=True)
    mobile: Mapped[str] = mapped_column(String(length=15), index=True)
    code: Mapped[str] = mapped_column(String(length=4))
    action: Mapped[str] = mapped_column(String(length=10))


class UserSocialAuth(CoreModel, Base):
    """社交账号登录"""
    __tablename__ = "user_socialauth"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    user: Mapped[User] = relationship(back_populates='social_authes')
    provider: Mapped[str] = mapped_column(String(length=12), nullable=False)
    uid: Mapped[str] = mapped_column(String(length=64), index=True)
