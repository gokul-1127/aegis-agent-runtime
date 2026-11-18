"""Pytest configuration and fixtures."""
from __future__ import annotations

import pytest

from app.db import SessionLocal, engine, init_db
from app.models.task import Task, Base


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database tables once per test session."""
    init_db()
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a clean database session for each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def clean_database():
    """Clean all task data before each test."""
    session = SessionLocal()
    try:
        session.query(Task).delete()
        session.commit()
    finally:
        session.close()