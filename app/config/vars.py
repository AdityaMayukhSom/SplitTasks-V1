from abc import ABC
from typing import Annotated

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvVars(BaseSettings, ABC):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
        validate_assignment=True,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )


class DBVars(EnvVars):
    protocol: str = Field(alias="DB_PROTOCOL", default="snorlax")
    username: str = Field(alias="DB_USERNAME", default="otto-octavius")
    password: str = Field(alias="DB_PASSWORD", default="password-password-who")
    hostname: str = Field(alias="DB_HOSTNAME", default="not-a-database.com")
    database: str = Field(alias="DB_DATABASE", default="ofcourse-non-prod")
    port: int = Field(alias="DB_PORT", default=6969)

    def get_database_url(self):
        conn_url = f"{self.protocol}://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.database}?sslmode=require"
        return conn_url


def get_db_vars():
    return DBVars()


DBVarsDep = Annotated[DBVars, Depends(get_db_vars)]


class JWTVars(EnvVars):
    signing_algo: str = Field(alias="JWT_SIGNING_ALGO", default="HS256")
    secret_key: str = Field(alias="JWT_SECRET_KEY", default="please-change-this-secret")
    expiry_minutes: int = Field(alias="JWT_EXPIRY_MINUTES", default=10)
    issuer: str = Field(alias="JWT_ISSUER", default="")
    # audience: str = Field(alias="JWT_AUDIENCE", default="")


def get_jwt_vars():
    return JWTVars()


JWTVarsDep = Annotated[JWTVars, Depends(get_jwt_vars)]
