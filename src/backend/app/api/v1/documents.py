"""
Document generation API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import limiter
from app.infrastructure.database.models import DocumentORM
from app.core.services.ai_engine import ai_engine

bp = Blueprint('api_documents', __name__)


class GenerateDocumentSchema(Schema):
    """Validation schema for document generation."""
    doc_type = fields.Str(
        required=True,
        validate=validate.OneOf([
            'rti', 'fir', 'consumer', 'rent', 'scholarship', 'electricity', 'pension', 'cybercrime'
        ])
    )
    template_data = fields.Dict(required=True)


@bp.route('/documents/<doc_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_document(doc_id):
    """GET /api/documents/<id> - Read metadata for an already stored draft."""
    document = DocumentORM.query.filter_by(public_id=doc_id).first()
    if not document:
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    return jsonify({
        'success': True,
        'data': {
            'id': document.public_id,
            'title': document.title or f'{document.doc_type.upper()} draft',
            'status': document.status,
            'type': document.doc_type.upper(),
            'createdAt': document.created_at.isoformat() if document.created_at else '',
            'fileSize': document.file_size or 0,
        },
    }), 200


@bp.route('/documents/generate', methods=['POST'])
@limiter.limit("20 per minute")
def generate_document():
    """
    POST /api/documents/generate - Generate legal document.
    
    Returns generated document content.
    """
    try:
        schema = GenerateDocumentSchema()
        data = schema.load(request.get_json() or {})
        
        # Generate using AI engine
        content = ai_engine.generate_document(
            doc_type=data['doc_type'],
            data=data['template_data']
        )
        
        return jsonify({
            'success': True,
            'doc_type': data['doc_type'],
            'content': content,
            'generated_at': datetime.utcnow().isoformat(),
            'disclaimer': 'This is a draft. Verify with legal counsel before submission.'
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Document generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate document'
        }), 500


@bp.route('/documents/<doc_id>/download', methods=['GET'])
@limiter.limit("30 per minute")
def download_document(doc_id):
    """GET /api/documents/<id>/download - Download generated PDF."""
    # Implementation would retrieve from storage and return PDF
    # For now, return placeholder
    return jsonify({
        'success': False,
        'error': 'PDF generation service not yet implemented'
    }), 501


# Import at bottom
from datetime import datetime
