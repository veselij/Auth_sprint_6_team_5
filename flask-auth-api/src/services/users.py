import json
from typing import Optional
from time import time

from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti
from sqlalchemy.exc import OperationalError

from core.config import config, logger
from db.cache import CacheManager
from db.db import db_session, commit_session
from models.db_models import User, UserAccessHistory
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError
from utils.password_hashing import get_password_hash


def create_user(username: str, password: str) -> Optional[User]:
    user = User(login=username, password=get_password_hash(password))
    db_session.add(user)
    commited = commit_session()
    if not commited:
        return
    return user


def log_login_attempt(user_id: str, status: bool) -> None:
    user_agent = request.headers.get('User-Agent')
    login_attempt = UserAccessHistory(user_id=user_id, user_agent=user_agent, login_status=status)
    db_session.add(login_attempt)
    commit_session()


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def autorize_user(login: str, password: str) -> Optional[User]:
    try:
        user = User.query.filter_by(login=login).one_or_none()
    except OperationalError:
        raise RetryExceptionError('Database not available')
    if not user:
        return
    if not user.check_password(password):
        log_login_attempt(user.id, False)
        return
    log_login_attempt(user.id, True)
    return user


def generate_tokens(user_id: str, cache: CacheManager) -> dict[str, str]:
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id, additional_claims={'access_token': get_jti(access_token)})
    cache.set_value(name=str(get_jti(refresh_token)), value=user_id, ex=config.refresh_ttl)
    return {'access_token': access_token, 'refresh_token': refresh_token}


def check_refresh_token(jwt: dict, cache: CacheManager, user_id: str) -> bool:
    key = jwt.get('jti')
    user_id_cache = cache.get_value(key)
    if not user_id:
        return False
    if user_id != user_id_cache:
        return False
    return True


def check_revoked_token(user_id: str, cache: CacheManager, token: dict) -> bool:
    access_token = token['access_token']
    exp = token['exp']
    revoked_tokens = cache.get_value(user_id)
    if not revoked_tokens:
        return True
    revoked_tokens = json.loads(revoked_tokens)
    if 'all' in revoked_tokens:
        return exp <= float(revoked_tokens['all'])
    token_revoke_time = revoked_tokens.get(access_token, None)
    if token_revoke_time is None:
        return True
    return exp <= float(token_revoke_time)


def revoke_access_token(token: dict, cache: CacheManager, user_id: str, all: bool = False) -> None:
    if all:
        jti = 'all'
    else:
        jti = token['jti']
    value = str(time())
    current_value = cache.get_value(str(user_id))
    if current_value:
        data = json.loads(current_value)
        data[jti] = value
    else:
        data = {jti: value}
    cache.set_value(str(user_id), json.dumps(data), ex=config.refresh_ttl)
