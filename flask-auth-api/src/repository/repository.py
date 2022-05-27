from contextlib import AbstractContextManager
from typing import Callable, Optional

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from core.config import logger
from db.db import Base
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError


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
                raise RetryExceptionError("Database not available")
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
                raise RetryExceptionError("Database not available")
        return True

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def get_object_by_field(self, obj: type[Base], **kwargs) -> Optional[Base]:
        with self.session_factory() as session:
            try:
                obj_instance = session.query(obj).filter_by(**kwargs).one_or_none()
            except OperationalError:
                raise RetryExceptionError("Database not available")
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
                raise RetryExceptionError("Database not available")
        return obj_instance

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def get_joined_objects_by_field(self, obj: type[Base], joined_obj: InstrumentedAttribute) -> Optional[Base]:
        with self.session_factory() as session:
            try:
                objs = session.query(obj).join(joined_obj)
            except OperationalError:
                raise RetryExceptionError("Database not available")
        return objs

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
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
                raise RetryExceptionError("Database not available")
            return True

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def add_many_to_many_row(
        self,
        main_obj: type[Base],
        main_id: str,
        related_obj: type[Base],
        related_values: list,
        update_field: str,
    ) -> bool:
        with self.session_factory() as session:
            try:
                m_obj = session.query(main_obj).filter_by(id=main_id).one_or_none()
                if not m_obj:
                    session.rollback()
                    return False
                for related_value in related_values:
                    r_obj = session.query(related_obj).filter_by(id=related_value).one_or_none()
                    if not r_obj:
                        session.rollback()
                        return False
                    getattr(m_obj, update_field).append(r_obj)
                session.add(m_obj)
                session.commit()
            except OperationalError:
                session.rollback()
                raise RetryExceptionError("Database not available")
            return True

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def remove_many_to_many_row(
        self,
        main_obj: type[Base],
        main_id: str,
        related_obj: type[Base],
        related_values: list,
        update_field: str,
    ) -> bool:
        with self.session_factory() as session:
            try:
                m_obj = session.query(main_obj).filter_by(id=main_id).one_or_none()
                if not m_obj:
                    session.rollback()
                    return False
                for related_value in related_values:
                    r_obj = session.query(related_obj).filter_by(id=related_value).one_or_none()
                    if not r_obj:
                        session.rollback()
                        return False
                    getattr(m_obj, update_field).remove(r_obj)
                session.add(m_obj)
                session.commit()
            except OperationalError:
                session.rollback()
                raise RetryExceptionError("Database not available")
            return True

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def refresh_object(self, obj: Base) -> Base:
        with self.session_factory() as session:
            return session.refresh(obj)
