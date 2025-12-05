"""
Database Connection Module
Handles PostgreSQL database connections and operations
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from datetime import datetime
import uuid

from database.models import Base, Transcription, User, AudioSession

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = None
        self.Session = None
        self.initialize_engine()
    
    def initialize_engine(self):
        """Initialize database engine with connection pooling"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            self.Session = scoped_session(
                sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {str(e)}")
            raise
    
    def init_db(self):
        """Initialize database tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def create_transcription(self, user_id, session_id, audio_url, transcription_text, 
                            confidence, duration, language='en-US'):
        """Create new transcription record"""
        try:
            with self.get_session() as session:
                transcription = Transcription(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    session_id=session_id,
                    audio_url=audio_url,
                    transcription_text=transcription_text,
                    confidence=confidence,
                    duration=duration,
                    language=language,
                    status='completed',
                    created_at=datetime.utcnow()
                )
                
                session.add(transcription)
                session.flush()
                
                logger.info(f"Transcription created: {transcription.id}")
                return transcription
                
        except Exception as e:
            logger.error(f"Error creating transcription: {str(e)}")
            raise
    
    def get_transcription(self, transcription_id):
        """Get transcription by ID"""
        try:
            with self.get_session() as session:
                transcription = session.query(Transcription).filter(
                    Transcription.id == transcription_id
                ).first()
                
                if transcription:
                    # Detach from session to avoid expiration
                    session.expunge(transcription)
                
                return transcription
                
        except Exception as e:
            logger.error(f"Error fetching transcription: {str(e)}")
            return None
    
    def get_user_transcriptions(self, user_id, page=1, per_page=20):
        """Get all transcriptions for a user with pagination"""
        try:
            with self.get_session() as session:
                transcriptions = session.query(Transcription).filter(
                    Transcription.user_id == user_id
                ).order_by(
                    Transcription.created_at.desc()
                ).limit(per_page).offset((page - 1) * per_page).all()
                
                # Detach from session
                for t in transcriptions:
                    session.expunge(t)
                
                return transcriptions
                
        except Exception as e:
            logger.error(f"Error fetching user transcriptions: {str(e)}")
            return []
    
    def update_transcription(self, transcription_id, **kwargs):
        """Update transcription record"""
        try:
            with self.get_session() as session:
                transcription = session.query(Transcription).filter(
                    Transcription.id == transcription_id
                ).first()
                
                if transcription:
                    for key, value in kwargs.items():
                        if hasattr(transcription, key):
                            setattr(transcription, key, value)
                    
                    transcription.updated_at = datetime.utcnow()
                    logger.info(f"Transcription updated: {transcription_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating transcription: {str(e)}")
            return False
    
    def delete_transcription(self, transcription_id):
        """Delete transcription record"""
        try:
            with self.get_session() as session:
                transcription = session.query(Transcription).filter(
                    Transcription.id == transcription_id
                ).first()
                
                if transcription:
                    session.delete(transcription)
                    logger.info(f"Transcription deleted: {transcription_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error deleting transcription: {str(e)}")
            return False
    
    def create_user(self, user_id, email, name):
        """Create new user"""
        try:
            with self.get_session() as session:
                user = User(
                    id=user_id,
                    email=email,
                    name=name,
                    created_at=datetime.utcnow()
                )
                
                session.add(user)
                logger.info(f"User created: {user_id}")
                return user
                
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return None
    
    def create_session(self, user_id, session_name=None):
        """Create audio session"""
        try:
            with self.get_session() as session:
                audio_session = AudioSession(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    session_name=session_name or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                    started_at=datetime.utcnow()
                )
                
                session.add(audio_session)
                session.flush()
                
                logger.info(f"Audio session created: {audio_session.id}")
                return audio_session
                
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def get_statistics(self):
        """Get service statistics"""
        try:
            with self.get_session() as session:
                total_transcriptions = session.query(Transcription).count()
                total_users = session.query(User).count()
                
                avg_confidence = session.query(
                    text("AVG(confidence)")
                ).select_from(Transcription).scalar()
                
                total_duration = session.query(
                    text("SUM(duration)")
                ).select_from(Transcription).scalar()
                
                return {
                    'total_transcriptions': total_transcriptions,
                    'total_users': total_users,
                    'average_confidence': round(float(avg_confidence or 0), 2),
                    'total_audio_duration': round(float(total_duration or 0), 2)
                }
                
        except Exception as e:
            logger.error(f"Error fetching statistics: {str(e)}")
            return {}
    
    def close(self):
        """Close database connections"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connections closed")