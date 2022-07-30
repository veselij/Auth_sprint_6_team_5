import logging
from typing import Optional

from pydantic import BaseSettings, Field

SWAGGER_TEMPLATE = {
    "components": {
        "securitySchemes": {
            "bearerAuth": {"type": "apiKey", "name": "Authorization", "in": "header"}
        }
    },
    "security": {"bearerAuth": []},
}


class ConfigSettings(BaseSettings):
    project_name: str = Field("Movies", env="PROJECT_NAME")
    test: bool = Field(True, env="FLASK_TESTING")

    logs: str = Field("error.log", env="LOGS_PATH")

    redis_host: str = Field("127.0.0.1", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")

    pg_host: str = Field("127.0.0.1", env="PG_HOST")
    pg_port: str = Field("5432", env="PG_PORT")
    pg_user: str = Field("app", env="PG_USER")
    pg_password: str = Field("123qwe", env="PG_PASSWORD")
    pg_database: str = Field("users", env="PG_DATABASE")

    superuser: Optional[str] = Field(None, env="SUPERUSER")
    superuser_password: Optional[str] = Field(None, env="SUPERUSER_PASSWORD")

    secret: str = Field(
        "7da9c735ec6e9e9c2a5a8731a39a3a71547c4c8f99d4057e1a5eab0243dc9938", env="SECRET"
    )
    access_ttl: int = Field(60 * 60, env="ACCESS_TTL")
    refresh_ttl: int = Field(60 * 60 * 24, env="REFRESH_TTL")

    api_name: str = Field("Auth API", env="API_NAME")
    uiversion: str = Field("3", env="UIVERSION")
    openapi: str = Field("3.0.2", env="OPENAPI")

    request_ttl: int = Field(60, env="REQUEST_TTL")

    jager_status: bool = Field(True, env="JAGER_STATUS")
    jager_host: str = Field("127.0.0.1", env="JAGER_HOST")

    google_client_id: str = Field("", env="GOOGLE_CLIENT_ID")
    google_secret_id: str = Field("", env="GOOGLE_CLIENT_SECRET")

    yandex_client_id: str = Field("", env="YANDEX_CLIENT_ID")
    yandex_secret_id: str = Field("", env="YANDEX_CLIENT_SECRET")

    yandex_test_token: str = Field("", env="YANDEX_TEST_TOKEN")
    yandex_test_token_exp: str = Field("", env="YANDEX_TEST_TOKEN_EXP")

    logstash_host: str = Field("logstash", env="LOGSTASH_HOST")
    logstash_port: int = Field(5044, env="LOGSTASH_PORT")

    bitly_api_access_token: str = Field("", env="BITLY_API_ACCESS_TOKEN")
    email_verification_period: int = Field(1, env="EMAIL_VERIFICATION_PERIOD")
    site_domain: str = Field("example.com", env="SITE_DOMAIN")
    redirect_url: str = Field("example.com", env="REDIRECT_URL")

    rabbit_host: str = Field("localhost", env="RABBIT_HOST")
    rabbit_queue: str = Field("WELCOME_QUEUE", env="RABBIT_QUEUE")
    notificaion_template: str = Field("123", env="NOTIFICATION_TEMPLATE")


config = ConfigSettings()

logger = logging.getLogger(__name__)
