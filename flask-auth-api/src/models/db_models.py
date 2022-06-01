import uuid
from datetime import datetime
from functools import partial
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.event import listen
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import UniqueConstraint

from db.db import Base
from utils.password_hashing import verify_password

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
    email = Column(String, nullable=True)
    roles = relationship("Role", secondary=user_role_association_table, back_populates="users")
    totp_secret = Column(String, nullable=True)
    totp_active = Column(Boolean, default=False, nullable=False)
    totp_sync = Column(Boolean, default=False, nullable=False)

    def __init__(self, login: str, password: str, email: Optional[str] = None, is_superuser: bool = False) -> None:
        self.login = login
        self.password = password
        self.is_superuser = is_superuser
        self.email = email

    def __repr__(self) -> str:
        return "User {0}".format(self.login)

    def check_password(self, password):
        return verify_password(password, self.password)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "login": self.login,
            "is_superuser": self.is_superuser,
            "totp_secret": self.totp_secret,
            "totp_sync": self.totp_sync,
            "totp_active": self.totp_active,
        }


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


def create_user_history_partitions(target, connection, **kw) -> None:
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_access_history_default" PARTITION OF "users_access_history" DEFAULT;"""
    )
    for m in range(month, 12):
        connection.execute(
            f"""CREATE TABLE IF NOT EXISTS "users_access_history_y{year}m{m}" PARTITION OF "users_access_history" FOR VALUES FROM ('{year}-{m}-01') TO ('{year}-{m + 1}-01')"""
        )


def on_table_create(class_, ddl):
    def listener(tablename, ddl, table, bind, **kw):
        if table.name == tablename:
            ddl(table, bind, **kw)

    listen(Table, "after_create", partial(listener, class_.__table__.name, ddl))


class UserAccessHistory(Base):
    __tablename__ = "users_access_history"
    __table_args__ = (
        UniqueConstraint("id", "login_date", name="user_acc_hist_id_login_date"),
        {
            "postgresql_partition_by": "RANGE (login_date)",
        },
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_agent = Column(String, nullable=True)
    login_date = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())
    login_status = Column(Boolean, nullable=False)
    service_name = Column(String, nullable=True)
    request_id = Column(String, nullable=False)
    totp_status = Column(Boolean, default=True, nullable=False)

    def __init__(
        self, user_id: UUID, user_agent: str, login_status: bool, request_id: str, service_name: Optional[str] = None
    ) -> None:
        self.user_id = user_id
        self.user_agent = user_agent
        self.login_status = login_status
        self.service_name = service_name
        self.request_id = request_id

    def __repr__(self) -> str:
        return "User {0} access {1} with status {2}".format(self.user_id, self.login_date, self.login_status)


class SocialAccount(Base):
    __tablename__ = "social_account"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref=backref("social_accounts", lazy=True))

    social_id = Column(String, nullable=False)
    social_name = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("social_id", "social_name", name="social_pk"),)

    def __init__(self, user_id: UUID, social_id: str, social_name: str) -> None:
        self.user_id = user_id
        self.social_id = social_id
        self.social_name = social_name

    def __repr__(self) -> str:
        return f"<SocialAccount {self.social_name}:{self.user_id}>"


on_table_create(UserAccessHistory, create_user_history_partitions)
