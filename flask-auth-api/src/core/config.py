from typing import Optional
from pydantic import BaseSettings, Field


class ConfigSettings(BaseSettings):
    redis_host: str = Field('127.0.0.1', env='REDIS_HOST')
    redis_port: str = Field('6379', env='REDIS_PORT')
    pg_host: str = Field('127.0.0.1', env='PG_HOST')
    pg_port: str = Field('5432', env='PG_PORT')
    pg_user: str = Field('app', env='PG_USER')
    pg_password: str = Field('123qwe', env='PG_PASSWORD')
    pg_database: str = Field('users', env='PG_DATABASE')
    superuser: Optional[str] = Field(None, env='SUPERUSER')
    superuser_password: Optional[str] = Field(None, env='SUPERUSER_PASSWORD')
    secret: str = Field('7da9c735ec6e9e9c2a5a8731a39a3a71547c4c8f99d4057e1a5eab0243dc9938', env='SECRET')


config = ConfigSettings()
