# AI Job Application Optimizer

An intelligent Flask web application that uses AI to analyze job descriptions and optimize resumes and cover letters for maximum impact and ATS compatibility.

## Features

- **Smart Job Analysis**: AI-powered analysis of job descriptions to extract key requirements and keywords
- **Automatic Optimization**: Optimizes resumes and cover letters while maintaining original formatting
- **Real-time Editing**: Interactive editing interface with live score updates
- **ATS Compatibility**: Ensures documents pass Applicant Tracking Systems
- **Detailed Feedback**: Comprehensive scoring and brutal honest feedback (1-10 scale)
- **Multiple Formats**: Supports PDF, DOCX, and TXT files

## Technologies Used

- **Backend**: Flask, SQLAlchemy, OpenAI API
- **Frontend**: Bootstrap 5, jQuery, HTML5
- **Document Processing**: PyPDF2, pdfplumber, python-docx
- **Database**: SQLite (development), PostgreSQL (production)
- **AI**: OpenAI GPT-4 for analysis and optimization

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Redis (optional, for background processing)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/weedu34/AI-Based-Job-Application-Optimiser.git
   cd job-optimizer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv job_optimiser_venv
   source job_optimiser_venv/bin/activate  # On Windows: job_optimiser_venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   SECRET_KEY=your-secret-key-here
   ```

5. **Create upload directories**
   ```bash
   mkdir -p static/uploads static/processed static/temp
   ```

6. **Initialize database**
   ```bash
   python -c "from app import create_app, init_db; app = create_app(); init_db(app)"
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

8. **Open browser**
   Visit `http://localhost:5000`

## Usage

### Step 1: Upload Documents
1. Navigate to the homepage
2. Upload or paste your job description
3. Upload your current resume (PDF/DOCX)
4. Upload your current cover letter (PDF/DOCX/TXT)
5. Click "Start Optimization"

### Step 2: AI Processing
The system will:
- Parse your documents
- Analyze job requirements
- Extract important keywords
- Optimize your documents
- Check ATS compatibility
- Generate scores and feedback

### Step 3: Review & Edit
- View side-by-side comparison (original vs optimized)
- Make real-time edits to optimized documents
- Watch scores update as you make changes
- See keyword highlighting and suggestions

### Step 4: Download
- Get your optimized documents in original format
- Receive detailed feedback report
- Download improvement summary

## API Endpoints

- `POST /upload` - Upload documents
- `POST /api/analyze/<session_id>` - Start AI analysis
- `POST /api/update-document/<session_id>` - Update document content
- `GET /api/generate-feedback/<session_id>` - Generate detailed feedback

## Scoring System

Documents are scored on a 1-10 scale across four categories:

- **Keyword Match Score**: How well keywords from job description are incorporated
- **ATS Compatibility Score**: Whether the document will pass automated screening
- **Content Relevance Score**: How relevant the content is to the job requirements
- **Overall Score**: Weighted average of all scores

## File Structure

```
job_optimizer/
├── app.py                    # Main Flask application
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── .env.template           # Environment variables template
├── README.md              # This file
├── templates/             # HTML templates
│   ├── base.html
│   ├── upload.html
│   ├── processing.html
│   ├── review.html
│   └── download.html
├── static/               # Static files
│   ├── css/
│   ├── js/
│   └── uploads/         # Uploaded files
├── modules/             # Core functionality modules
│   ├── __init__.py
│   ├── document_parser.py
│   ├── job_analyzer.py
│   ├── keyword_extractor.py
│   ├── resume_optimizer.py
│   ├── cover_letter_optimizer.py
│   ├── ats_checker.py
│   ├── feedback_generator.py
│   └── document_generator.py
├── database/           # Database models
│   └── models.py
└── tests/             # Test suite
    ├── __init__.py
    ├── conftest.py
    └── test_basic_functionality.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `DATABASE_URL` | Database connection string | `sqlite:///job_optimizer.db` |
| `REDIS_URL` | Redis connection for background tasks | `redis://localhost:6379/0` |
| `MAX_CONTENT_LENGTH` | Maximum file upload size | `16MB` |

### Supported File Formats

- **Job Descriptions**: PDF, DOCX, TXT, or text input
- **Resumes**: PDF, DOCX
- **Cover Letters**: PDF, DOCX, TXT

## Testing

### 🧪 Testing Overview

Our comprehensive testing suite ensures reliability and maintainability using pytest. The tests cover:
- **Unit Tests** - Individual functions and components
- **Integration Tests** - API endpoints and database operations
- **File Upload Tests** - Document handling and validation
- **Error Handling Tests** - Failure scenarios and edge cases
- **Mocked External Services** - AI analysis and document parsing

### Test Coverage

#### Core Functionality Tested
- ✅ **File Upload & Validation** - Document type checking, file security, missing file handling
- ✅ **Session Management** - Processing session creation, status transitions, database persistence
- ✅ **API Endpoints** - Document analysis, document updates, feedback generation
- ✅ **Database Operations** - CRUD operations, version management, score calculations
- ✅ **Error Scenarios** - Parser failures, AI service failures, invalid inputs
- ✅ **Workflow States** - Page access control, session state validation

#### External Dependencies Mocked
- **DocumentParser** - Controlled success/failure responses
- **JobAnalyzer** - Mocked AI analysis without OpenAI API calls
- **File Operations** - Temporary directories for isolated testing

### Quick Start

