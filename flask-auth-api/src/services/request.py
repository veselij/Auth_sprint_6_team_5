import json
from datetime import datetime
from typing import NamedTuple, Optional, Union

import pyotp
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from core.config import config
from db.cache import Caches
from models.db_models import User, UserAccessHistory
from repository.repository import Repositiry
from utils.exceptions import ObjectDoesNotExistError, TotpNotSyncError


class Token(NamedTuple):
    access_token: str
    refresh_token: str
    required_fields: list


class ProvisioningUrl(NamedTuple):
    url: str


class RedisUser(NamedTuple):
    id: str
    login: str
    is_superuser: bool
    totp_secret: str
    totp_sync: str
    totp_active: str
    required_fields: list
    roles: list


class RequestService:
    def __init__(self, repository: Repositiry, cache: Caches) -> None:
        self.cache = cache
        self.repository = repository

    def check_refresh_token(self, jwt: dict, user_id: str) -> bool:
        key = jwt.get("jti")
        user_id_cache = self.cache.refresh_cache.get_value(key)
        if user_id != user_id_cache:
            return False
        return True

    def generate_tokens(
        self, user_id: str, is_superuser: Union[bool, int], roles: list, required_fields: Optional[list] = None
    ) -> Token:
        required_fields = required_fields or []
        access_token = create_access_token(
            identity=user_id,
            additional_claims={"roles": roles, "admin": int(is_superuser)},
        )
        refresh_token = create_refresh_token(
            identity=user_id,
            additional_claims={"related_access_token": get_jti(access_token), "admin": int(is_superuser)},
        )
        self.cache.refresh_cache.set_value(name=str(get_jti(refresh_token)), value=user_id, ex=config.refresh_ttl)
        return Token(access_token, refresh_token, required_fields)

    def get_user_data_from_cache(self, request_id) -> RedisUser:
        user_data = self.cache.request_cache.get_value(request_id)
        if not user_data:
            raise ObjectDoesNotExistError
        return RedisUser(**json.loads(user_data))

    def update_user_secret(self, secret: str, user_id: str) -> None:
        self.repository.update_obj_in_db(User, {"totp_secret": secret}, id=user_id)

    def update_user_totp_status(self, user_id: str) -> None:
        self.repository.update_obj_in_db(User, {"totp_active": True, "totp_sync": True}, id=user_id)

    def generate_provisioning_url(self, request_id: str) -> ProvisioningUrl:
        user = self.get_user_data_from_cache(request_id)
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        self.update_user_secret(secret, user.id)
        provisioning_url = totp.provisioning_uri(name=user.login, issuer_name=config.project_name)
        return ProvisioningUrl(provisioning_url)

    def activate_totp(self, request_id: str, code: str) -> Token:
        user = self.get_user_data_from_cache(request_id)
        db_user = self.repository.get_object_by_field(User, id=user.id)
        if not db_user:
            raise ObjectDoesNotExistError
        totp = pyotp.TOTP(db_user.totp_secret)
        if not totp.verify(code):
            raise ObjectDoesNotExistError
        self.update_user_totp_status(user.id)
        return self.generate_tokens(user.id, user.is_superuser, user.roles, user.required_fields)

    def check_totp(self, request_id: str, code: str) -> Token:
        user = self.get_user_data_from_cache(request_id)
        if not user.totp_active:
            return self.generate_tokens(user.id, user.is_superuser, user.roles, user.required_fields)

        if not user.totp_sync:
            self.update_login_attempt(request_id)
            raise TotpNotSyncError

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code):
            self.update_login_attempt(request_id)
            raise ObjectDoesNotExistError
        return self.generate_tokens(user.id, user.is_superuser, user.roles, user.required_fields)

    def update_login_attempt(self, request_id: str):
        self.repository.update_obj_in_db(
            UserAccessHistory,
            {"totp_status": False},
            request_id=request_id,
            login_date=datetime.now().strftime("%Y-%m-%d"),
        )
