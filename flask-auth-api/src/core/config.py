import logging
from typing import Optional

from pydantic import BaseSettings, Field


class ConfigSettings(BaseSettings):
    logs: str = Field('error.log', env='LOGS_PATH')

    redis_host: str = Field('127.0.0.1', env='REDIS_HOST')
    redis_port: int = Field(6379, env='REDIS_PORT')

    pg_host: str = Field('127.0.0.1', env='PG_HOST')
    pg_port: str = Field('5432', env='PG_PORT')
    pg_user: str = Field('app', env='PG_USER')
    pg_password: str = Field('123qwe', env='PG_PASSWORD')
    pg_database: str = Field('users', env='PG_DATABASE')

    superuser: Optional[str] = Field(None, env='SUPERUSER')
    superuser_password: Optional[str] = Field(None, env='SUPERUSER_PASSWORD')

    secret: str = Field('7da9c735ec6e9e9c2a5a8731a39a3a71547c4c8f99d4057e1a5eab0243dc9938', env='SECRET')
    access_ttl: int = Field(10 * 60, env='ACCESS_TTL')
    refresh_ttl: int = Field(10 * 60 * 24, env='REFRESH_TTL')

    api_name: str = Field('Auth API', env='API_NAME')
    uiversion: str = Field('3', env='UIVERSION')
    openapi: str = Field('3.0.2', env='OPENAPI')


config = ConfigSettings()


logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(filename=config.logs)
fh.setFormatter(formatter)
logger.addHandler(fh)
