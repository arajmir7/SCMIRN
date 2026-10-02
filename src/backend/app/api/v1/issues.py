"""
Issue API endpoints - RESTful routes for issue management.
"""

from flask import Blueprint, request, jsonify, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import db, limiter
from app.infrastructure.database.repositories import SQLAlchemyIssueRepository
from app.application.commands.report_issue import ReportIssueCommand, ReportIssueHandler
from app.application.queries.get_issues import GetIssuesQuery, GetIssuesHandler, GetIssueStatisticsHandler

# Create blueprint
bp = Blueprint('api_issues', __name__)


# ============ SCHEMAS ============

class CreateIssueSchema(Schema):
    """Validation schema for issue creation."""
    title = fields.Str(required=True, validate=validate.Length(min=10, max=500))
    description = fields.Str(required=True, validate=validate.Length(min=20, max=2000))
    category = fields.Str(required=True, validate=validate.OneOf([
        'road', 'water', 'electricity', 'safety', 'sanitation', 
        'corruption', 'transport', 'environment', 'other'
    ]))
    lat = fields.Float(allow_none=True)
    lon = fields.Float(allow_none=True)
    fund_target = fields.Float(load_default=0.0)


class DonationSchema(Schema):
    """Validation schema for donations."""
    amount = fields.Float(required=True, validate=validate.Range(min=10, max=100000))


# ============ ROUTES ============

@bp.route('/issues', methods=['GET'])
@limiter.limit("100 per minute")
def get_issues():
    """
    GET /api/issues - List issues with filtering.
    
    Query params:
        - tier: critical|high|medium|low
        - status: reported|verified|funded|in_progress|resolved
        - lat, lon, radius: Geo search
        - limit, offset: Pagination
    """
    try:
        # Build query from request args
        query = GetIssuesQuery(
            tier=request.args.get('tier'),
            status=request.args.get('status'),
            nearby_lat=request.args.get('lat', type=float),
            nearby_lon=request.args.get('lon', type=float),
            radius_km=request.args.get('radius', 5.0, type=float),
            limit=request.args.get('limit', 100, type=int),
            offset=request.args.get('offset', 0, type=int)
        )
        
        # Execute query
        repo = SQLAlchemyIssueRepository()
        handler = GetIssuesHandler(repo)
        result = handler.execute(query)

        # Preserve the legacy first-visit demo seed after moving page rendering
        # out of Flask. The seed helper exits immediately once issues exist.
        if result.get('count', 0) == 0 and current_app.config.get('DEMO_MODE', False):
            from app.infrastructure.database.database import seed_database
            seed_database()
            result = handler.execute(query)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching issues: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch issues'
        }), 500


@bp.route('/issues/stats', methods=['GET'])
@limiter.limit("60 per minute")
def get_statistics():
    """GET /api/issues/stats - Get dashboard statistics."""
    try:
        repo = SQLAlchemyIssueRepository()
        handler = GetIssueStatisticsHandler(repo)
        result = handler.execute()
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch statistics'
        }), 500


@bp.route('/issues/<public_id>', methods=['GET'])
@limiter.limit("100 per minute")
def get_issue(public_id):
    """GET /api/issues/<id> - Get single issue details."""
    try:
        repo = SQLAlchemyIssueRepository()
        issue = repo.get_by_public_id(public_id)
        
        if not issue:
            return jsonify({
                'success': False,
                'error': 'Issue not found'
            }), 404
        
        return jsonify({
            'success': True,
            'issue': issue.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching issue: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch issue'
        }), 500


@bp.route('/issues', methods=['POST'])
@limiter.limit("10 per minute")
def create_issue():
    """
    POST /api/issues - Report new civic issue.
    
    Handles multipart/form-data for file uploads + JSON data.
    """
    try:
        # Validate JSON fields
        schema = CreateIssueSchema()
        data = schema.load(request.form.to_dict() or request.get_json() or {})
        
        # Handle file uploads
        media_urls = []
        if 'media' in request.files:
            files = request.files.getlist('media')
            for file in files:
                if file and allowed_file(file.filename):
                    # Save file and get URL
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'issues', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    media_urls.append(f'/uploads/issues/{filename}')
        
        # Build command
        command = ReportIssueCommand(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            lat=data.get('lat'),
            lon=data.get('lon'),
            media_urls=media_urls,
            fund_target=0.0,
            reporter_phone=request.form.get('phone')
        )
        
        # Execute
        repo = SQLAlchemyIssueRepository()
        handler = ReportIssueHandler(repo)
        result = handler.execute(command)
        
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Error creating issue: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create issue'
        }), 500


