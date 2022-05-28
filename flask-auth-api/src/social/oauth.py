from authlib.integrations.flask_client import FlaskOAuth2App, OAuth

from core.config import config
from social.config import config_oauth
from social.providers import Providers


class CustomFlaskOAuth2App(FlaskOAuth2App):
    def authorize_access_token(self, **kwargs):
        token = {
            "access_token": config_oauth.yandex_test_token,
            "expires_in": config_oauth.yandex_test_token_exp,
            "token_type": "bearer",
        }
        self.token = token
        return token


class TestingOAuth(OAuth):
    oauth2_client_cls = CustomFlaskOAuth2App


if not config.test:
    oauth = OAuth()

    oauth.register(
        name=Providers.google.value,
        client_id=config_oauth.google_client_id,
        client_secret=config_oauth.google_secret_id,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
        },
    )

    oauth.register(
        name=Providers.yandex.value,
        client_id=config_oauth.yandex_client_id,
        client_secret=config_oauth.yandex_secret_id,
        authorize_url="https://oauth.yandex.ru/authorize",
        access_token_url="https://oauth.yandex.ru/token",
        api_base_url="https://login.yandex.ru/",
        userinfo_endpoint="info",
        client_kwargs={
            "scope": "login:email login:info",
        },
    )
else:
    oauth = TestingOAuth()

    oauth.register(
        name=Providers.yandex.value,
        client_id=config_oauth.yandex_client_id,
        client_secret=config_oauth.yandex_secret_id,
        authorize_url="https://oauth.yandex.ru/authorize",
        access_token_url=f"https://oauth.yandex.ru/authorize?response_type=token&client_id={config_oauth.yandex_client_id}",
        api_base_url="https://login.yandex.ru/",
        userinfo_endpoint="info",
        client_kwargs={
            "scope": "login:email login:info",
        },
    )
