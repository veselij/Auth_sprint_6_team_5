from dataclasses import dataclass
from typing import Any

from social.providers import Providers


@dataclass
class UserData:
    social_id: str
    social_service: str
    user_email: str


def get_user_data_from_google(token: dict, client: Any):
    user_data = token["userinfo"]
    return UserData(social_id=user_data["sub"], social_service=Providers.google.value, user_email=user_data["email"])


def get_user_data_from_yandex(token: dict, client: Any):
    user_data = client.userinfo()
    return UserData(
        social_id=user_data["psuid"], social_service=Providers.yandex.value, user_email=user_data["default_email"]
    )


user_data_registry = {
    Providers.google.value: get_user_data_from_google,
    Providers.yandex.value: get_user_data_from_yandex,
}
