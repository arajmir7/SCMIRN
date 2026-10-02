"""
AI Assistant API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import db, limiter
from app.core.services.ai_engine import ai_engine
from app.infrastructure.database.models import ChatLogORM

bp = Blueprint('api_ai', __name__)


class ChatMessageSchema(Schema):
    """Validation schema for chat messages."""
    message = fields.Str(
        required=True, 
        validate=validate.Length(min=2, max=1000)
    )
    location = fields.Str(allow_none=True)
    session_id = fields.Str(load_default='default')


class RightsAnalyzeSchema(Schema):
    """Validation schema for rights analysis."""
    query = fields.Str(required=True, validate=validate.Length(min=3, max=2000))


@bp.route('/ai-assistant', methods=['POST'])
@limiter.limit("30 per minute")
def ai_assistant():
    """
    POST /api/ai-assistant - Main AI chat endpoint.
    
    Processes natural language queries and returns structured civic assistance.
    """
    try:
        schema = ChatMessageSchema()
        data = schema.load(request.get_json() or {})
        
        # Process through AI engine
        result = ai_engine.process(
            text=data['message'],
            user_location=data.get('location'),
            session_id=data.get('session_id')
        )
        
        # Log conversation (async in production)
        log = ChatLogORM(
            session_id=data.get('session_id', 'default'),
            message=data['message'],
            response=result.response[:500],  # Truncate for storage
            intent=result.intent,
            confidence=result.confidence
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'intent': result.intent,
            'response': result.response,
            'confidence': result.confidence,
            'action': result.action,
            'document_type': result.document_type,
            'related_laws': result.related_laws,
            'metadata': result.metadata
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"AI processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'AI processing failed. Please try again.'
        }), 500


@bp.route('/ai-suggestions', methods=['GET'])
@limiter.limit("60 per minute")
def get_suggestions():
    """GET /api/ai-suggestions - Get suggested queries for empty state."""
    suggestions = [
        {'text': 'How do I file an RTI application?', 'intent': 'rti', 'icon': 'file-alt'},
        {'text': 'Police refused to file my FIR', 'intent': 'fir', 'icon': 'exclamation-triangle'},
        {'text': 'My scholarship is delayed', 'intent': 'scholarship', 'icon': 'graduation-cap'},
        {'text': 'Find my nearest police station', 'intent': 'office_finder', 'icon': 'map-marker-alt'},
        {'text': 'What are my consumer rights?', 'intent': 'consumer', 'icon': 'shopping-cart'},
        {'text': 'Wrong electricity bill', 'intent': 'electricity', 'icon': 'bolt'},
        {'text': 'Landlord threatening eviction', 'intent': 'rent', 'icon': 'home'},
        {'text': 'Ration card blocked', 'intent': 'ration', 'icon': 'utensils'}
    ]
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    }), 200


@bp.route('/ai-feedback', methods=['POST'])
@limiter.limit("20 per minute")
def submit_feedback():
    """POST /api/ai-feedback - Submit feedback on AI response."""
    try:
        data = request.get_json() or {}
        
        # Store feedback (implementation depends on requirements)
        current_app.logger.info(f"AI Feedback: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Feedback recorded. Thank you!'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error recording feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to record feedback'
        }), 500


@bp.route('/rights/analyze', methods=['POST'])
@limiter.limit("30 per minute")
def analyze_rights():
    """POST /api/rights/analyze - Analyze legal rights for a civic query."""
    try:
        schema = RightsAnalyzeSchema()
        data = schema.load(request.get_json() or {})
        result = ai_engine.analyze_rights(data['query'])
        return jsonify({
            'success': True,
            'analysis': result
        }), 200
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.messages
        }), 400
    except Exception as e:
        current_app.logger.error(f"Rights analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Rights analysis failed. Please try again.'
        }), 500
