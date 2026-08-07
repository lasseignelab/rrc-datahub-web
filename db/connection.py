# PostgreSQL connection setup using SQLAlchemy and python-dotenv.

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

load_dotenv()


def _db_url() -> str:
    """Build the SQLAlchemy connection URL from environment variables."""
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


_engine: Engine | None = None
_factory = None


def _is_debug() -> bool:
    """Return True when DEBUG env var is set to a truthy value."""
    return os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


def get_engine() -> Engine:
    """Return the SQLAlchemy engine, creating it on first call."""
    global _engine, _factory
    engine = _engine
    if engine is None:
        engine = create_engine(_db_url(), echo=_is_debug())
        _engine = engine
        _factory = sessionmaker(bind=engine)
    return engine


def _get_factory():
    global _factory
    factory = _factory
    if factory is None:
        factory = sessionmaker(bind=get_engine())
        _factory = factory
    return factory


def SessionLocal():
    """Return a new SQLAlchemy session. Caller must close it."""
    return _get_factory()()
