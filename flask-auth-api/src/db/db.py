from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from core.config import config

engine = create_engine(
    "postgresql://{username}:{password}@{host}/{database}".format(
        username=config.pg_user, password=config.pg_password, host=config.pg_host, database=config.pg_database,
    ), convert_unicode=True,
)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    import models.db_models
    Base.metadata.create_all(bind=engine)
