"""
REST API Routes
Main entry point for all API endpoints.
"""

from flask import Blueprint, current_app
from redis import Redis
from sqlalchemy import text

from app.extensions import db, limiter

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/health', methods=['GET'])
@limiter.exempt
def health_check():
    """Process liveness probe; it does not depend on external services."""
    return {'status': 'healthy'}, 200


@api_bp.route('/ready', methods=['GET'])
@limiter.exempt
def readiness_check():
    """Report readiness only when required production stores answer probes."""
    try:
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
    except Exception:
        current_app.logger.warning('Readiness probe failed: database unavailable')
        return {'status': 'not_ready'}, 503

    if current_app.config.get('CACHE_TYPE') == 'RedisCache':
        redis_client = None
        try:
            redis_url = current_app.config.get('REDIS_URL')
            if not redis_url:
                raise RuntimeError('Redis is required but REDIS_URL is not configured')
            redis_client = Redis.from_url(
                redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                ssl_cert_reqs='required',
                ssl_check_hostname=True,
            )
            redis_client.ping()
        except Exception:
            current_app.logger.warning('Readiness probe failed: Redis unavailable')
            return {'status': 'not_ready'}, 503
        finally:
            if redis_client is not None:
                redis_client.close()

    return {'status': 'ready'}, 200
