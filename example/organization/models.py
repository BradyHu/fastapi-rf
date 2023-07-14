from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
import uuid

from config.database import Base
from user.models import User


class Organization(Base):
    __tablename__ = 'organization_organization'
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)


class UserCurrentOrganization(Base):
    __tablename__ = 'user_currentorganization'
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey(Organization.id, ondelete='CASCADE'))
    organization = relationship(Organization)
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    user = relationship(User, back_populates='current_organization')


User.current_organization = relationship(UserCurrentOrganization, back_populates="user")
