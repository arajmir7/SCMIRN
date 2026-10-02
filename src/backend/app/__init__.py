"""
SCMIRN Application Factory
Creates and configures the Flask application instance.
"""

import os
import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
import click

from app import config as app_config
from app.config import config_by_name, validate_production_config
from app.extensions import db, migrate, jwt, cache, limiter
from app.infrastructure.database.database import init_database
from app.production_api import is_production_api_allowed


class PrivacyPreservingFlask(Flask):
    """Avoid writing exception messages or stack locals to the default app log."""

    def log_exception(self, exc_info):
        exception_type = exc_info[0].__name__ if exc_info and exc_info[0] else 'UnknownError'
        request_id = request.environ.get('scmirn.request_id', 'unavailable')
        self.logger.error('Unhandled request failure; exception_type=%s request_id=%s', exception_type, request_id)


def create_app(config_name='development'):
    """
    Application factory pattern - creates app with specified configuration.
    
    Args:
        config_name: Configuration environment (development, production, testing)
    
    Returns:
        Configured Flask application instance
    """
    app = PrivacyPreservingFlask(__name__, template_folder=None, static_folder=None)
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    app.config['SCMIRN_ENVIRONMENT'] = config_name
    if config_name == 'production':
        validate_production_config(app.config)
    
    # Ensure data directories exist
    os.makedirs(app_config.DATA_DIR, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    for folder in ['issues', 'verifications', 'documents', 'profiles']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], folder), exist_ok=True)
    
    # Initialize extensions
    _init_extensions(app)
    
    # Register blueprints
    _register_blueprints(app)

    @app.before_request
    def assign_request_id():
        # Generate locally so a caller cannot inject arbitrary values into logs.
        request.environ['scmirn.request_id'] = uuid.uuid4().hex

    @app.after_request
    def attach_request_id(response):
        response.headers['X-Request-ID'] = request.environ.get('scmirn.request_id', 'unavailable')
        return response

    @app.before_request
    def production_readiness_gate():
        """Keep unreviewed legacy and simulated APIs unavailable in production."""
        if app.config.get('MIGRATION_MODE'):
            return jsonify({
                'success': False,
                'error': 'Application traffic is disabled while a database migration is running.',
                'code': 'MIGRATION_MODE',
                'error_code': 'DEPENDENCY_UNAVAILABLE',
                'message': 'Application traffic is disabled while a database migration is running.',
                'request_id': request.environ.get('scmirn.request_id'),
                'safe_details': {},
            }), 503
        if app.config.get('SCMIRN_ENVIRONMENT') != 'production' or request.method == 'OPTIONS':
            return None

        if request.path.startswith(('/api/', '/uploads/')) and not is_production_api_allowed(
            request.url_rule.rule if request.url_rule else None,
            request.method,
        ):
            return jsonify({
                'success': False,
                'error': 'This API is disabled until production readiness review is complete.',
                'code': 'PRODUCTION_ENDPOINT_DISABLED',
                'error_code': 'FEATURE_DISABLED',
                'message': 'This API is disabled until production readiness review is complete.',
                'request_id': request.environ.get('scmirn.request_id'),
                'safe_details': {},
            }), 503
        if request.path.startswith('/api/v1/staff/') and not app.config.get('STAFF_AUTH_ENABLED'):
            return jsonify({
                'success': False,
                'error': 'Staff identity endpoints are disabled until their deployment secrets are configured.',
                'code': 'STAFF_AUTH_DISABLED',
                'error_code': 'FEATURE_DISABLED',
                'message': 'Staff identity endpoints are disabled until their deployment secrets are configured.',
                'request_id': request.environ.get('scmirn.request_id'),
                'safe_details': {},
            }), 503
        return None
    
    # Initialize database
    init_database(app)
    
    # Configure CORS
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    if isinstance(cors_origins, str) and cors_origins != '*':
        cors_origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })
    
    # Register error handlers
    _register_error_handlers(app)

    @app.cli.command('seed-routing-registry')
    def seed_routing_registry_command():
        """Insert the reviewed, source-gated routing registry candidate."""
        from app.source_routing.registry_seed import seed_routing_registry
        seed_routing_registry()
        click.echo('Routing registry seed completed; existing versions were not overwritten.')

    @app.cli.command('purge-route-decisions')
    @click.option('--dry-run', is_flag=True, help='Count expired route decisions without deleting them.')
    def purge_route_decisions_command(dry_run):
        """Purge route decision metadata past its retention deadline."""
        import json
        from app.source_routing.retention import purge_expired_route_decisions
        result = purge_expired_route_decisions(dry_run=dry_run)
        click.echo(json.dumps(result, sort_keys=True))

    @app.cli.command('verify-route-audit-chain')
    def verify_route_audit_chain_command():
        """Verify the metadata-only route audit chain without exposing event data."""
        import json
        from app.source_routing.audit_chain import verify_chain
        result = verify_chain()
        click.echo(json.dumps(result, sort_keys=True))
        if not result['valid']:
            raise click.exceptions.Exit(1)

    @app.cli.command('create-staff-tenant')
    @click.option('--slug', prompt=True, help='Stable lowercase tenant slug.')
    @click.option('--name', prompt='Tenant display name', help='Organization name shown in staff tools.')
    def create_staff_tenant_command(slug, name):
        """Create a staff tenant through the explicitly run operator CLI."""
        import re
        import uuid
        from app.extensions import db
        from app.staff_auth.models import Tenant
        from app.staff_auth.security import set_tenant_scope
        slug = slug.strip().lower()
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,78}[a-z0-9])?', slug):
            raise click.ClickException('Tenant slug must contain lowercase letters, numbers, and internal hyphens only.')
        if Tenant.query.filter_by(slug=slug).first():
            raise click.ClickException('That tenant slug already exists.')
        tenant = Tenant(id=str(uuid.uuid4()), slug=slug, display_name=name.strip())
        set_tenant_scope(tenant.id)
        db.session.add(tenant)
        db.session.commit()
        click.echo(f'Created staff tenant {tenant.slug} ({tenant.id}).')

    @app.cli.command('create-staff-user')
    @click.option('--tenant', 'tenant_slug', prompt=True, help='Existing tenant slug.')
    @click.option('--email', prompt=True, help='Staff email address.')
    @click.option('--name', 'display_name', prompt='Staff display name')
    @click.option('--role', type=click.Choice(['TENANT_ADMIN', 'CASE_OFFICER', 'SOURCE_REVIEWER', 'AUDITOR']), prompt=True)
    def create_staff_user_command(tenant_slug, email, display_name, role):
        """Provision one staff identity and a one-time MFA enrollment URI."""
        from datetime import datetime, timedelta, timezone
        from app.extensions import db
        from app.staff_auth.models import StaffMfaFactor, StaffRoleGrant, StaffUser, Tenant
        from app.staff_auth.security import (
            encrypt_totp_secret, hash_password, new_totp_secret,
            password_meets_policy, provisioning_uri, set_tenant_scope,
        )
        tenant = Tenant.query.filter_by(slug=tenant_slug.strip().lower(), active=True).first()
        if not tenant:
            raise click.ClickException('Active tenant was not found.')
        email = email.strip().lower()
        if len(email) > 254 or '@' not in email or email.startswith('@') or email.endswith('@'):
            raise click.ClickException('Enter a valid email address.')
        set_tenant_scope(tenant.id)
        if StaffUser.query.filter_by(tenant_id=tenant.id, email=email).first():
            raise click.ClickException('That email already exists in this tenant.')
        password = click.prompt('Initial password (14+ characters with a letter and number)', hide_input=True, confirmation_prompt=True)
        if not password_meets_policy(password):
            raise click.ClickException('Password does not meet the minimum length and character requirements.')
        user = StaffUser(tenant_id=tenant.id, email=email, display_name=display_name.strip(), password_hash=hash_password(password))
        db.session.add(user)
        db.session.flush()
        db.session.add(StaffRoleGrant(tenant_id=tenant.id, user_id=user.id, role=role))
        secret = new_totp_secret()
        enrollment_token = __import__('secrets').token_urlsafe(32)
        db.session.add(StaffMfaFactor(
            tenant_id=tenant.id, user_id=user.id, secret_ciphertext=encrypt_totp_secret(secret),
            active=False,
            enrollment_token_hash=__import__('hashlib').sha256(enrollment_token.encode('utf-8')).hexdigest(),
            enrollment_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ))
        db.session.commit()
        click.echo('Staff account created. Deliver these enrollment values through an approved secure channel; they are shown once.')
        click.echo(f'Tenant slug: {tenant.slug}')
        click.echo(f'Enrollment token: {enrollment_token}')
        click.echo(f'TOTP provisioning URI: {provisioning_uri(secret, email, tenant.slug)}')

    @app.cli.command('reset-staff-password')
    @click.option('--tenant', 'tenant_slug', prompt=True)
    @click.option('--email', prompt=True)
    def reset_staff_password_command(tenant_slug, email):
        """Reset a staff password and revoke all of that account's sessions."""
        from datetime import datetime, timezone
        from app.extensions import db
        from app.staff_auth.models import StaffAuditEvent, StaffSession, StaffUser, Tenant
        from app.staff_auth.security import hash_password, password_meets_policy, set_session_management_scope, set_tenant_scope
        tenant = Tenant.query.filter_by(slug=tenant_slug.strip().lower(), active=True).first()
        if not tenant:
            raise click.ClickException('Active tenant was not found.')
        set_tenant_scope(tenant.id)
        user = StaffUser.query.filter_by(tenant_id=tenant.id, email=email.strip().lower()).first()
        if not user:
            raise click.ClickException('Staff account was not found.')
        password = click.prompt('New password (14+ characters with a letter and number)', hide_input=True, confirmation_prompt=True)
        if not password_meets_policy(password):
            raise click.ClickException('Password does not meet the minimum length and character requirements.')
        now = datetime.now(timezone.utc)
        user.password_hash = hash_password(password)
        user.password_changed_at = now
        user.failed_login_count = 0
        user.locked_until = None
        set_session_management_scope(user.id)
        for session_row in StaffSession.query.filter_by(tenant_id=tenant.id, user_id=user.id, revoked_at=None).all():
            session_row.revoked_at = now
        db.session.add(StaffAuditEvent(
            tenant_id=tenant.id, actor_id=None, action='STAFF_PASSWORD_RESET',
            object_type='staff_user', object_id=user.id, request_id='operator-cli',
        ))
        db.session.commit()
        click.echo('Password updated and existing staff sessions revoked.')

    @app.cli.command('disable-staff-user')
    @click.option('--tenant', 'tenant_slug', prompt=True)
    @click.option('--email', prompt=True)
    def disable_staff_user_command(tenant_slug, email):
        """Disable a staff account and revoke its active sessions."""
        from datetime import datetime, timezone
        from app.extensions import db
        from app.staff_auth.models import StaffAuditEvent, StaffSession, StaffUser, Tenant
        from app.staff_auth.security import set_session_management_scope, set_tenant_scope
        tenant = Tenant.query.filter_by(slug=tenant_slug.strip().lower(), active=True).first()
        if not tenant:
            raise click.ClickException('Active tenant was not found.')
        set_tenant_scope(tenant.id)
        user = StaffUser.query.filter_by(tenant_id=tenant.id, email=email.strip().lower()).first()
        if not user:
            raise click.ClickException('Staff account was not found.')
        now = datetime.now(timezone.utc)
        user.active = False
        set_session_management_scope(user.id)
        for session_row in StaffSession.query.filter_by(tenant_id=tenant.id, user_id=user.id, revoked_at=None).all():
            session_row.revoked_at = now
        db.session.add(StaffAuditEvent(
            tenant_id=tenant.id, actor_id=None, action='STAFF_USER_DISABLED',
            object_type='staff_user', object_id=user.id, request_id='operator-cli',
        ))
        db.session.commit()
        click.echo('Staff account disabled and existing sessions revoked.')
    
    # Store config name for reference
    app.config_name = config_name
    
    return app


