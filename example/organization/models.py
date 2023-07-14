from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column, sessionmaker
from sqlalchemy.sql.expression import insert
from sqlalchemy import event
import uuid

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
    organization_id = connection.execute(
        insert(Organization).values(
            name=target.nickname
        )
    ).inserted_primary_key[0]
    connection.execute(
        insert(UserCurrentOrganization).values(
            organization_id=organization_id,
            user_id=target.id
        )
    )


class OrganizationRole(CoreModel, Base):
    organization_id: Mapped[int] = mapped_column(ForeignKey(Organization, ondelete='CASCADE'))
    name: Mapped[str]
    description: Mapped[str]
    default: Mapped[bool] = mapped_column(default=False)
    customized: Mapped[bool] = mapped_column(default=True)


class OrganizationMember(CoreModel, Base):
    pass
