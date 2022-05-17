from typing import Optional, Type

from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError, OperationalError

from core.config import config, logger
from db.cache import Cache
from db.db import db_session
from models.db_models import User
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError
from utils.password_hashing import get_password_hash


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def create_user(username: str, password: str) -> Optional[User]:
    user = User(login=username, password=get_password_hash(password))
    db_session.add(user)
    try:
        db_session.commit()
    except IntegrityError:
        return
    except OperationalError:
        db_session.rollback()
        raise RetryExceptionError('Database not available')
    return user


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def autorize_user(login: str, password: str) -> Optional[User]:
    try:
        user = User.query.filter_by(login=login).one_or_none()
    except OperationalError:
        raise RetryExceptionError('Database not available')
    if not user or not user.check_password(password):
        return
    return user


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def generate_tokens(user: User, cache: Cache, exc: Type[Exception]) -> dict[str, str]:
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id, additional_claims={'access_token': access_token})
    try:
        cache.set(name=str(refresh_token), value=str(user.id), ex=config.refresh_ttl)
    except exc:
        raise RetryExceptionError('Cache is not available')
    return {'access_token': access_token, 'refresh_token': refresh_token}
