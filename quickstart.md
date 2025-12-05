# STT Service - Quick Start Guide

Get the STT service running in 5 minutes!

## 🚀 Quick Start (Docker)

### 1. Prerequisites Check

```bash
# Check Docker
docker --version

# Check Docker Compose
docker-compose --version
```

### 2. Clone and Setup

```bash
# Navigate to service directory
cd services/stt-service

# Copy environment file
cp .env.example .env

# Edit .env file with your AWS credentials
nano .env
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f stt-service

# Wait for services to be ready (~30 seconds)
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:5002/health

# Expected response:
# {"status":"healthy","service":"stt-service",...}
```

### 5. Test Transcription

```bash
# Create test audio file
ffmpeg -f lavfi -i sine=frequency=1000:duration=5 -ar 16000 test_audio.wav

# Transcribe audio
curl -X POST http://localhost:5002/transcribe \
  -F "audio=@test_audio.wav" \
  -F "user_id=test_user" \
  -F "language=en-US"
```

## 🐍 Quick Start (Python - No Docker)

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Install PostgreSQL (if not installed)
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS:
brew install postgresql

# Start PostgreSQL
sudo service postgresql start  # Linux
brew services start postgresql  # macOS

# Create database
createdb stt_db
```

### 3. Setup Kafka

```bash
# Download Kafka
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz
tar -xzf kafka_2.13-3.6.0.tgz
cd kafka_2.13-3.6.0

# Start Kafka (in separate terminals)
bin/zookeeper-server-start.sh config/zookeeper.properties
bin/kafka-server-start.sh config/server.properties
```

### 4. Configure Environment

```bash
# Edit .env file
export DATABASE_URL="postgresql://user:password@localhost:5432/stt_db"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export S3_BUCKET="your_bucket"
```

### 5. Initialize Database

```bash
python -c "from database.connection import DatabaseConnection; db = DatabaseConnection('postgresql://user:password@localhost:5432/stt_db'); db.init_db()"
```

### 6. Run Service

```bash
python app.py
```

## 📝 Common Commands

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart service
docker-compose restart stt-service

# View logs
docker-compose logs -f stt-service

# Rebuild after code changes
docker-compose up -d --build

# Clean everything
docker-compose down -v
```

### API Testing

```bash
# Health check
curl http://localhost:5002/health

# Get languages
curl http://localhost:5002/api/v1/languages

# Get formats
curl http://localhost:5002/api/v1/formats

# Transcribe audio
curl -X POST http://localhost:5002/transcribe \
  -F "audio=@your_audio.wav" \
  -F "user_id=user123" \
  -F "language=en-US"

# Get user transcriptions
curl http://localhost:5002/transcriptions/user/user123
```

### Database Commands

```bash
# Connect to database
docker exec -it stt-postgres psql -U stt_user -d stt_db

# View tables
\dt

# View transcriptions
SELECT * FROM transcriptions LIMIT 10;

# Exit
\q
```

### Kafka Commands

```bash
# List topics
docker exec -it stt-kafka kafka-topics --list --bootstrap-server localhost:9092

# View messages
docker exec -it stt-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic audio-transcribed \
  --from-beginning

# Create topic manually
docker exec -it stt-kafka kafka-topics \
  --create \
  --bootstrap-server localhost:9092 \
  --topic audio-transcribed \
  --partitions 3 \
  --replication-factor 1
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run test script
chmod +x test_service.sh
./test_service.sh
```

## 🔧 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs stt-service

# Check if ports are in use
netstat -tulpn | grep 5002

# Restart all services
docker-compose down && docker-compose up -d
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker exec -it stt-postgres psql -U stt_user -d stt_db -c "SELECT 1"

# Check environment variables
docker-compose exec stt-service env | grep DATABASE
```

### Kafka Connection Failed

```bash
# Check Kafka is running
docker-compose ps kafka

# Test Kafka
docker exec -it stt-kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Check topics
docker exec -it stt-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Audio Processing Errors

```bash
# Check FFmpeg installation
docker-compose exec stt-service ffmpeg -version

# Check audio file format
file your_audio.wav

# Convert audio to supported format
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

## 📚 Next Steps

1. **Read the full README.md** for detailed documentation
2. **Configure AWS S3** for audio storage
3. **Set up monitoring** with Prometheus/Grafana
4. **Configure API Gateway** (Kong) for production
5. **Enable HTTPS** with SSL certificates
6. **Set up CI/CD** pipeline

## 🆘 Need Help?

- Check logs: `docker-compose logs -f`
- Review configuration: `.env` file
- Test endpoints: `./test_service.sh`
- Read documentation: `README.md`

## ⚡ Performance Tips

1. **Increase worker processes** for better concurrency
2. **Enable Redis caching** for faster responses
3. **Optimize audio preprocessing** settings
4. **Use connection pooling** for database
5. **Enable batch processing** for multiple files

## 🔐 Security Checklist

- [ ] Change default database passwords
- [ ] Configure JWT authentication
- [ ] Enable HTTPS
- [ ] Set up rate limiting
- [ ] Restrict CORS origins
- [ ] Use IAM roles for AWS access
- [ ] Enable audit logging
- [ ] Set up firewall rules

---

**Ready to go!** 🎉

Your STT service should now be running at `http://localhost:5002`
