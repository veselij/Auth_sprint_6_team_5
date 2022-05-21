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

from core.config import config
from db.cache import get_cache_access, get_cache_refresh
from db.db import session_manager
from models.db_models import (
    User,
    UserAccessHistory,
    Role,
)
from services.common import get_object_by_field, create_obj_in_db, update_obj_in_db
from utils.password_hashing import get_password_hash


def create_user(username: str, password: str) -> bool:
    user = User(login=username, password=get_password_hash(password))
    return create_obj_in_db(user)


def log_login_attempt(user_id: str, status: bool) -> None:
    user_agent = request.headers.get("User-Agent")
    login_attempt = UserAccessHistory(user_id=user_id, user_agent=user_agent, login_status=status)
    create_obj_in_db(login_attempt)


def autorize_user(login: str, password: str) -> Optional[str]:
    user = get_object_by_field(User, login=login)
    if not user:
        return
    if not user.check_password(password):
        log_login_attempt(user.id, False)
        return
    log_login_attempt(user.id, True)
    return str(user.id)


def generate_tokens(user_id: str) -> dict[str, str]:
    roles = [str(r.id) for r in get_user_roles(user_id)]
    roles = []
    access_token = create_access_token(identity=user_id, additional_claims={"roles": roles})
    refresh_token = create_refresh_token(identity=user_id, additional_claims={"related_access_token": get_jti(access_token)})
    cache = get_cache_refresh()
    cache.set_value(name=str(get_jti(refresh_token)), value=user_id, ex=config.refresh_ttl)
    return {"access_token": access_token, "refresh_token": refresh_token}


def check_refresh_token(jwt: dict, user_id: str) -> bool:
    key = jwt.get("jti")
    cache = get_cache_refresh()
    user_id_cache = cache.get_value(key)
    if user_id != user_id_cache:
        return False
    return True


def check_revoked_token(user_id: str, token: dict) -> bool:
    if "related_access_token" in token:
        access_token = token["related_access_token"]
        exp = token["exp"] - config.refresh_ttl
    else:
        access_token = token["jti"]
        exp = token["exp"] - config.access_ttl
    cache = get_cache_access()
    revoked_tokens = cache.get_value(user_id)
    if not revoked_tokens:
        return False
    revoked_tokens = json.loads(revoked_tokens)
    if "all" in revoked_tokens:
        return exp <= float(revoked_tokens["all"])
    token_revoke_time = revoked_tokens.get(access_token, None)
    if token_revoke_time is None:
        return False
    return exp <= float(token_revoke_time)


def revoke_access_token(token: dict, user_id: str, all: str) -> None:
    if strtobool(all):
        jti = "all"
    else:
        jti = token["jti"]
    value = str(time())
    cache = get_cache_access()
    current_value = cache.get_value(str(user_id))
    if current_value:
        data = json.loads(current_value)
        data[jti] = value
    else:
        data = {jti: value}
    cache.set_value(str(user_id), json.dumps(data), ex=config.refresh_ttl)


def update_user_data(user: User, fields: dict) -> bool:
    if 'password' in fields:
        fields['password'] = get_password_hash(fields['password'])
    if not update_obj_in_db(obj=User, fileds_to_update=fields, id=user.id):
        return False
    return True


def get_user_history(user_id: str, page_num: int, page_items: int) -> Optional[UserAccessHistory]:
    start = (page_num - 1) * page_items
    end = start + page_items
    return get_user_history_from_db(user_id, start, end)


def get_user(user_id: str) -> Optional[User]:
    return get_object_by_field(User, id=user_id)


def get_user_history_from_db(user_id: str, start: int, end: int) -> Optional[UserAccessHistory]:
    with session_manager() as session:
        user_access_history = (
            session.query(UserAccessHistory).filter_by(user_id=user_id)
            .order_by(UserAccessHistory.login_date.desc())
            .slice(start, end)
        )
    return user_access_history


def get_user_roles(user_id: str) -> list[Role]:
    with session_manager() as session:
        roles = session.query(Role).join(User.roles).filter(User.id == user_id).all()
    return roles