def _init_extensions(app):
    """Initialize Flask extensions with app context."""
    db.init_app(app)
    migration_dir = os.path.join(app.root_path, 'infrastructure', 'database', 'migrations')
    migrate.init_app(app, db, directory=migration_dir)
    jwt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)


def _register_blueprints(app):
    """Register Flask blueprints (route modules)."""
    from app.api.v1.routes import api_bp
    from app.api.v1.issues import bp as issues_bp
    from app.api.v1.ai import bp as ai_bp
    from app.api.v1.documents import bp as documents_bp
    from app.api.v1.heatmap import bp as heatmap_bp
    from app.api.v1.iot import bp as iot_bp
    from app.api.v1.blockchain import bp as blockchain_bp
    from app.api.v1.ai_v1 import bp as ai_v1_bp
    from app.api.v1.gamification import bp as gamification_bp
    from app.api.v1.resilience import bp as resilience_bp
    from app.api.v1.twin import bp as twin_bp
    from app.api.v1.city_brain import bp as city_brain_bp
    from app.api.v1.enterprise import bp as enterprise_bp
    from app.api.v1.scmirn import bp as scmirn_bp
    from app.api.v1.offices import bp as offices_bp
    from app.api.uploads import bp as uploads_bp
    from app.source_routing.api import bp as source_routing_bp
    
    # Public pages are owned by src/frontend; Flask only registers APIs here.
    # The retired Jinja implementation is kept under docs/legacy for reference.
    # API routes (RESTful, JSON responses)
    app.register_blueprint(api_bp)
    app.register_blueprint(issues_bp, url_prefix='/api')
    app.register_blueprint(ai_bp, url_prefix='/api')
    app.register_blueprint(documents_bp, url_prefix='/api')
    app.register_blueprint(heatmap_bp)
    app.register_blueprint(iot_bp)
    app.register_blueprint(blockchain_bp)
    app.register_blueprint(ai_v1_bp)
    app.register_blueprint(gamification_bp)
    app.register_blueprint(resilience_bp)
    app.register_blueprint(twin_bp)
    app.register_blueprint(city_brain_bp)
    app.register_blueprint(enterprise_bp)
    app.register_blueprint(scmirn_bp)
    app.register_blueprint(offices_bp, url_prefix='/api')
    app.register_blueprint(uploads_bp)
    app.register_blueprint(source_routing_bp, url_prefix='/api/v1')
    from app.staff_auth.api import bp as staff_auth_bp
    app.register_blueprint(staff_auth_bp, url_prefix='/api/v1/staff')


def _register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'error_code': 'NOT_FOUND',
            'message': 'Resource not found',
            'request_id': request.environ.get('scmirn.request_id'),
            'safe_details': {},
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'message': 'Internal server error',
            'request_id': request.environ.get('scmirn.request_id'),
            'safe_details': {},
        }), 500
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {
            'success': False, 
            'error': 'Rate limit exceeded. Please slow down.',
            'error_code': 'RATE_LIMITED',
            'message': 'Rate limit exceeded. Please slow down.',
            'request_id': request.environ.get('scmirn.request_id'),
            'safe_details': {},
        }, 429


# Import at bottom to avoid circular imports
from flask import jsonify
