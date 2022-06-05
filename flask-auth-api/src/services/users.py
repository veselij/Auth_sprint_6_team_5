import json
from dataclasses import asdict, dataclass, fields
from distutils.util import strtobool
from time import time
from typing import NamedTuple, Optional

from flask import request
from flask_jwt_extended import decode_token
from flask_jwt_extended.utils import get_jti
from sqlalchemy import extract
from sqlalchemy.dialects.postgresql.base import UUID

from core.config import config
from db.cache import Caches
from models.db_models import Role, SocialAccount, User, UserAccessHistory
from repository.repository import Repositiry
from social.userdata import UserData
from utils.exceptions import (
    ConflictError,
    InvalidTokenError,
    LoginPasswordError,
    ObjectDoesNotExistError,
)
from utils.password_hashing import generate_random_string, get_password_hash
from utils.tracing import tracing
from utils.tokens import Token, get_token
from utils.view_decorators import check_revoked_token


@dataclass
class UserRandomFields:
    login: str = generate_random_string()
    password: str = get_password_hash(generate_random_string())


class RequestId(NamedTuple):
    request_id: str
    totp_active: bool
    token: Optional[Token]


class UserService:
    def __init__(self, repository: Repositiry, cache: Caches) -> None:
        self.repository = repository
        self.cache = cache

    @tracing
    def create_user(self, username: str, password: str) -> bool:
        user = User(login=username, password=get_password_hash(password))
        return self.repository.create_obj_in_db(user)

    def log_login_attempt(
        self,
        user_id: UUID,
        status: bool,
        request_id: str,
        social_service: Optional[str] = None,
    ) -> None:
        user_agent = request.headers.get("User-Agent")
        login_attempt = UserAccessHistory(
            user_id=user_id,
            user_agent=user_agent,
            login_status=status,
            request_id=request_id,
            service_name=social_service,
        )
        self.repository.create_obj_in_db(login_attempt)

    def autorize_user(self, login: str, password: str) -> RequestId:
        user = self.repository.get_object_by_field(User, login=login)
        request_id = generate_random_string()
        if not user:
            raise LoginPasswordError
        if not user.check_password(password):
            self.log_login_attempt(user.id, False, request_id)
            raise LoginPasswordError
        self.log_login_attempt(user.id, True, request_id)
        return self.generate_request_id(user, request_id)

    def put_user_data_to_cache(self, user: User, request_id: str, required_fields: list) -> None:
        user_data = user.to_dict()
        user_data["required_fields"] = required_fields
        user_data["roles"] = self.get_user_roles(user.id)
        self.cache.request_cache.set_value(request_id, json.dumps(user_data), config.request_ttl)

    def generate_request_id(self, user: User, request_id: str, required_fields: Optional[list] = None) -> RequestId:
        if user.totp_active:
            token = None
            required_fields = required_fields or []
            self.put_user_data_to_cache(user, request_id, required_fields)
        else:
            token = get_token(user.id, user.is_superuser, self.get_user_roles(user.id), [])
            self.cache.refresh_cache.set_value(
                name=str(get_jti(token.refresh_token)), value=str(user.id), ex=config.refresh_ttl
            )
        return RequestId(request_id=request_id, totp_active=user.totp_active, token=token)

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

    def update_user_data(self, user: User, fields: dict) -> None:
        if "password" in fields:
            fields["password"] = get_password_hash(fields["password"])
        if not self.repository.update_obj_in_db(obj=User, fileds_to_update=fields, id=user.id):
            raise ConflictError

    def get_user_history(
        self, user_id: str, page_num: int, page_items: int, year: int, month: int
    ) -> Optional[UserAccessHistory]:
        start = (page_num - 1) * page_items
        end = start + page_items
        return self.get_user_history_from_db(user_id, start, end, year, month)

    def get_user(self, user_id: str) -> Optional[User]:
        return self.repository.get_object_by_field(User, id=user_id)

    def get_user_history_from_db(
        self, user_id: str, start: int, end: int, year: int, month: int
    ) -> Optional[UserAccessHistory]:
        user_access_history = self.repository.get_objects_by_field(UserAccessHistory, user_id=user_id)
        if user_access_history:
            month_user_access_history = user_access_history.filter(
                extract("month", UserAccessHistory.login_date) == month
            ).filter(extract("year", UserAccessHistory.login_date) == year)
            return month_user_access_history.order_by(UserAccessHistory.login_date.desc()).slice(start, end)

    def get_user_roles(self, user_id: str) -> list[Optional[str]]:
        roles = self.repository.get_joined_objects_by_field(Role, User.roles)
        if roles:
            return [str(r.role) for r in roles.filter(User.id == user_id).all()]
        return []

    def add_user_roles(self, user_id: str, role_ids: list) -> bool:
        self.revoke_access_token({}, user_id, "true")
        return self.repository.add_many_to_many_row(User, user_id, Role, role_ids, "roles")

    def remove_user_roles(self, user_id: str, role_ids: list) -> bool:
        self.revoke_access_token({}, user_id, "true")
        return self.repository.remove_many_to_many_row(User, user_id, Role, role_ids, "roles")

    def check_user_roles(self, access_token: str) -> list:
        token = decode_token(access_token)
        if check_revoked_token(token):
            raise InvalidTokenError
        return token["roles"]

    def create_random_user(self, email: str) -> Optional[User]:
        attempts = 3
        while attempts > 0:
            random_fields = UserRandomFields()
            user = User(**asdict(random_fields))
            user.email = email
            if self.repository.create_obj_in_db(user):
                return self.repository.get_object_by_field(User, login=random_fields.login)
            attempts -= 1
        return

    def create_social_account(self, user_data: UserData) -> User:
        user = self.create_random_user(user_data.user_email)
        if not user:
            raise ConflictError
        social_account = SocialAccount(
            social_id=user_data.social_id,
            social_name=user_data.social_service,
            user_id=user.id,
        )
        self.repository.create_obj_in_db(social_account)
        self.log_login_attempt(user.id, True, user_data.social_service)
        return user

    def login_via_social_provider(self, user_data: UserData) -> RequestId:
        social_account = self.repository.get_object_by_field(
            SocialAccount,
            social_id=user_data.social_id,
            social_name=user_data.social_service,
        )
        request_id = generate_random_string()
        if not social_account:
            user = self.create_social_account(user_data)
            required_fields = [field.name for field in fields(UserRandomFields)]
            return self.generate_request_id(user, request_id, required_fields)

        user = self.repository.get_object_by_field(User, id=social_account.user_id)
        if not user:
            raise ObjectDoesNotExistError
        self.log_login_attempt(user.id, True, user_data.social_service)
        return self.generate_request_id(user, request_id)

    def delete_social_account(self, token: dict, provider: str) -> None:
        user_id = str(token["sub"])
        self.revoke_access_token(token, user_id, "true")
        if not self.repository.delete_object_by_field(SocialAccount, user_id=user_id, social_name=provider):
            raise ObjectDoesNotExistError
