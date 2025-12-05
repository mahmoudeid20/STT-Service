"""
Database Models for STT Service
SQLAlchemy ORM models
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transcriptions = relationship('Transcription', back_populates='user', cascade='all, delete-orphan')
    sessions = relationship('AudioSession', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class AudioSession(Base):
    """Audio session model for grouping transcriptions"""
    __tablename__ = 'audio_sessions'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    session_name = Column(String(255))
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime)
    
    # Relationships
    user = relationship('User', back_populates='sessions')
    transcriptions = relationship('Transcription', back_populates='session')
    
    def __repr__(self):
        return f"<AudioSession(id={self.id}, user_id={self.user_id})>"


class Transcription(Base):
    """Transcription model"""
    __tablename__ = 'transcriptions'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey('audio_sessions.id'), index=True)
    audio_url = Column(String(500), nullable=False)
    transcription_text = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    duration = Column(Float, default=0.0)  # Duration in seconds
    language = Column(String(10), default='en-US')
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='transcriptions')
    session = relationship('AudioSession', back_populates='transcriptions')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_session_created', 'session_id', 'created_at'),
        Index('idx_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Transcription(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'audio_url': self.audio_url,
            'transcription_text': self.transcription_text,
            'confidence': self.confidence,
            'duration': self.duration,
            'language': self.language,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TranscriptionMetadata(Base):
    """Additional metadata for transcriptions"""
    __tablename__ = 'transcription_metadata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transcription_id = Column(String(36), ForeignKey('transcriptions.id'), nullable=False, unique=True)
    word_count = Column(Integer)
    char_count = Column(Integer)
    sample_rate = Column(Integer)
    channels = Column(Integer)
    bit_depth = Column(Integer)
    format = Column(String(20))
    file_size = Column(Integer)  # Size in bytes
    processing_time = Column(Float)  # Time taken to process in seconds
    
    def __repr__(self):
        return f"<TranscriptionMetadata(transcription_id={self.transcription_id})>"