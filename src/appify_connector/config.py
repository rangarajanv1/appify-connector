from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    appify_login_url: str = "https://login.appify.com"
    appify_gateway_auth: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_ttl_seconds: int = 12 * 60 * 60

    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 23 * 60 * 60

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    cors_allow_origins: Annotated[list[str], NoDecode] = []

    path_prefix: str = ""

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
