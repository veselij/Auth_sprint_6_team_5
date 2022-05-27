from pydantic import BaseSettings, Field


class ConfigOauth(BaseSettings):
    google_client_id: str = Field("", env="GOOGLE_CLIENT_ID")
    google_secret_id: str = Field("", env="GOOGLE_CLIENT_SECRET")

    yandex_client_id: str = Field("", env="YANDEX_CLIENT_ID")
    yandex_secret_id: str = Field("", env="YANDEX_CLIENT_SECRET")

    yandex_test_token: str = Field("", env="YANDEX_TEST_TOKEN")
    yandex_test_token_exp: str = Field("", env="YANDEX_TEST_TOKEN_EXP")


config_oauth = ConfigOauth()
