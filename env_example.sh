# STT Service Environment Variables

# Service Configuration
SERVICE_PORT=5002
FLASK_DEBUG=False
SERVICE_NAME=stt-service

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_GROUP_ID=stt-service-group
KAFKA_AUTO_OFFSET_RESET=earliest

# Database Configuration
DATABASE_URL=postgresql://stt_user:stt_password@postgres:5432/stt_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET=voice-assistant-bucket
S3_AUDIO_PREFIX=audio/

# Processing Configuration
MAX_AUDIO_SIZE=10485760
MAX_BATCH_SIZE=10
PROCESSING_TIMEOUT=300
SUPPORTED_FORMATS=wav,mp3,flac,ogg,m4a

# Speech Recognition Configuration
DEFAULT_LANGUAGE=en-US
CONFIDENCE_THRESHOLD=0.5
SAMPLE_RATE=16000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis (Optional - for caching)
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600
