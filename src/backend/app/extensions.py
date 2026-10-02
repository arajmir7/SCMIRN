"""
Flask extensions initialization.
Extensions are created here but bound to app in factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_limiter import Limiter

# Database ORM
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# JWT authentication
jwt = JWTManager()

# Caching
cache = Cache()

# Rate limiting
limiter = Limiter(
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

# Import for key_func
from flask import request
