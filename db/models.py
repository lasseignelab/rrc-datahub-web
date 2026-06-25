# SQLAlchemy ORM models for the RRC DataHub database.

from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class Dataset(Base):
    """One row per GEO BioProject dataset."""

    __tablename__ = "dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bioproject: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return f"Dataset(id={self.id!r}, bioproject={self.bioproject!r})"
