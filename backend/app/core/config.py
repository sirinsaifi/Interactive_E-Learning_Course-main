"""Application configuration.

Loads settings from environment variables (.env) using Pydantic Settings.
All runtime configuration must be read from this module — never hardcode
values inside routers, services, or repositories.
"""
from functools import lru_cache
from typing import List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Query params that managed MySQL providers include in their copy-paste URLs
# but PyMySQL/SQLAlchemy don't understand. Stripped silently during
# normalization so the URL parses cleanly.
_DROP_QUERY_PARAMS = {"sslaccept", "sslmode", "ssl-mode", "ssl_mode"}


def _normalize_mysql_url(url: str) -> str:
    """Convert a user-pasted MySQL URL into a SQLAlchemy/PyMySQL-friendly form."""
    if not url:
        return url
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme == "mysql":
        scheme = "mysql+pymysql"
    query_pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _DROP_QUERY_PARAMS
    ]
    if not any(k.lower() == "charset" for k, _ in query_pairs):
        query_pairs.append(("charset", "utf8mb4"))
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    APP_NAME: str = "LearnSphere API"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ---- Server ----
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ---- Logging ----
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ---- Database (MySQL) ----
    DATABASE_URL_OVERRIDE: str = Field(default="", alias="DATABASE_URL")
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "lms_user"
    DB_PASSWORD: str = "lms_password"
    DB_NAME: str = "lms_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False
    DB_SSL: bool = False

    # ---- Storage ----
    STORAGE_BACKEND: str = "local"
    STORAGE_ROOT: str = "storage"
    VIDEOS_SUBDIR: str = "videos"
    THUMBNAILS_SUBDIR: str = "thumbnails"
    VIDEO_STREAM_CHUNK_SIZE: int = 1024 * 1024
    THUMBNAILS_URL_PREFIX: str = "/static/thumbnails"

    # ---- Cloudinary ----
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "videos"

    # ---- Content sync ----
    AUTO_SEED_ON_STARTUP: bool = True
    AUTO_SEED_PRUNE_MISSING: bool = True

    # ---- Auth (email-based) ----
    # The single instructor email. Anyone who logs in with this address gets
    # the "instructor" role; every other email gets "learner".
    INSTRUCTOR_EMAIL: str = ""
    # Secret used to sign session tokens. Override in production.
    SESSION_SECRET: str = "change-me-in-production-please-use-a-long-random-string"

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return _normalize_mysql_url(self.DATABASE_URL_OVERRIDE)
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
