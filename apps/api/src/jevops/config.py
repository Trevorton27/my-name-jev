from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JEVOPS_DB_")

    host: str = "localhost"
    port: int = 5433
    user: str = "jevops"
    password: str = "jevops"
    name: str = "jevops"
    sslmode: str = ""

    @property
    def _requires_ssl(self) -> bool:
        if self.sslmode:
            return self.sslmode != "disable"
        return self.host != "localhost"

    @property
    def async_url(self) -> str:
        base = f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"{base}?ssl=require" if self._requires_ssl else base

    @property
    def sync_url(self) -> str:
        base = f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"{base}?sslmode=require" if self._requires_ssl else base


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JEVOPS_REDIS_")

    host: str = "localhost"
    port: int = 6379
    password: str = ""
    ssl: bool = False
    db: int = 0

    @property
    def url(self) -> str:
        scheme = "rediss" if self.ssl else "redis"
        auth = f"default:{self.password}@" if self.password else ""
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"


class JevSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JEVOPS_JEV_")

    provider: str = Field(default="mock", description="Provider: mock, typesafe, failure")
    model: str = "jev-latest"
    api_key: str = ""
    timeout: float = 30.0
    max_retries: int = 3


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JEVOPS_SECURITY_")

    api_key_pepper: str = "change-me-in-production"
    cors_origins: list[str] = ["http://localhost:3000"]
    rate_limit_per_minute: int = 60
    max_request_size_bytes: int = 1_048_576  # 1MB
    # POST /v1/demo/reset is disabled unless this is set; callers must send it as X-Demo-Reset-Token
    demo_reset_token: str = ""


class OtelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JEVOPS_OTEL_")

    enabled: bool = False
    endpoint: str = "http://localhost:4317"
    service_name: str = "jevops-api"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JEVOPS_")

    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    log_format: str = "console"  # "console" or "json"

    db: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    jev: JevSettings = JevSettings()
    security: SecuritySettings = SecuritySettings()
    otel: OtelSettings = OtelSettings()


def get_settings() -> Settings:
    return Settings()
