"""Authentication API placeholder."""

from flask import Blueprint, jsonify


bp = Blueprint('api_auth', __name__)


@bp.route('/auth/health', methods=['GET'])
def auth_health():
    return jsonify({'success': True, 'status': 'ok'})
