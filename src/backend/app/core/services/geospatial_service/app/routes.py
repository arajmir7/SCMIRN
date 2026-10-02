from flask import Blueprint, jsonify, request
from .engines.heatmap_engine import generate_issue_heatmap
from app.core_platform.infrastructure.persistence.sqlalchemy.repositories import IssueRepository

geospatial_bp = Blueprint('geospatial', __name__, url_prefix='/api/v1/geo')

@geospatial_bp.route('/heatmap')
def get_heatmap():
    """Get heatmap data for issues"""
    algorithm = request.args.get('algorithm', 'grid')
    category = request.args.get('category')
    
    # Fetch issues from DB
    repo = IssueRepository()
    issues = repo.get_all_active()
    
    if category:
        issues = [i for i in issues if i.get('category') == category]
    
    result = generate_issue_heatmap(issues, algorithm=algorithm)
    return jsonify(result)

@geospatial_bp.route('/hotspots')
def get_hotspots():
    """Get top priority zones"""
    repo = IssueRepository()
    issues = repo.get_all_active()
    
    from .engines.heatmap_engine import get_priority_zones
    hotspots = get_priority_zones(issues)
    
    return jsonify({
        'hotspots': hotspots,
        'total': len(hotspots)
    })
