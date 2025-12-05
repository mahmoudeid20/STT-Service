-- STT Service Database Schema
-- PostgreSQL Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- Audio sessions table
CREATE TABLE IF NOT EXISTS audio_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_name VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_audio_sessions_user_id ON audio_sessions(user_id);

-- Transcriptions table
CREATE TABLE IF NOT EXISTS transcriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36),
    audio_url VARCHAR(500) NOT NULL,
    transcription_text TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    duration FLOAT DEFAULT 0.0,
    language VARCHAR(10) DEFAULT 'en-US',
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES audio_sessions(id) ON DELETE SET NULL
);

CREATE INDEX idx_transcriptions_user_id ON transcriptions(user_id);
CREATE INDEX idx_transcriptions_session_id ON transcriptions(session_id);
CREATE INDEX idx_transcriptions_created_at ON transcriptions(created_at);
CREATE INDEX idx_transcriptions_status ON transcriptions(status);
CREATE INDEX idx_transcriptions_user_created ON transcriptions(user_id, created_at);

-- Transcription metadata table
CREATE TABLE IF NOT EXISTS transcription_metadata (
    id SERIAL PRIMARY KEY,
    transcription_id VARCHAR(36) NOT NULL UNIQUE,
    word_count INTEGER,
    char_count INTEGER,
    sample_rate INTEGER,
    channels INTEGER,
    bit_depth INTEGER,
    format VARCHAR(20),
    file_size INTEGER,
    processing_time FLOAT,
    FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE
);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transcriptions_updated_at BEFORE UPDATE ON transcriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for transcription statistics
CREATE OR REPLACE VIEW transcription_stats AS
SELECT 
    user_id,
    COUNT(*) as total_transcriptions,
    AVG(confidence) as avg_confidence,
    SUM(duration) as total_duration,
    AVG(duration) as avg_duration,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count
FROM transcriptions
GROUP BY user_id;

-- View for daily statistics
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as transcription_count,
    AVG(confidence) as avg_confidence,
    SUM(duration) as total_duration
FROM transcriptions
WHERE status = 'completed'
GROUP BY DATE(created_at)
ORDER BY date DESC;