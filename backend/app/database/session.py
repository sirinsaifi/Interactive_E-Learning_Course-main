"""Database engine and session management.

Exposes a single `SessionLocal` factory and a FastAPI dependency `get_db`
that yields a SQLAlchemy 2.0 ORM session and guarantees cleanup.
"""
import ssl
from collections.abc import Generator
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Hostnames belonging to managed MySQL providers that require TLS. Used to
# auto-enable SSL even when `DB_SSL` isn't explicitly set in env.
_TLS_HOST_SUFFIXES = (
    ".psdb.cloud",            # PlanetScale
    ".aivencloud.com",        # Aiven
    ".clever-cloud.com",      # Clever Cloud
    ".rds.amazonaws.com",     # AWS RDS
    ".azure.com",             # Azure MySQL flexible server
)


def _needs_tls(url: str) -> bool:
    if settings.DB_SSL:
        return True
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return False
    return any(host.endswith(suffix) for suffix in _TLS_HOST_SUFFIXES)


def _build_connect_args(url: str) -> dict:
    """Add a TLS context to PyMySQL's connect kwargs when required.

    Using an `ssl.SSLContext` is the most portable way: PyMySQL accepts it
    directly, and it picks up the OS trust store (no need to ship CA bundles).
    """
    if not _needs_tls(url):
        return {}
    ctx = ssl.create_default_context()
    return {"ssl": ctx}


def _create_engine() -> Engine:
    url = settings.DATABASE_URL
    try:
        host = urlsplit(url).hostname or "?"
    except ValueError:
        host = "?"
    logger.info("Initializing database engine for host=%s tls=%s", host, _needs_tls(url))
    return create_engine(
        url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        echo=settings.DB_ECHO,
        future=True,
        connect_args=_build_connect_args(url),
    )


engine: Engine = _create_engine()

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
