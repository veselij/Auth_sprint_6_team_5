import json
from distutils.util import strtobool
from time import time
from typing import Optional

from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jti,
)

from core.config import config
from db.cache import Caches
from models.db_models import (
    User,
    UserAccessHistory,
    Role,
)
from repository.repository import Repositiry
from utils.password_hashing import get_password_hash


class UserService:

    def __init__(self, repository: Repositiry, cache: Caches) -> None:
        self.repository = repository
        self.cache = cache
        
    def create_user(self, username: str, password: str) -> bool:
        user = User(login=username, password=get_password_hash(password))
        return self.repository.create_obj_in_db(user)


    def log_login_attempt(self, user_id: str, status: bool) -> None:
        user_agent = request.headers.get("User-Agent")
        login_attempt = UserAccessHistory(user_id=user_id, user_agent=user_agent, login_status=status)
        self.repository.create_obj_in_db(login_attempt)


    def autorize_user(self, login: str, password: str) -> Optional[User]:
        user = self.repository.get_object_by_field(User, login=login)
        if not user:
            return
        if not user.check_password(password):
            self.log_login_attempt(user.id, False)
            return
        self.log_login_attempt(user.id, True)
        return user


    def generate_tokens(self, user_id: str, is_superuser: bool) -> dict[str, str]:
        roles = [str(r.id) for r in self.get_user_roles(user_id)]
        access_token = create_access_token(identity=user_id, additional_claims={"roles": roles, "admin": int(is_superuser)})
        refresh_token = create_refresh_token(identity=user_id, additional_claims={"related_access_token": get_jti(access_token), "admin": int(is_superuser)})
        self.cache.refresh_cache.set_value(name=str(get_jti(refresh_token)), value=user_id, ex=config.refresh_ttl)
        return {"access_token": access_token, "refresh_token": refresh_token}


    def check_refresh_token(self, jwt: dict, user_id: str) -> bool:
        key = jwt.get("jti")
        user_id_cache = self.cache.refresh_cache.get_value(key)
        if user_id != user_id_cache:
            return False
        return True

    def revoke_access_token(self, token: dict, user_id: str, all: str) -> None:
        if strtobool(all):
            jti = "all"
        else:
            jti = token["jti"]
        value = str(time())
        current_value = self.cache.access_cache.get_value(str(user_id))
        if current_value:
            data = json.loads(current_value)
            data[jti] = value
        else:
            data = {jti: value}
        self.cache.access_cache.set_value(str(user_id), json.dumps(data), ex=config.refresh_ttl)


    def update_user_data(self, user: User, fields: dict) -> bool:
        if 'password' in fields:
            fields['password'] = get_password_hash(fields['password'])
        if not self.repository.update_obj_in_db(obj=User, fileds_to_update=fields, id=user.id):
            return False
        return True


    def get_user_history(self, user_id: str, page_num: int, page_items: int) -> Optional[UserAccessHistory]:
        start = (page_num - 1) * page_items
        end = start + page_items
        return self.get_user_history_from_db(user_id, start, end)


    def get_user(self, user_id: str) -> Optional[User]:
        return self.repository.get_object_by_field(User, id=user_id)


    def get_user_history_from_db(self, user_id: str, start: int, end: int) -> Optional[UserAccessHistory]:
        user_access_history = self.repository.get_objects_by_field(UserAccessHistory, user_id=user_id)
        if user_access_history:
            return user_access_history.order_by(UserAccessHistory.login_date.desc()).slice(start, end)

    def get_user_roles(self, user_id: str) -> list[Role]:
        roles = self.repository.get_joined_objects_by_field(Role, User.roles)
        if roles:
            return roles.filter(User.id == user_id).all()
        return []
