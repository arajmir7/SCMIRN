"""
Application configuration classes.
Implements 12-factor app configuration via environment variables.
"""

import base64
import os
import secrets
from datetime import timedelta
from sqlalchemy.engine import make_url
from urllib.parse import urlsplit


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'infrastructure', 'database', 'instance')
UPLOADS_DIR = os.path.join(BASE_DIR, 'infrastructure', 'uploads')


def _positive_int_env(name, default=None):
    raw = os.getenv(name, '')
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


class Config:
    """Base configuration shared across all environments."""
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY') or os.urandom(32).hex()
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or os.urandom(32).hex()
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_CREATE_DB = True
    AUTO_SEED_ROUTING_REGISTRY = False
    DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'
    STAFF_API_ENABLED = os.getenv(
        'STAFF_API_ENABLED', os.getenv('STAFF_AUTH_ENABLED', 'false')
    ).lower() == 'true'
    # Compatibility alias for existing route guards and downstream deployments.
    STAFF_AUTH_ENABLED = STAFF_API_ENABLED
    SCMIRN_APP_DB_ROLE = os.getenv('SCMIRN_APP_DB_ROLE', 'scmirn_app')
    SCMIRN_MIGRATOR_DB_ROLE = os.getenv('SCMIRN_MIGRATOR_DB_ROLE', 'scmirn_migrator')
    STAFF_MFA_ENCRYPTION_KEY = os.getenv('STAFF_MFA_ENCRYPTION_KEY', '')
    STAFF_SESSION_IDLE_MINUTES = 30
    STAFF_SESSION_ABSOLUTE_HOURS = 12

    # Evidence remains unavailable unless a deployment explicitly configures
    # the store, scanner, and authority retention policy.
    EVIDENCE_VAULT_ENABLED = os.getenv('EVIDENCE_VAULT_ENABLED', 'false').lower() == 'true'
    EVIDENCE_STORAGE_BACKEND = os.getenv('EVIDENCE_STORAGE_BACKEND', 'local')
    EVIDENCE_LOCAL_ROOT = os.getenv(
        'EVIDENCE_LOCAL_ROOT', os.path.join(DATA_DIR, 'private-evidence')
    )
    EVIDENCE_S3_BUCKET = os.getenv('EVIDENCE_S3_BUCKET', '')
    EVIDENCE_S3_REGION = os.getenv('EVIDENCE_S3_REGION', '')
    EVIDENCE_S3_ENDPOINT_URL = os.getenv('EVIDENCE_S3_ENDPOINT_URL', '')
    EVIDENCE_S3_KMS_KEY_ID = os.getenv('EVIDENCE_S3_KMS_KEY_ID', '')
    EVIDENCE_CLAMAV_UNIX_SOCKET = os.getenv('EVIDENCE_CLAMAV_UNIX_SOCKET', '')
    EVIDENCE_CLAMAV_HOST = os.getenv('EVIDENCE_CLAMAV_HOST', '')
    EVIDENCE_CLAMAV_PORT = _positive_int_env('EVIDENCE_CLAMAV_PORT', 3310)
    EVIDENCE_CLAMAV_TIMEOUT_SECONDS = _positive_int_env('EVIDENCE_CLAMAV_TIMEOUT_SECONDS', 5)
    EVIDENCE_MAX_BYTES = _positive_int_env('EVIDENCE_MAX_BYTES', 15 * 1024 * 1024)
    EVIDENCE_RETRIEVAL_URL_TTL_SECONDS = _positive_int_env('EVIDENCE_RETRIEVAL_URL_TTL_SECONDS', 60)
    EVIDENCE_DEFAULT_RETENTION_DAYS = _positive_int_env('EVIDENCE_DEFAULT_RETENTION_DAYS')
    EVIDENCE_RETENTION_POLICY_ID = os.getenv('EVIDENCE_RETENTION_POLICY_ID', '')
    
    # File uploads
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    UPLOAD_FOLDER = UPLOADS_DIR
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'pdf'}
    
    # Caching
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate limiting
    RATELIMIT_STORAGE_URI = 'memory://'
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    
    # AI Engine
    AI_CONFIDENCE_THRESHOLD = 0.7

    # Outbound email delivery (enterprise briefings)
    EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'auto')  # auto | sendgrid | ses | none
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', '')
    SES_FROM_EMAIL = os.getenv('SES_FROM_EMAIL', '')
    AWS_REGION = os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    ENV = 'development'
    AUTO_SEED_ROUTING_REGISTRY = True
    DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    EVIDENCE_STORAGE_BACKEND = os.getenv('EVIDENCE_STORAGE_BACKEND', 'local')
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(DATA_DIR, 'scmirn_dev.db')}"
    )
    
    # Detailed error pages
    PROPAGATE_EXCEPTIONS = True


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    ENV = 'production'
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    AUTO_CREATE_DB = False
    AUTO_SEED_ROUTING_REGISTRY = False
    DEMO_MODE = False
    STAFF_API_ENABLED = os.getenv(
        'STAFF_API_ENABLED', os.getenv('STAFF_AUTH_ENABLED', 'false')
    ).lower() == 'true'
    STAFF_AUTH_ENABLED = STAFF_API_ENABLED
    EVIDENCE_VAULT_ENABLED = os.getenv('EVIDENCE_VAULT_ENABLED', 'false').lower() == 'true'
    EVIDENCE_STORAGE_BACKEND = os.getenv('EVIDENCE_STORAGE_BACKEND', 's3')
    SCMIRN_APP_DB_ROLE = os.getenv('SCMIRN_APP_DB_ROLE', 'scmirn_app')
    SCMIRN_MIGRATOR_DB_ROLE = os.getenv('SCMIRN_MIGRATOR_DB_ROLE', 'scmirn_migrator')
    MIGRATION_MODE = os.getenv('SCMIRN_MIGRATION_MODE', 'false').lower() == 'true'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # Required in prod
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800
    }
    
    # Production caching with Redis
    CACHE_TYPE = 'RedisCache'
    REDIS_URL = os.getenv('REDIS_URL')
    CACHE_REDIS_URL = REDIS_URL
    
    # Production rate limiting
    RATELIMIT_STORAGE_URI = REDIS_URL
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    DEBUG = True
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    EMAIL_PROVIDER = 'none'
    AUTO_SEED_ROUTING_REGISTRY = True
    DEMO_MODE = False
    STAFF_AUTH_ENABLED = True
    STAFF_API_ENABLED = True
    STAFF_MFA_ENCRYPTION_KEY = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('ascii')
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def validate_production_config(config):
    """Reject development secrets, local origins and non-PostgreSQL storage."""
    errors = []
    for name in ('SECRET_KEY', 'JWT_SECRET_KEY'):
        value = config.get(name)
        if not isinstance(value, str) or len(value) < 32:
            errors.append(f'{name} must be configured with at least 32 characters')
    if config.get('STAFF_API_ENABLED', config.get('STAFF_AUTH_ENABLED', False)):
        key = config.get('STAFF_MFA_ENCRYPTION_KEY', '')
        try:
            import base64
            decoded_key = base64.b64decode(
                key + '=' * (-len(key) % 4), altchars=b'-_', validate=True
            ) if isinstance(key, str) else b''
        except Exception:
            decoded_key = b''
        if len(decoded_key) != 32:
            errors.append('STAFF_MFA_ENCRYPTION_KEY must be URL-safe base64 for exactly 32 key bytes when staff APIs are enabled')
    if config.get('EVIDENCE_VAULT_ENABLED', False):
        if config.get('EVIDENCE_STORAGE_BACKEND') != 's3':
            errors.append('Evidence vault requires the configured private S3-compatible backend in production')
        for name in ('EVIDENCE_S3_BUCKET', 'EVIDENCE_S3_REGION', 'EVIDENCE_S3_KMS_KEY_ID'):
            if not isinstance(config.get(name), str) or not config[name].strip():
                errors.append(f'{name} must be configured when the evidence vault is enabled')
        endpoint = config.get('EVIDENCE_S3_ENDPOINT_URL', '')
        if endpoint and not endpoint.startswith('https://'):
            errors.append('EVIDENCE_S3_ENDPOINT_URL must use HTTPS in production')
        scanner_socket = config.get('EVIDENCE_CLAMAV_UNIX_SOCKET', '')
        if not isinstance(scanner_socket, str) or not os.path.isabs(scanner_socket):
            errors.append('EVIDENCE_CLAMAV_UNIX_SOCKET must name the configured private scanner socket')
        if not isinstance(config.get('EVIDENCE_DEFAULT_RETENTION_DAYS'), int) or config['EVIDENCE_DEFAULT_RETENTION_DAYS'] <= 0:
            errors.append('EVIDENCE_DEFAULT_RETENTION_DAYS must come from the approved authority retention policy')
        if not isinstance(config.get('EVIDENCE_RETENTION_POLICY_ID'), str) or not config['EVIDENCE_RETENTION_POLICY_ID'].strip():
            errors.append('EVIDENCE_RETENTION_POLICY_ID must identify an approved authority policy')
        if not isinstance(config.get('EVIDENCE_MAX_BYTES'), int) or not 1 <= config['EVIDENCE_MAX_BYTES'] <= 25 * 1024 * 1024:
            errors.append('EVIDENCE_MAX_BYTES must be between 1 and 26214400')
        if not isinstance(config.get('EVIDENCE_RETRIEVAL_URL_TTL_SECONDS'), int) or not 1 <= config['EVIDENCE_RETRIEVAL_URL_TTL_SECONDS'] <= 300:
            errors.append('EVIDENCE_RETRIEVAL_URL_TTL_SECONDS must be between 1 and 300')
    database_url = config.get('SQLALCHEMY_DATABASE_URI')
    if not isinstance(database_url, str) or not database_url.startswith(('postgresql+psycopg://',)):
        errors.append('DATABASE_URL must use the installed PostgreSQL psycopg 3 driver in production')
    else:
        try:
            database_settings = make_url(database_url)
            database_options = database_settings.query
            migration_mode = config.get('MIGRATION_MODE', False)
            expected_db_role = config.get(
                'SCMIRN_MIGRATOR_DB_ROLE' if migration_mode else 'SCMIRN_APP_DB_ROLE',
                'scmirn_migrator' if migration_mode else 'scmirn_app',
            )
            if database_settings.username != expected_db_role:
                required_identity = 'migration' if migration_mode else 'application'
                errors.append(f'DATABASE_URL must use the dedicated {required_identity} PostgreSQL role')
            if database_options.get('sslmode') != 'verify-full':
                errors.append('DATABASE_URL must require PostgreSQL TLS with sslmode=verify-full')
            if database_options.get('sslrootcert') != '/run/postgres-ca.crt':
                errors.append('DATABASE_URL must verify PostgreSQL using the mounted CA certificate')
        except Exception:
            errors.append('DATABASE_URL must be a valid PostgreSQL connection URL')
    redis_url = config.get('REDIS_URL') or config.get('CACHE_REDIS_URL') or config.get('RATELIMIT_STORAGE_URI')
    if not isinstance(redis_url, str) or not redis_url.startswith('rediss://'):
        errors.append('REDIS_URL must configure TLS-protected Redis for production cache and rate limits')
    else:
        try:
            redis_options = make_url(redis_url).query
            if redis_options.get('ssl_ca_certs') != '/run/redis-ca.crt':
                errors.append('REDIS_URL must use the mounted Redis CA certificate')
            if redis_options.get('ssl_cert_reqs') != 'required':
                errors.append('REDIS_URL must require Redis certificate verification')
            if str(redis_options.get('ssl_check_hostname', '')).lower() not in {'true', 'yes', '1'}:
                errors.append('REDIS_URL must enable Redis hostname verification')
        except Exception:
            errors.append('REDIS_URL must be a valid Redis TLS connection URL')
    origins = config.get('CORS_ORIGINS', [])
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(',') if origin.strip()]
    if not isinstance(origins, (list, tuple)) or not origins:
        errors.append('CORS_ORIGINS must contain at least one HTTPS origin')
    elif any(not _is_production_origin(origin) for origin in origins):
        errors.append('CORS_ORIGINS may contain only HTTPS origins in production')
    if errors:
        raise RuntimeError('Production configuration rejected: ' + '; '.join(errors))


def _is_production_origin(origin):
    if not isinstance(origin, str):
        return False
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return False
    hostname = (parsed.hostname or '').lower()
    return bool(
        parsed.scheme == 'https'
        and hostname
        and not parsed.username
        and not parsed.password
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and '*' not in hostname
        and hostname != 'localhost'
        and not hostname.endswith('.example')
        and 'example.' not in hostname
    )
