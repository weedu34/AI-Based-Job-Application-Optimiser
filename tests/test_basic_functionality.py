# tests/test_basic_functionality.py - Core functionality tests
import pytest
import os
import json
import uuid
from database.models import ProcessingSession, DocumentVersion
from unittest.mock import Mock
from werkzeug.datastructures import FileStorage
from io import BytesIO

class TestAppBasics:
    """Test basic app configuration and setup."""
    
    def test_app_exists(self, app):
        """Test that the app instance exists."""
        assert app is not None

    def test_app_is_testing(self, app):
        """Test that the app is in testing mode."""
        assert app.config['TESTING']

    def test_app_config(self, app):
        """Test app configuration for testing."""
        assert app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///')
        assert app.config['SECRET_KEY'] == 'test-secret-key'
        assert 'pdf' in app.config['ALLOWED_EXTENSIONS']

class TestRoutes:
    """Test basic route functionality."""
    
    def test_index_route(self, client):
        """Test the main upload page."""
        response = client.get('/')
        assert response.status_code == 200
        # Check if upload form is present (adjust based on your template)
        assert b'upload' in response.data.lower()

    def test_process_route_with_valid_session(self, client, sample_session):
        """Test process page with valid session."""
        response = client.get(f'/process/{sample_session}')
        assert response.status_code == 200

    def test_process_route_with_invalid_session(self, client):
        """Test process page with invalid session ID."""
        fake_id = str(uuid.uuid4())
        response = client.get(f'/process/{fake_id}')
        assert response.status_code == 404

    def test_review_route_requires_completed_session(self, client, sample_session):
        """Test that review page redirects if session not completed."""
        response = client.get(f'/review/{sample_session}')
        # Should redirect to process page since session is not completed
        assert response.status_code == 302
        assert f'/process/{sample_session}' in response.location

    def test_review_route_with_completed_session(self, client, completed_session):
        """Test review page with completed session."""
        response = client.get(f'/review/{completed_session}')
        assert response.status_code == 200

class TestFileUpload:
    """Test file upload functionality."""
    
    def test_upload_with_missing_files(self, client):
        """Test upload with missing required files."""
        response = client.post('/upload', data={})
        assert response.status_code == 302  # Redirect back to index
        # Should redirect with flash message

    def test_upload_with_empty_filenames(self, client):
        """Test upload with empty filenames."""
        data = {
            'resume': (BytesIO(b''), ''),
            'cover_letter': (BytesIO(b''), ''),
            'job_description_text': 'Python developer position'
        }
        response = client.post('/upload', data=data)
        assert response.status_code == 302  # Redirect back to index

    def test_upload_with_job_description_text_only(self, client, mock_document_parser):
        """Test upload with job description as text input."""
        data = {
            'resume': (BytesIO(b'Resume content'), 'resume.txt'),
            'cover_letter': (BytesIO(b'Cover letter content'), 'cover_letter.txt'),
            'job_description_text': 'Python developer position requiring 3+ years experience'
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        # Should create session and redirect to processing
        assert response.status_code == 302
        assert '/process/' in response.location

    def test_upload_with_job_description_file(self, client, mock_document_parser):
        """Test upload with job description as file."""
        data = {
            'resume': (BytesIO(b'Resume content'), 'resume.txt'),
            'cover_letter': (BytesIO(b'Cover letter content'), 'cover_letter.txt'),
            'job_description': (BytesIO(b'Job description content'), 'job_desc.txt'),
            'job_description_text': ''  # Empty text when file is provided
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        assert response.status_code == 302
        assert '/process/' in response.location

    def test_allowed_file_extensions(self, app):
        """Test file extension validation."""
        with app.app_context():
            # Test allowed extensions
            assert app.config['ALLOWED_EXTENSIONS'] == {'pdf', 'docx', 'txt'}

class TestSessionManagement:
    """Test processing session management."""
    
    def test_session_creation(self, app):
        """Test creating a new processing session."""
        with app.app_context():
            session_id = str(uuid.uuid4())
            session = ProcessingSession(
                id=session_id,
                job_description_text="Test job description"
            )
            from database.models import db
            db.session.add(session)
            db.session.commit()
            
            # Retrieve and verify
            retrieved = ProcessingSession.query.get(session_id)
            assert retrieved is not None
            assert retrieved.job_description_text == "Test job description"
            assert retrieved.status == 'uploaded'  # Default status

    def test_session_status_transitions(self, app, sample_session):
        """Test session status changes."""
        with app.app_context():
            # Get the session from database using the ID
            session_obj = ProcessingSession.query.get(sample_session)
            assert session_obj is not None
            
            # Start with uploaded status
            assert session_obj.status == 'uploaded'
            
            # Update to processing
            session_obj.status = 'processing'
            from database.models import db
            db.session.commit()
            
            # Verify change
            updated_session = ProcessingSession.query.get(sample_session)
            assert updated_session.status == 'processing'

class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    def test_analyze_endpoint_with_valid_session(self, client, sample_session, mock_job_analyzer):
        """Test document analysis API endpoint."""
        response = client.post(f'/api/analyze/{sample_session}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'analysis' in data
        assert 'insights' in data
        assert 'scores' in data

    def test_analyze_endpoint_with_invalid_session(self, client):
        """Test analysis endpoint with invalid session ID."""
        fake_id = str(uuid.uuid4())
        response = client.post(f'/api/analyze/{fake_id}')
        # Based on the actual app behavior, it returns 200 with success: False for invalid sessions
        # rather than 404, because the route exists but the session doesn't
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False

    def test_update_document_endpoint(self, client, completed_session):
        """Test document update API endpoint."""
        update_data = {
            'document_type': 'resume',
            'content': 'Updated resume content with more keywords'
        }
        
        response = client.post(
            f'/api/update-document/{completed_session}',
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'scores' in data

    def test_update_document_invalid_type(self, client, completed_session):
        """Test document update with invalid document type."""
        update_data = {
            'document_type': 'invalid_type',
            'content': 'Some content'
        }
        
        response = client.post(
            f'/api/update-document/{completed_session}',
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should still return 200 but not update anything meaningful
        assert response.status_code == 200

    def test_generate_feedback_endpoint(self, client, completed_session):
        """Test feedback generation endpoint."""
        response = client.get(f'/api/generate-feedback/{completed_session}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'feedback' in data

class TestDatabaseOperations:
    """Test database operations and models."""
    
    def test_document_version_creation(self, app, completed_session):
        """Test creating document versions."""
        with app.app_context():
            version = DocumentVersion(
                session_id=completed_session,
                document_type='resume',
                content='Version 1 content',
                version_number=1
            )
            
            from database.models import db
            db.session.add(version)
            db.session.commit()
            
            # Verify creation
            retrieved = DocumentVersion.query.filter_by(
                session_id=completed_session,
                document_type='resume'
            ).first()
            
            assert retrieved is not None
            assert retrieved.content == 'Version 1 content'
            assert retrieved.version_number == 1

    def test_session_scores_update(self, app, sample_session):
        """Test updating session scores."""
        with app.app_context():
            # Get the session object from database
            session_obj = ProcessingSession.query.get(sample_session)
            assert session_obj is not None
            
            # Update scores
            session_obj.keyword_match_score = 8.5
            session_obj.ats_compatibility_score = 7.5
            session_obj.content_relevance_score = 8.0
            session_obj.overall_score = 8.0
            
            from database.models import db
            db.session.commit()
            
            # Verify updates
            updated = ProcessingSession.query.get(sample_session)
            assert updated.keyword_match_score == 8.5
            assert updated.overall_score == 8.0

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_document_parser_failure(self, client, mock_document_parser):
        """Test handling when document parsing fails."""
        # Configure mock to return failure
        mock_document_parser.parse_document.return_value = {
            'success': False,
            'error': 'Failed to parse document'
        }
        
        data = {
            'resume': (BytesIO(b'Resume content'), 'resume.txt'),
            'cover_letter': (BytesIO(b'Cover letter content'), 'cover_letter.txt'),
            'job_description_text': 'Python developer position'
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        # Should redirect back to index with error message
        assert response.status_code == 302

    def test_job_analyzer_failure(self, client, sample_session, mock_job_analyzer):
        """Test handling when job analysis fails."""
        # Configure mock to return failure
        mock_job_analyzer.analyze_job_description.return_value = {
            'success': False,
            'error': 'AI analysis failed'
        }
        
        response = client.post(f'/api/analyze/{sample_session}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_missing_job_description(self, client):
        """Test upload without job description (file or text)."""
        data = {
            'resume': (BytesIO(b'Resume content'), 'resume.txt'),
            'cover_letter': (BytesIO(b'Cover letter content'), 'cover_letter.txt'),
            'job_description_text': ''  # Empty text and no file
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 302  # Redirect with error