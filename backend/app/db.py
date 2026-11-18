"""Database setup using SQLAlchemy 2.x."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.config import settings


def _make_engine():
    url = settings.database_url
    if url.startswith("sqlite"):
        # SQLite works well for local development
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url)


engine = _make_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db() -> Session:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)