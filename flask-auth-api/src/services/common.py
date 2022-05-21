from typing import Optional

from sqlalchemy.exc import IntegrityError, OperationalError

from core.config import logger
from db.db import Base, session_manager
from utils.exceptions import RetryExceptionError
from utils.decorators import backoff


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def create_obj_in_db(obj: Base) -> bool:
    with session_manager() as session:
        try:
            session.add(obj)
            session.commit()
        except IntegrityError:
            session.rollback()
            return False
        except OperationalError:
            session.rollback()
            raise RetryExceptionError('Database not available')
    return True


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def update_obj_in_db(obj: type[Base], fileds_to_update: dict, **kwargs) -> bool:
    with session_manager() as session:
        try:
            session.query(obj).filter_by(**kwargs).update(fileds_to_update, synchronize_session="fetch")
            session.commit()
        except IntegrityError:
            session.rollback()
            return False
        except OperationalError:
            session.rollback()
            raise RetryExceptionError('Database not available')
    return True


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def get_object_by_field(obj: type[Base], **kwargs) -> Optional[Base]:
    with session_manager() as session:
        try:
            obj_instance = session.query(obj).filter_by(**kwargs).one_or_none()
        except OperationalError:
            raise RetryExceptionError('Database not available')
    return obj_instance
