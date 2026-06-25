# PostgreSQL connection setup using SQLAlchemy and python-dotenv.

import os

from dotenv import load_dotenv  # type: ignore[import-untyped]
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


engine = create_engine(_db_url())
SessionLocal = sessionmaker(bind=engine)
