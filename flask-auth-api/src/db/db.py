from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from core.config import config, logger
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError

engine = create_engine(
    'postgresql://{username}:{password}@{host}/{database}'.format(
        username=config.pg_user,
        password=config.pg_password,
        host=config.pg_host,
        database=config.pg_database,
    ),
    convert_unicode=True,
)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def init_db():
    import models.db_models

    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError:
        raise RetryExceptionError('Database not available')
