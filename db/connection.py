# PostgreSQL connection setup using SQLAlchemy and python-dotenv.

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
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


_engine = None
_factory = None


def _get_factory():
    global _engine, _factory
    if _factory is None:
        _engine = create_engine(_db_url())
        _factory = sessionmaker(bind=_engine)
    return _factory


def SessionLocal():
    """Return a new SQLAlchemy session. Caller must close it."""
    return _get_factory()()


def get_engine():
    """Return the SQLAlchemy engine, creating it on first call."""
    _get_factory()
    return _engine
