# STT Service (Speech-to-Text)

**Member 3** - Voice Assistant Platform

## Overview

The STT Service is responsible for converting audio files to text using advanced speech recognition technology. It supports multiple languages, audio formats, and provides high-quality transcriptions with confidence scores.

## Features

- 🎤 **Multi-format Support**: WAV, MP3, FLAC, OGG, M4A
- 🌍 **Multi-language**: 14+ languages supported
- ⚡ **Real-time Processing**: Fast transcription with streaming support
- 📊 **Confidence Scoring**: Quality metrics for each transcription
- 💾 **Database Integration**: PostgreSQL for data persistence
- 📨 **Kafka Integration**: Event-driven architecture
- ☁️ **S3 Storage**: Audio file storage in AWS S3
- 🔄 **Batch Processing**: Process multiple files simultaneously

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐     ┌──────────┐
│  Flask API  │────▶│  Kafka   │
└──────┬──────┘     └──────────┘
       │
       ├──────▶ Audio Processor
       │
       ├──────▶ PostgreSQL DB
       │
       └──────▶ AWS S3
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Kafka 3.0+
- AWS Account (for S3)
- FFmpeg

### Setup

1. **Clone the repository**
```bash
cd services/stt-service
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize database**
```bash
python -c "from database.connection import DatabaseConnection; db = DatabaseConnection('your_db_url'); db.init_db()"
```

5. **Run the service**
```bash
python app.py
```

## Environment Variables

```env
# Service Configuration
SERVICE_PORT=5002
FLASK_DEBUG=False

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/stt_db

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=voice-assistant-bucket

# Processing Configuration
MAX_AUDIO_SIZE=10485760  # 10MB in bytes
```

## API Endpoints

### Core Endpoints

#### 1. Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "stt-service",
  "timestamp": "2024-01-15T10:30:00Z",
  "kafka": "connected",
  "database": "connected"
}
```

#### 2. Transcribe Audio
```http
POST /transcribe
Content-Type: multipart/form-data

audio: <file>
user_id: string
session_id: string (optional)
language: string (default: "en-US")
```

Response:
```json
{
  "transcription_id": "uuid",
  "text": "Hello, this is a test transcription",
  "confidence": 0.95,
  "duration": 5.2,
  "language": "en-US",
  "status": "completed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 3. Get Transcription
```http
GET /transcriptions/{transcription_id}
```

#### 4. Get User Transcriptions
```http
GET /transcriptions/user/{user_id}?page=1&per_page=20
```

#### 5. Batch Transcribe
```http
POST /batch-transcribe
Content-Type: multipart/form-data

files: <file[]>
user_id: string
```

### Additional Endpoints

#### Get Supported Languages
```http
GET /api/v1/languages
```

#### Get Supported Formats
```http
GET /api/v1/formats
```

#### Validate Audio File
```http
POST /api/v1/validate
Content-Type: multipart/form-data

audio: <file>
```

#### Create Session
```http
POST /api/v1/sessions
Content-Type: application/json

{
  "user_id": "string",
  "session_name": "string"
}
```

## Supported Languages

- English (US, UK)
- Spanish (Spain, Mexico)
- French
- German
- Italian
- Portuguese (Brazil)
- Japanese
- Korean
- Chinese (Simplified)
- Arabic
- Russian
- Hindi

## Audio Processing Pipeline

1. **Upload**: Audio file uploaded to API
2. **Validation**: File format and size validation
3. **Preprocessing**: 
   - Format conversion to WAV
   - Noise reduction
   - Volume normalization
   - Sample rate conversion (16kHz)
4. **Storage**: Upload to S3
5. **Transcription**: Speech-to-text processing
6. **Post-processing**: 
   - Confidence calculation
   - Metadata extraction
7. **Storage**: Save to database
8. **Event Publishing**: Publish to Kafka

## Kafka Topics

### Published Topics

- `audio-transcribed`: Successful transcription events
- `stt-errors`: Error events

### Consumed Topics

- `audio-upload`: New audio upload events
- `audio-processing-request`: Processing requests from other services

## Database Schema

### Tables

1. **users**
   - id (PK)
   - email
   - name
   - created_at
   - updated_at

2. **audio_sessions**
   - id (PK)
   - user_id (FK)
   - session_name
   - started_at
   - ended_at

3. **transcriptions**
   - id (PK)
   - user_id (FK)
   - session_id (FK)
   - audio_url
   - transcription_text
   - confidence
   - duration
   - language
   - status
   - created_at
   - updated_at

4. **transcription_metadata**
   - transcription_id (FK)
   - word_count
   - sample_rate
   - processing_time

## Docker Deployment

```bash
# Build image
docker build -t stt-service .

# Run container
docker run -d \
  -p 5002:5002 \
  --env-file .env \
  --name stt-service \
  stt-service
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_api.py::test_health_check
```

## Performance Optimization

- **Connection Pooling**: Database connection pool (size: 10)
- **Kafka Batching**: Batch message production
- **Audio Caching**: Preprocessed audio cache
- **Async Processing**: Background task processing

## Monitoring

### Metrics

- Total transcriptions
- Average confidence score
- Processing time
- Error rate
- Kafka lag

### Logs

Logs are structured in JSON format:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "stt-service",
  "message": "Transcription completed",
  "transcription_id": "uuid",
  "duration": 5.2
}
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid file format | Use supported formats |
| 413 Payload Too Large | File size > 10MB | Compress or split audio |
| 500 Internal Error | Processing failure | Check logs |
| 503 Service Unavailable | Dependency down | Check Kafka/DB status |

## Security

- Input validation on all endpoints
- File size limits
- Rate limiting (via API Gateway)
- JWT authentication (via API Gateway)
- Secure S3 access with IAM roles

## Contributing

1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Use meaningful commit messages

## License

MIT License

## Contact

Member 3 - STT Service
Project: CSE363 Phase 2
