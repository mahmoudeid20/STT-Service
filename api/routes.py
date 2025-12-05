"""
API Routes for STT Service
Additional API endpoints
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages"""
    languages = [
        {'code': 'en-US', 'name': 'English (US)'},
        {'code': 'en-GB', 'name': 'English (UK)'},
        {'code': 'es-ES', 'name': 'Spanish (Spain)'},
        {'code': 'es-MX', 'name': 'Spanish (Mexico)'},
        {'code': 'fr-FR', 'name': 'French'},
        {'code': 'de-DE', 'name': 'German'},
        {'code': 'it-IT', 'name': 'Italian'},
        {'code': 'pt-BR', 'name': 'Portuguese (Brazil)'},
        {'code': 'ja-JP', 'name': 'Japanese'},
        {'code': 'ko-KR', 'name': 'Korean'},
        {'code': 'zh-CN', 'name': 'Chinese (Simplified)'},
        {'code': 'ar-SA', 'name': 'Arabic'},
        {'code': 'ru-RU', 'name': 'Russian'},
        {'code': 'hi-IN', 'name': 'Hindi'}
    ]
    return jsonify({'languages': languages}), 200

@api_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported audio formats"""
    formats = [
        {'extension': '.wav', 'mime_type': 'audio/wav', 'description': 'WAV Audio'},
        {'extension': '.mp3', 'mime_type': 'audio/mpeg', 'description': 'MP3 Audio'},
        {'extension': '.flac', 'mime_type': 'audio/flac', 'description': 'FLAC Audio'},
        {'extension': '.ogg', 'mime_type': 'audio/ogg', 'description': 'OGG Audio'},
        {'extension': '.m4a', 'mime_type': 'audio/m4a', 'description': 'M4A Audio'}
    ]
    return jsonify({'formats': formats}), 200

@api_bp.route('/validate', methods=['POST'])
def validate_audio():
    """Validate audio file before transcription"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Check file extension
        allowed_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
        file_ext = '.' + audio_file.filename.rsplit('.', 1)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'valid': False,
                'error': f'Unsupported format. Allowed: {", ".join(allowed_extensions)}'
            }), 400
        
        # Check file size
        audio_file.seek(0, 2)
        file_size = audio_file.tell()
        audio_file.seek(0)
        
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return jsonify({
                'valid': False,
                'error': f'File too large. Max size: {max_size / (1024*1024)}MB'
            }), 400
        
        return jsonify({
            'valid': True,
            'file_size': file_size,
            'format': file_ext,
            'estimated_processing_time': file_size / 100000  # Rough estimate
        }), 200
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create new audio session"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_name = data.get('session_name')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Create session in database (assuming db is imported)
        from app import db
        session = db.create_session(user_id, session_name)
        
        return jsonify({
            'session_id': session.id,
            'session_name': session.session_name,
            'started_at': session.started_at.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """End audio session"""
    try:
        from app import db
        from datetime import datetime
        
        success = db.update_session(session_id, ended_at=datetime.utcnow())
        
        if success:
            return jsonify({'message': 'Session ended successfully'}), 200
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/export/<transcription_id>', methods=['GET'])
def export_transcription(transcription_id):
    """Export transcription in different formats"""
    try:
        from app import db
        
        format_type = request.args.get('format', 'json')
        transcription = db.get_transcription(transcription_id)
        
        if not transcription:
            return jsonify({'error': 'Transcription not found'}), 404
        
        if format_type == 'json':
            return jsonify(transcription.to_dict()), 200
        
        elif format_type == 'txt':
            from flask import Response
            return Response(
                transcription.transcription_text,
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename=transcription_{transcription_id}.txt'}
            )
        
        elif format_type == 'srt':
            # TODO: Implement SRT subtitle format
            return jsonify({'error': 'SRT format not yet implemented'}), 501
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/search', methods=['GET'])
def search_transcriptions():
    """Search transcriptions by text"""
    try:
        from app import db
        
        query = request.args.get('q', '')
        user_id = request.args.get('user_id')
        
        if not query or not user_id:
            return jsonify({'error': 'query and user_id are required'}), 400
        
        # Search in database (simplified)
        results = db.search_transcriptions(user_id, query)
        
        return jsonify({
            'query': query,
            'results': [r.to_dict() for r in results]
        }), 200
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500