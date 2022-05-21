from pydantic import BaseSettings, Field


class ConfigSettings(BaseSettings):
    redis_host: str = Field('127.0.0.1', env='REDIS_HOST')
    redis_port: str = Field('6379', env='REDIS_PORT')
    api_ip: str = Field('127.0.0.1', env='API_IP')
    api_port: str = Field(5000, env='API_IP_PORT')

    pg_host: str = Field("127.0.0.1", env="PG_HOST")
    pg_port: str = Field("5432", env="PG_PORT")
    pg_user: str = Field("app", env="PG_USER")
    pg_password: str = Field("123qwe", env="PG_PASSWORD")
    pg_db: str = Field("users", env="PG_DB")


config = ConfigSettings()
