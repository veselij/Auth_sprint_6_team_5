import json
from distutils.util import strtobool
from time import time
from typing import Optional

from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jti,
    get_jwt_identity,
)
from marshmallow import ValidationError
from marshmallow.schema import Schema

from core.config import config
from db.cache import CacheManager
from db.db import commit_session, db_session
from models.db_models import User, UserAccessHistory, get_user, get_user_history_from_db
from utils.password_hashing import get_password_hash


def create_user(username: str, password: str) -> Optional[User]:
    user = User(login=username, password=get_password_hash(password))
    db_session.add(user)
    commited = commit_session()
    if not commited:
        return
    return user


def log_login_attempt(user_id: str, status: bool) -> None:
    user_agent = request.headers.get("User-Agent")
    login_attempt = UserAccessHistory(user_id=user_id, user_agent=user_agent, login_status=status)
    db_session.add(login_attempt)
    commit_session()


def autorize_user(login: str, password: str) -> Optional[User]:
    user = get_user(login)
    if not user:
        return
    if not user.check_password(password):
        log_login_attempt(user.id, False)
        return
    log_login_attempt(user.id, True)
    return user


def generate_tokens(user_id: str, cache: CacheManager) -> dict[str, str]:
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id, additional_claims={"access_token": get_jti(access_token)})
    cache.set_value(name=str(get_jti(refresh_token)), value=user_id, ex=config.refresh_ttl)
    return {"access_token": access_token, "refresh_token": refresh_token}


def check_refresh_token(jwt: dict, cache: CacheManager, user_id: str) -> bool:
    key = jwt.get("jti")
    user_id_cache = cache.get_value(key)
    if user_id != user_id_cache:
        return False
    return True


def check_revoked_token(user_id: str, cache: CacheManager, token: dict) -> bool:
    access_token = token["access_token"] if "access_token" in token else get_jwt_identity()
    exp = token["exp"]
    revoked_tokens = cache.get_value(user_id)
    if not revoked_tokens:
        return False
    revoked_tokens = json.loads(revoked_tokens)
    if "all" in revoked_tokens:
        return exp <= float(revoked_tokens["all"])
    token_revoke_time = revoked_tokens.get(access_token, None)
    if token_revoke_time is None:
        return False
    return exp - config.refresh_ttl <= float(token_revoke_time)


def revoke_access_token(token: dict, cache: CacheManager, user_id: str, all: str) -> None:
    if strtobool(all):
        jti = "all"
    else:
        jti = token["jti"]
    value = str(time())
    current_value = cache.get_value(str(user_id))
    if current_value:
        data = json.loads(current_value)
        data[jti] = value
    else:
        data = {jti: value}
    cache.set_value(str(user_id), json.dumps(data), ex=config.refresh_ttl)


def update_user_data(user: User, login: str, password: str) -> bool:
    user.login = login
    user.password = get_password_hash(password)
    if not commit_session():
        return False
    return True


def get_user_history(user_id: str, schema: type[Schema], page_num: int, page_items: int) -> Optional[list[dict]]:
    start = (page_num - 1) * page_items + 1
    end = start + page_items
    try:
        user_history = schema(many=True).dump(get_user_history_from_db(user_id, start, end))
    except ValidationError:
        return
    return user_history
