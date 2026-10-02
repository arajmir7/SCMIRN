"""
Web interface routes - HTML page rendering.
Separates web UI from API endpoints.
"""

import json

from flask import Blueprint, render_template, current_app, request, send_from_directory

from app.infrastructure.database.repositories import SQLAlchemyIssueRepository
from app.application.queries.get_issues import GetIssuesQuery, GetIssuesHandler, GetIssueStatisticsHandler
from app.infrastructure.database.database import seed_database

bp = Blueprint('web', __name__)


@bp.app_template_filter('fromjson')
def fromjson_filter(value):
    """Parse JSON string to object for templates."""
    try:
        if value is None:
            return []
        if isinstance(value, (list, dict)):
            return value
        return json.loads(value)
    except Exception:
        return []


def _normalize_issues_for_template(issues):
    """Normalize issue dicts for template compatibility."""
    for issue in issues:
        # Ensure lat/lon are top-level keys
        location = issue.get('location') or {}
        issue['lat'] = issue.get('lat') or location.get('lat')
        issue['lon'] = issue.get('lon') or location.get('lng')

        # Normalize media_files to JSON string of URLs
        media_files = issue.get('media_files') or []
        if isinstance(media_files, str):
            continue
        urls = []
        for media in media_files:
            if isinstance(media, dict):
                url = media.get('url')
            else:
                url = media
            if url:
                urls.append(url)
        issue['media_files'] = json.dumps(urls)
    return issues


def _build_map_issues(issues):
    """Prepare compact issue data for map rendering."""
    map_issues = []
    for issue in issues:
        photos = fromjson_filter(issue.get('media_files'))
        map_issues.append({
            'id': issue.get('id'),
            'lat': issue.get('lat'),
            'lng': issue.get('lon'),
            'title': issue.get('title'),
            'tier': issue.get('priority_tier'),
            'category': issue.get('category'),
            'photo': photos[0] if photos else 'https://via.placeholder.com/100',
            'description': issue.get('description', ''),
            'fund': issue.get('fund_collected', 0),
            'target': issue.get('fund_target', 0)
        })
    return map_issues


@bp.route('/')
def index():
    """
    Homepage - Main entry point.
    Fetches data and renders full HTML template.
    """
    try:
        # Fetch issues for display
        repo = SQLAlchemyIssueRepository()
        
        # Get all issues
        query = GetIssuesQuery(limit=50)
        issues_handler = GetIssuesHandler(repo)
        issues_result = issues_handler.execute(query)

        # Seed database if empty (first run)
        if issues_result.get('count', 0) == 0:
            seed_database()
            issues_result = issues_handler.execute(query)
        
        # Get statistics
        stats_handler = GetIssueStatisticsHandler(repo)
        stats_result = stats_handler.execute()
        
        issues = _normalize_issues_for_template(issues_result.get('issues', []))
        map_issues = _build_map_issues(issues)

        return render_template(
            'index.html',
            issues=issues,
            stats=stats_result.get('statistics', {}),
            map_issues=map_issues
        )
        
    except Exception as e:
        current_app.logger.error(f"Error rendering homepage: {str(e)}")
        # Return basic page on error
        return render_template('index.html', issues=[], stats={}, map_issues=[])


@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')


@bp.route('/documents')
def documents():
    """Document generator page."""
    doc_type = request.args.get('type', 'rti')
    return render_template('documents.html', doc_type=doc_type)


@bp.route('/heatmap')
def heatmap():
    """Full-screen heatmap view."""
    try:
        repo = SQLAlchemyIssueRepository()
        query = GetIssuesQuery(limit=200)
        issues_handler = GetIssuesHandler(repo)
        issues_result = issues_handler.execute(query)

        if issues_result.get('count', 0) == 0:
            seed_database()
            issues_result = issues_handler.execute(query)

        issues = _normalize_issues_for_template(issues_result.get('issues', []))
        map_issues = _build_map_issues(issues)

        return render_template('heatmap.html', map_issues=map_issues)
    except Exception as e:
        current_app.logger.error(f"Error rendering heatmap: {str(e)}")
        return render_template('heatmap.html', map_issues=[])


@bp.route('/offices')
def offices():
    """Office locator page."""
    try:
        from app.infrastructure.database.models import OfficeORM
        offices_list = OfficeORM.query.order_by(OfficeORM.rating.desc()).all()
        return render_template('offices.html', offices=offices_list)
    except Exception as e:
        current_app.logger.error(f"Error rendering offices: {str(e)}")
        return render_template('offices.html', offices=[])


@bp.route('/tracker')
def tracker():
    """Government tracker dashboard page."""
    return render_template('tracker.html')


@bp.route('/analytics')
def analytics():
    """Predictive intelligence dashboard page."""
    return render_template('analytics.html')


@bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@bp.route('/favicon.ico')
def favicon():
    """Avoid 404 spam for favicon in dev."""
    return ("", 204)