@bp.route('/report-issue', methods=['POST'])
@limiter.limit("10 per minute")
def report_issue_compat():
    """
    POST /api/report-issue - Compatibility endpoint for legacy UI.
    Mirrors /api/issues but returns simplified response.
    """
    try:
        schema = CreateIssueSchema()
        data = schema.load(request.form.to_dict() or request.get_json() or {})

        media_urls = []
        if 'media' in request.files:
            files = request.files.getlist('media')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'issues', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    media_urls.append(f'/uploads/issues/{filename}')

        command = ReportIssueCommand(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            lat=data.get('lat'),
            lon=data.get('lon'),
            media_urls=media_urls,
            fund_target=0.0,
            reporter_phone=request.form.get('phone')
        )

        repo = SQLAlchemyIssueRepository()
        handler = ReportIssueHandler(repo)
        result = handler.execute(command)

        return jsonify({
            'success': True,
            'priority': result['priority']['tier'],
            'score': result['priority']['score'],
            'message': result['message'],
            'issue_id': result['issue_id']
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error creating issue (compat): {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create issue'
        }), 500


@bp.route('/issues/<public_id>/donate', methods=['POST'])
@limiter.limit("5 per minute")
def donate_to_issue(public_id):
    """Return an unavailable response; no payment provider is configured."""
    return jsonify({
        'success': False,
        'error': 'Payments are unavailable; no funds were collected or recorded.',
        'code': 'PAYMENTS_NOT_CONFIGURED',
    }), 503


@bp.route('/donate', methods=['POST'])
@limiter.limit("5 per minute")
def donate_compat():
    """Compatibility endpoint intentionally disabled until a payment provider exists."""
    return jsonify({
        'success': False,
        'error': 'Payments are unavailable; no funds were collected or recorded.',
        'code': 'PAYMENTS_NOT_CONFIGURED',
    }), 503


@bp.route('/issues/nearby', methods=['GET'])
@limiter.limit("100 per minute")
def get_nearby_issues():
    """GET /api/issues/nearby?lat=xx&lon=yy&radius=5 - Geo search."""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 5.0, type=float)
        
        if not lat or not lon:
            return jsonify({
                'success': False,
                'error': 'lat and lon parameters required'
            }), 400
        
        query = GetIssuesQuery(
            nearby_lat=lat,
            nearby_lon=lon,
            radius_km=radius,
            limit=request.args.get('limit', 50, type=int)
        )
        
        repo = SQLAlchemyIssueRepository()
        handler = GetIssuesHandler(repo)
        result = handler.execute(query)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching nearby issues: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch nearby issues'
        }), 500


@bp.route('/tracker/summary', methods=['GET'])
@limiter.limit("60 per minute")
def tracker_summary():
    """GET /api/tracker/summary - Dashboard-ready case tracker summary."""
    try:
        limit = request.args.get('limit', 25, type=int)
        limit = max(1, min(limit, 100))

        rows = (
            IssueORM.query
            .order_by(IssueORM.created_at.desc())
            .limit(limit)
            .all()
        )

        eta_by_tier = {
            'critical': 3,
            'high': 7,
            'medium': 14,
            'low': 21
        }

        items = []
        open_count = 0
        escalation_due = 0
        eta_values = []
        funded_progress_values = []

        for row in rows:
            status = (row.status or 'reported').lower()
            tier = (row.priority_tier or 'medium').lower()
            eta_days = eta_by_tier.get(tier, 14)

            if status != 'resolved':
                open_count += 1
                if status in {'reported', 'verified'} and eta_days <= 7:
                    escalation_due += 1

            eta_values.append(eta_days)

            target = float(row.fund_target or 0)
            collected = float(row.fund_collected or 0)
            progress = 0.0 if target <= 0 else min((collected / target) * 100.0, 100.0)
            funded_progress_values.append(progress)

            items.append({
                'public_id': row.public_id,
                'title': row.title,
                'status': status,
                'priority_tier': tier,
                'category': row.category,
                'eta_days': eta_days,
                'escalation_ready': status in {'reported', 'verified'} and eta_days <= 7,
                'fund_progress': round(progress, 1),
                'created_at': row.created_at.isoformat() if row.created_at else None
            })

        avg_eta = round(sum(eta_values) / len(eta_values), 1) if eta_values else 0.0
        avg_funded = round(sum(funded_progress_values) / len(funded_progress_values), 1) if funded_progress_values else 0.0

        return jsonify({
            'success': True,
            'kpis': {
                'open_cases': open_count,
                'due_escalations': escalation_due,
                'avg_eta_days': avg_eta,
                'avg_funded_progress': avg_funded
            },
            'items': items
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error building tracker summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to build tracker summary'
        }), 500


@bp.route('/analytics/summary', methods=['GET'])
@limiter.limit("60 per minute")
def analytics_summary():
    """GET /api/analytics/summary - Operational insights for predictive dashboard."""
    try:
        rows = IssueORM.query.all()
        total = len(rows)

        if total == 0:
            return jsonify({
                'success': True,
                'summary': {
                    'total_reports': 0,
                    'critical_share': 0.0,
                    'predicted_sla': 'N/A',
                    'top_bottleneck': 'N/A'
                },
                'category_distribution': {},
                'status_distribution': {}
            }), 200

        category_counts = {}
        status_counts = {}
        unresolved_counts = {}
        critical_count = 0

        for row in rows:
            category = (row.category or 'other').lower()
            status = (row.status or 'reported').lower()
            tier = (row.priority_tier or 'medium').lower()

            category_counts[category] = category_counts.get(category, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

            if status != 'resolved':
                unresolved_counts[category] = unresolved_counts.get(category, 0) + 1

            if tier == 'critical':
                critical_count += 1

        critical_share = round((critical_count / total) * 100.0, 1)
        top_bottleneck = max(unresolved_counts, key=unresolved_counts.get) if unresolved_counts else 'N/A'

        unresolved = sum(unresolved_counts.values())
        if unresolved == 0:
            predicted_sla = '3-5 days'
        elif unresolved < 10:
            predicted_sla = '7-12 days'
        elif unresolved < 25:
            predicted_sla = '12-18 days'
        else:
            predicted_sla = '18+ days'

        return jsonify({
            'success': True,
            'summary': {
                'total_reports': total,
                'critical_share': critical_share,
                'predicted_sla': predicted_sla,
                'top_bottleneck': top_bottleneck
            },
            'category_distribution': category_counts,
            'status_distribution': status_counts
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error building analytics summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to build analytics summary'
        }), 500


# ============ UTILITIES ============

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}


# Import at bottom to avoid circular imports
import os
import time
from werkzeug.utils import secure_filename
from app.infrastructure.database.models import IssueORM
