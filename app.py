"""
STT Service Main Application
Member 3 - Speech-to-Text Service
"""
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from datetime import datetime
import json
import tempfile
import wave
import struct

from kafka_integration import KafkaHandler
from audio_processor import AudioProcessor
from database.connection import DatabaseConnection
from database.models import Transcription, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    S3_BUCKET = os.getenv('S3_BUCKET', 'voice-assistant-bucket')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@postgres:5432/stt_db')
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5002))
    MAX_AUDIO_SIZE = int(os.getenv('MAX_AUDIO_SIZE', 10485760))  # 10MB

app.config.from_object(Config)

# Initialize components
kafka_handler = KafkaHandler(app.config['KAFKA_BOOTSTRAP_SERVERS'])
audio_processor = AudioProcessor()
db = DatabaseConnection(app.config['DATABASE_URL'])

# Initialize AWS S3
s3_client = boto3.client(
    's3',
    region_name=app.config['AWS_REGION'],
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db.test_connection()
        kafka_status = kafka_handler.check_connection()
        return jsonify({
            'status': 'healthy',
            'service': 'stt-service',
            'timestamp': datetime.utcnow().isoformat(),
            'kafka': 'connected' if kafka_status else 'disconnected',
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Main endpoint for audio transcription
    Accepts audio file and returns transcription
    """
    try:
        # Validate request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        user_id = request.form.get('user_id', 'anonymous')
        session_id = request.form.get('session_id')
        language = request.form.get('language', 'en-US')
        
        # Validate file size
        audio_file.seek(0, 2)
        file_size = audio_file.tell()
        audio_file.seek(0)
        
        if file_size > app.config['MAX_AUDIO_SIZE']:
            return jsonify({'error': 'Audio file too large'}), 413
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"audio/{user_id}/{timestamp}_{audio_file.filename}"
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        # Process audio
        logger.info(f"Processing audio file: {filename}")
        processed_audio = audio_processor.preprocess(temp_path)
        
        # Upload to S3
        s3_client.upload_file(
            temp_path,
            app.config['S3_BUCKET'],
            filename,
            ExtraArgs={'ContentType': 'audio/wav'}
        )
        s3_url = f"s3://{app.config['S3_BUCKET']}/{filename}"
        
        # Transcribe audio
        transcription_text = audio_processor.transcribe(temp_path, language)
        
        # Calculate confidence and duration
        confidence = audio_processor.calculate_confidence(temp_path)
        duration = audio_processor.get_duration(temp_path)
        
        # Save to database
        transcription = db.create_transcription(
            user_id=user_id,
            session_id=session_id,
            audio_url=s3_url,
            transcription_text=transcription_text,
            confidence=confidence,
            duration=duration,
            language=language
        )
        
        # Publish to Kafka
        kafka_message = {
            'event_type': 'audio_transcribed',
            'transcription_id': transcription.id,
            'user_id': user_id,
            'session_id': session_id,
            'text': transcription_text,
            'confidence': confidence,
            'duration': duration,
            'language': language,
            's3_url': s3_url,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        kafka_handler.publish_transcription(kafka_message)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return jsonify({
            'transcription_id': transcription.id,
            'text': transcription_text,
            'confidence': confidence,
            'duration': duration,
            'language': language,
            'status': 'completed',
            'timestamp': transcription.created_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions/<transcription_id>', methods=['GET'])
def get_transcription(transcription_id):
    """Get transcription by ID"""
    try:
        transcription = db.get_transcription(transcription_id)
        if not transcription:
            return jsonify({'error': 'Transcription not found'}), 404
        
        return jsonify({
            'transcription_id': transcription.id,
            'user_id': transcription.user_id,
            'text': transcription.transcription_text,
            'confidence': transcription.confidence,
            'duration': transcription.duration,
            'language': transcription.language,
            'created_at': transcription.created_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching transcription: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcriptions/user/<user_id>', methods=['GET'])
def get_user_transcriptions(user_id):
    """Get all transcriptions for a user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        transcriptions = db.get_user_transcriptions(user_id, page, per_page)
        
        return jsonify({
            'transcriptions': [
                {
                    'transcription_id': t.id,
                    'text': t.transcription_text,
                    'confidence': t.confidence,
                    'duration': t.duration,
                    'created_at': t.created_at.isoformat()
                } for t in transcriptions
            ],
            'page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user transcriptions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/batch-transcribe', methods=['POST'])
def batch_transcribe():
    """Batch transcription endpoint"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        user_id = request.form.get('user_id', 'anonymous')
        
        results = []
        for audio_file in files:
            # Process each file (simplified)
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                audio_file.save(temp_file.name)
                text = audio_processor.transcribe(temp_file.name)
                results.append({
                    'filename': audio_file.filename,
                    'text': text
                })
                os.unlink(temp_file.name)
        
        return jsonify({
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Batch transcription error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/statistics', methods=['GET'])
def get_statistics():
    """Get service statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Kafka consumer for incoming audio events
def start_kafka_consumer():
    """Start Kafka consumer in background"""
    kafka_handler.start_consumer(process_audio_event)

def process_audio_event(message):
    """Process audio event from Kafka"""
    try:
        event_type = message.get('event_type')
        
        if event_type == 'audio_upload':
            # Process uploaded audio from S3
            s3_url = message.get('s3_url')
            user_id = message.get('user_id')
            
            # Download, process, and transcribe
            logger.info(f"Processing audio event for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error processing Kafka event: {str(e)}")

if __name__ == '__main__':
    # Initialize database
    db.init_db()
    
    # Start Kafka consumer in background thread
    import threading
    consumer_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    consumer_thread.start()
    
    # Start Flask app
    logger.info(f"Starting STT Service on port {app.config['SERVICE_PORT']}")
    app.run(
        host='0.0.0.0',
        port=app.config['SERVICE_PORT'],
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )