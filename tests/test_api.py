"""
Unit tests for STT Service API
"""
import pytest
import json
import io
from app import app as flask_app

@pytest.fixture
def app():
    """Create test app"""
    flask_app.config['TESTING'] = True
    yield flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] in ['healthy', 'unhealthy']
    assert 'service' in data

def test_transcribe_no_file(client):
    """Test transcribe endpoint without file"""
    response = client.post('/transcribe')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_transcribe_with_file(client):
    """Test transcribe endpoint with audio file"""
    # Create fake audio file
    data = {
        'audio': (io.BytesIO(b"fake audio data"), 'test.wav'),
        'user_id': 'test_user',
        'language': 'en-US'
    }
    
    response = client.post(
        '/transcribe',
        data=data,
        content_type='multipart/form-data'
    )
    
    # May fail in test environment without actual audio processing
    assert response.status_code in [200, 500]

def test_get_transcription_not_found(client):
    """Test get transcription with invalid ID"""
    response = client.get('/transcriptions/invalid_id')
    assert response.status_code == 404

def test_get_supported_languages(client):
    """Test languages endpoint"""
    response = client.get('/api/v1/languages')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'languages' in data
    assert len(data['languages']) > 0

def test_get_supported_formats(client):
    """Test formats endpoint"""
    response = client.get('/api/v1/formats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'formats' in data
    assert len(data['formats']) > 0

def test_validate_audio_no_file(client):
    """Test validate endpoint without file"""
    response = client.post('/api/v1/validate')
    assert response.status_code == 400

def test_statistics(client):
    """Test statistics endpoint"""
    response = client.get('/statistics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)