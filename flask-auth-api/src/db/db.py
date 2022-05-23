from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from core.config import config

Base = declarative_base()


class Database:
    def __init__(self) -> None:
        self.engine = create_engine(
            "postgresql://{username}:{password}@{host}/{database}".format(
                username=config.pg_user,
                password=config.pg_password,
                host=config.pg_host,
                database=config.pg_database,
            ),
            convert_unicode=True,
            pool_size=10,
            max_overflow=20,
        )
        self.db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))

    @contextmanager
    def session_manager(self):
        session: Session = self.db_session()
        try:
            yield session
        finally:
            session.close()
