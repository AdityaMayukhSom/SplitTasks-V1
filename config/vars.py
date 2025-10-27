from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvVars(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
    )

    pg_username: str = Field(alias="PG_USERNAME", default="")
    pg_password: str = Field(alias="PG_PASSWORD", default="")
    pg_hostname: str = Field(alias="PG_HOSTNAME", default="")
    pg_database: str = Field(alias="PG_DATABASE", default="")
    pg_port: int = Field(alias="PG_PORT", default=5432)

    def get_database_url(self):
        conn_url = f"postgresql://{self.pg_username}:{self.pg_password}@{self.pg_hostname}:{self.pg_port}/{self.pg_database}?sslmode=require"
        return conn_url
