"""Database connection helpers."""

from app.extensions import db


def get_connection():
    return db
