# conftest.py - pytest configuration for Job Optimizer Flask app
import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch
import json
import uuid
from app import create_app
from database.models import db, ProcessingSession, DocumentVersion, FeedbackHistory

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create temporary directories for testing
    temp_dir = tempfile.mkdtemp()
    upload_dir = os.path.join(temp_dir, 'uploads')
    processed_dir = os.path.join(temp_dir, 'processed')
    temp_test_dir = os.path.join(temp_dir, 'temp')
    
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(temp_test_dir, exist_ok=True)
    
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('development')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'UPLOAD_FOLDER': upload_dir,
        'PROCESSED_FOLDER': processed_dir,
        'TEMP_FOLDER': temp_test_dir,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
        'ALLOWED_EXTENSIONS': {'pdf', 'docx', 'txt'},
        'OPENAI_API_KEY': 'test-api-key'  # Mock API key for testing
    })
    
    # Create the database and tables
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up temporary files
    os.close(db_fd)
    os.unlink(db_path)
    shutil.rmtree(temp_dir)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def sample_session(app):
    """Create a sample processing session for testing."""
    with app.app_context():
        session_id = str(uuid.uuid4())
        session = ProcessingSession(
            id=session_id,
            job_description_text="Python developer position requiring 3+ years experience",
            original_resume_text="Software engineer with Python and SQL experience",
            original_cover_letter_text="I am interested in this Python developer position",
            status='uploaded'
        )
        db.session.add(session)
        db.session.commit()
        
        # Return the session ID instead of the object to avoid detached instance errors
        return session_id

@pytest.fixture
def completed_session(app):
    """Create a completed processing session for testing."""
    with app.app_context():
        session_id = str(uuid.uuid4())
        session = ProcessingSession(
            id=session_id,
            job_description_text="Senior Python developer role",
            original_resume_text="Experienced Python developer with 5 years experience",
            original_cover_letter_text="Applying for senior Python developer role",
            optimized_resume_text="Optimized resume content",
            optimized_cover_letter_text="Optimized cover letter content",
            extracted_keywords='{"high_priority": ["python", "sql"], "medium_priority": ["git"]}',
            job_requirements='{"technical_skills": ["Python", "SQL"]}',
            keyword_match_score=7.5,
            ats_compatibility_score=8.0,
            content_relevance_score=7.8,
            overall_score=7.7,
            status='completed'
        )
        db.session.add(session)
        db.session.commit()
        
        # Return the session ID instead of the object to avoid detached instance errors
        return session_id

@pytest.fixture
def mock_document_parser():
    """Mock the DocumentParser module."""
    with patch('app.DocumentParser') as mock:
        # Default successful parsing
        mock.parse_document.return_value = {
            'success': True,
            'text': 'Parsed document content'
        }
        yield mock

@pytest.fixture
def mock_job_analyzer():
    """Mock the JobAnalyzer module."""
    with patch('app.JobAnalyzer') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        
        # Mock job analysis
        mock_instance.analyze_job_description.return_value = {
            'success': True,
            'analysis': {
                'keywords': {
                    'high_priority': ['python', 'sql', 'api'],
                    'medium_priority': ['git', 'docker'],
                    'low_priority': ['agile']
                },
                'requirements': {
                    'technical_skills': ['Python', 'SQL', 'REST APIs'],
                    'soft_skills': ['Communication', 'Problem solving'],
                    'education': ['Bachelor\'s degree'],
                    'experience': ['2+ years experience']
                },
                'experience_level': 'mid',
                'industry': 'technology'
            }
        }
        
        # Mock optimization insights
        mock_instance.extract_optimization_insights.return_value = {
            'success': True,
            'insights': {
                'resume_gaps': ['Add more technical keywords'],
                'cover_letter_gaps': ['Mention company culture fit'],
                'keyword_opportunities': ['API development'],
                'ats_recommendations': ['Use standard section headers']
            }
        }
        
        yield mock_instance

@pytest.fixture
def sample_files():
    """Create sample test files."""
    files = {}
    
    # Create temporary files with sample content
    temp_dir = tempfile.mkdtemp()
    
    # Sample resume file
    resume_path = os.path.join(temp_dir, 'sample_resume.txt')
    with open(resume_path, 'w') as f:
        f.write('John Doe\nSoftware Engineer\nPython, SQL, JavaScript')
    
    # Sample cover letter file
    cover_letter_path = os.path.join(temp_dir, 'sample_cover_letter.txt')
    with open(cover_letter_path, 'w') as f:
        f.write('Dear Hiring Manager,\nI am excited to apply for this position.')
    
    # Sample job description file
    job_desc_path = os.path.join(temp_dir, 'sample_job_desc.txt')
    with open(job_desc_path, 'w') as f:
        f.write('Python Developer - 3+ years experience required')
    
    files['resume'] = resume_path
    files['cover_letter'] = cover_letter_path
    files['job_description'] = job_desc_path
    files['temp_dir'] = temp_dir
    
    yield files
    
    # Cleanup
    shutil.rmtree(temp_dir)