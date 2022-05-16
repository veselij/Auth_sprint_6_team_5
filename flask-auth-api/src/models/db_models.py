import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.db import Base

user_role_association_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    roles = relationship("Role", secondary=user_role_association_table, back_populates="users")

    def __init__(self, login: str, password: str, is_superuser: bool = False) -> None:
        self.login = login
        self.password = password
        self.is_superuser = is_superuser

    def __repr__(self) -> str:
        return "User {0}".format(self.login)


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    role = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    users = relationship("User", secondary=user_role_association_table, back_populates="roles")

    def __init__(self, role: str, description: str) -> None:
        self.role = role
        self.description = description

    def __repr__(self) -> str:
        return "Role {0}".format(self.role)


class UserAccessHistory(Base):
    __tablename__ = "users_access_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_agent = Column(String, nullable=True)
    login_date = Column(DateTime(timezone=True), server_default=func.now())
    login_status = Column(Boolean, nullable=False)

    def __init__(self, user_id, user_agent, login_status) -> None:
        self.user_id = user_id
        self.user_agent = user_agent
        self.login_status = login_status

    def __repr__(self) -> str:
        return "User {0} access {1} with status {2}".format(self.user_id, self.login_date, self.login_status)
