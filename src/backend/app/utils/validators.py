"""
Flask Extensions Initialization
"""
import importlib
from typing import Any
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

try:
    _migrate = importlib.import_module("flask_migrate")
    Migrate = _migrate.Migrate
except Exception:
    class Migrate:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

try:
    _jwt = importlib.import_module("flask_jwt_extended")
    JWTManager = _jwt.JWTManager
except Exception:
    class JWTManager:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

migrate = Migrate()
jwt = JWTManager()
