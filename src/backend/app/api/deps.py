"""Dependency helpers for API layer."""

from app.extensions import db


def get_db():
    """Return the SQLAlchemy db instance."""
    return db
