from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy import event
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.expression import insert

from fastapi_rf.models import Base, CoreModel
from user.models import User


class Organization(CoreModel, Base):
    __tablename__ = 'organization_organization'
    uuid: Mapped[str] = mapped_column(unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, index=True)

# 用户当前所在机构，用户创建时，默认创建用户对应机构
class UserCurrentOrganization(CoreModel, Base):
    __tablename__ = 'organization_usercurrentorganization'
    organization_id: Mapped[int] = mapped_column(ForeignKey(Organization.id, ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    organization = relationship(Organization)
    user = relationship(User, back_populates='current_organization')


User.current_organization = relationship(UserCurrentOrganization, back_populates="user")


@event.listens_for(User, 'after_insert')
def user_create_default_organization(mapper, connection, target: User):
    # 创建用户默认机构
    organization_id = connection.execute(
        insert(Organization).values(
            name=target.nickname
        )
    ).inserted_primary_key[0]
    # 创建机构成员
    connection.execute(
        insert(OrganizationMember).values(
            organization_id=organization_id,
            user_id=target.id
        )
    )
    # 更新用户当前机构
    connection.execute(
        insert(UserCurrentOrganization).values(
            organization_id=organization_id,
            user_id=target.id
        )
    )


class OrganizationRole(CoreModel, Base):
    __tablename__ = 'organization_role'
    organization_id: Mapped[int] = mapped_column(ForeignKey(Organization.id, ondelete='CASCADE'))
    name: Mapped[str]
    description: Mapped[str]
    default: Mapped[bool] = mapped_column(default=False)
    customized: Mapped[bool] = mapped_column(default=True)


class OrganizationMember(CoreModel, Base):
    __tablename__ = 'organization_member'
    organization_id: Mapped[int] = mapped_column(ForeignKey(Organization.id, ondelete='CASCADE'), )
    organization = relationship(Organization, back_populates='org_members')
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    user = relationship(User, back_populates='org_members')


Organization.org_members: Mapped[list[OrganizationMember]] = relationship(OrganizationMember,
                                                                          back_populates='organization')
User.org_members: Mapped[list[OrganizationMember]] = relationship(OrganizationMember,
                                                                  back_populates='user')
User.organizations: Mapped[list[Organization]] = relationship(Organization, secondary='organization_member',
                                                              back_populates='users')

Organization.users: Mapped[list[User]] = relationship(User, secondary='organization_member',
                                                      back_populates='organizations')