#### Install Testing Dependencies
```bash
pip install pytest pytest-flask pytest-cov pytest-mock factory-boy faker
```

#### Run Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov=database --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m api           # API tests only
pytest -m upload        # File upload tests only
```

### Test Structure

```
tests/
├── __init__.py                     # Empty file for Python package
├── conftest.py                     # Test configuration and fixtures
├── test_basic_functionality.py    # Core functionality tests
└── pytest.ini                     # Pytest configuration
```

#### Key Test Files

- **`conftest.py`** - App configuration, test database setup, fixtures, mocking setup
- **`test_basic_functionality.py`** - Comprehensive tests for all core functionality

### Running Specific Tests

```bash
# By test file
pytest tests/test_basic_functionality.py

# By test class
pytest tests/test_basic_functionality.py::TestFileUpload

# By individual test
pytest tests/test_basic_functionality.py::TestFileUpload::test_upload_with_job_description_text_only

# By markers
pytest -m "not slow"        # Skip slow tests
pytest -m "api and upload"  # Run API and upload tests

# With coverage
pytest --cov=app --cov=database --cov-report=html
# Open htmlcov/index.html to view detailed coverage
```

### Debugging Tests

```bash
# Verbose output with print statements
pytest -v -s

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf

# Debug specific failing test
pytest tests/test_basic_functionality.py::TestAPIEndpoints::test_analyze_endpoint -v -s
```

### Common Testing Issues

#### ImportError: No module named 'app'
```bash
# Ensure you're in the project root directory
cd /path/to/your/project
pytest
```

#### Database Connection Errors
```bash
# Check that your models are importable
python -c "from database.models import db, ProcessingSession"
```

#### Missing Dependencies
```bash
# Install all test dependencies
pip install pytest pytest-flask pytest-cov pytest-mock
```

### Adding New Tests

#### Create New Test File
```python
# tests/test_new_feature.py
import pytest

class TestNewFeature:
    def test_new_functionality(self, client):
        response = client.get('/new-endpoint')
        assert response.status_code == 200
```

#### Use Existing Fixtures
```python
def test_with_session(self, client, sample_session):
    # sample_session is available from conftest.py
    response = client.get(f'/api/something/{sample_session}')
    assert response.status_code == 200
```

### Test Performance

- **Full test suite**: ~5-15 seconds
- **Unit tests only**: ~2-5 seconds
- **Individual test**: ~0.1-1 seconds

#### Optimization Tips
```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Skip slow tests during development
pytest -m "not slow"
```

### CI/CD Integration

#### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    pip install pytest pytest-flask pytest-cov
    pytest --cov=app --cov-report=xml
```

## Development

### Adding New Features

1. **Document Processing**: Extend `modules/document_parser.py`
2. **AI Analysis**: Modify `modules/job_analyzer.py`
3. **Optimization Logic**: Update `modules/resume_optimizer.py` or `modules/cover_letter_optimizer.py`
4. **UI Components**: Add to templates and static files

### Database Migrations

When adding new fields to models:

```bash
# Add migration logic to database/models.py
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Development Workflow

1. **Write tests first** - Test-driven development approach
2. **Run tests frequently** - Catch issues early
3. **Maintain test coverage** - Aim for >80% coverage
4. **Mock external services** - Keep tests fast and reliable

## Deployment

### Production Deployment

1. **Set up production environment**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@localhost/joboptimizer
   ```

2. **Use production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. **Set up reverse proxy** (nginx/Apache)
4. **Enable HTTPS**
5. **Set up background task processing** with Celery
6. **Configure file storage** (AWS S3, etc.)

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Make sure `.env` file exists and contains `OPENAI_API_KEY`
   - Verify the key is valid and has credits

2. **File upload errors**
   - Check file size limits in `config.py`
   - Ensure upload directories exist and are writable

3. **Document parsing failures**
   - Verify file format is supported
   - Check if PDF is password-protected or corrupted

4. **Database errors**
   - Run database initialization: `python -c "from app import create_app, init_db; app = create_app(); init_db(app)"`
   - Check file permissions for SQLite database

5. **Test failures**
   - Ensure all testing dependencies are installed: `pip install pytest pytest-flask pytest-cov pytest-mock`
   - Check that you're in the project root directory
   - Verify database models are importable

### Performance Optimization

- Use Redis for caching analysis results
- Implement background processing with Celery
- Use CDN for static files
- Optimize document parsing for large files
- Implement rate limiting for API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. **Add tests for new functionality**
5. **Run the test suite**: `pytest`
6. **Ensure tests pass** and maintain coverage
7. Submit a pull request

### Testing Guidelines for Contributors

- Write tests for all new features
- Maintain or improve test coverage
- Use descriptive test names
- Mock external dependencies
- Follow existing test patterns in `tests/test_basic_functionality.py`

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Check troubleshooting section
- Review API documentation
- **Run the test suite** to verify setup: `pytest -v`
- Create an issue on GitHub
- Contact support team

## Roadmap

### Upcoming Features
- [ ] Multiple resume templates
- [ ] Industry-specific optimization
- [ ] Bulk processing
- [ ] Integration with job boards
- [ ] Advanced analytics dashboard
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Interview preparation features
- [ ] **Enhanced test coverage** for new features
- [ ] **Performance testing** for large files

### Known Limitations
- OpenAI API rate limits
- Large file processing time
- Limited to English language
- Requires internet connection
- PDF complex formatting may not be preserved

---

**Built with ❤️ to help job seekers land their dream jobs!**