from contextlib import AbstractContextManager
from typing import Optional, Callable

from sqlalchemy.exc import OperationalError, IntegrityError

from core.config import logger
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from db.db import Base


class Repositiry:

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        self.session_factory = session_factory

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def create_obj_in_db(self, obj: type[Base]) -> bool:
        with self.session_factory() as session:
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
    def update_obj_in_db(self, obj: type[Base], fileds_to_update: dict, **kwargs) -> bool:
        with self.session_factory() as session:
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
    def get_object_by_field(self, obj: type[Base], **kwargs) -> Optional[Base]:
        with self.session_factory() as session:
            try:
                obj_instance = session.query(obj).filter_by(**kwargs).one_or_none()
            except OperationalError:
                raise RetryExceptionError('Database not available')
        return obj_instance
    
    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def get_objects_by_field(self, obj: type[Base], **kwargs) -> Optional[Base]:
        with self.session_factory() as session:
            try:
                if kwargs:
                    obj_instance = session.query(obj).filter_by(**kwargs)
                else:
                    obj_instance = session.query(obj).all()
            except OperationalError:
                raise RetryExceptionError('Database not available')
        return obj_instance

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def get_joined_objects_by_field(self, obj: type[Base], joined_obj: InstrumentedAttribute) -> Optional[Base]:
        with self.session_factory() as session:
            try:
                objs = session.query(obj).join(joined_obj)
            except OperationalError:
                raise RetryExceptionError('Database not available')
        return objs

    def delete_object_by_field(self, obj: type[Base], **kwargs) -> bool:
        with self.session_factory() as session:
            try:
                obj = session.query(obj).filter_by(**kwargs).one_or_none()
                if not obj:
                    return False
                session.delete(obj)
                session.commit()
            except OperationalError:
                session.rollback()
                raise RetryExceptionError('Database not available')
            return True
