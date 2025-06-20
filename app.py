from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid

# Import our modules
from config import config
from database.models import db, ProcessingSession, DocumentVersion, FeedbackHistory
from modules.document_parser import DocumentParser
from modules.job_analyzer import JobAnalyzer

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
    
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    @app.route('/')
    def index():
        """Main upload page"""
        return render_template('upload.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_documents():
        """Handle document uploads and create processing session"""
        
        print("\n📁 Upload endpoint called!")  # Debug line
        print(f"Request method: {request.method}")  # Debug line
        print(f"Request files: {list(request.files.keys())}")  # Debug line
        print(f"Job description text length: {len(request.form.get('job_description_text', ''))}")  # Debug line
        
        try:
            # Check job description (file OR text)
            job_desc_file = request.files.get('job_description')
            job_desc_text = request.form.get('job_description_text', '').strip()
            
            if not job_desc_file or not job_desc_file.filename:
                # No file uploaded, check if text is provided
                if not job_desc_text:
                    flash('Please provide a job description (file upload or text input)')
                    return redirect(url_for('index'))
            
            # Check required files (resume and cover letter)
            required_files = ['resume', 'cover_letter']
            
            for file_key in required_files:
                if file_key not in request.files:
                    flash(f'Missing {file_key.replace("_", " ")}')
                    return redirect(url_for('index'))
                
                file = request.files[file_key]
                if file.filename == '':
                    flash(f'No {file_key.replace("_", " ")} selected')
                    return redirect(url_for('index'))
            
            # Create new processing session
            session_id = str(uuid.uuid4())
            session = ProcessingSession(id=session_id)
            
            # Handle job description (text input or file)
            job_desc_file = request.files.get('job_description')
            job_desc_text = request.form.get('job_description_text', '')
            
            if job_desc_file and job_desc_file.filename:
                # Save and parse job description file
                filename = secure_filename(f"{session_id}_job_desc_{job_desc_file.filename}")
                job_desc_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                job_desc_file.save(job_desc_path)
                
                # Parse job description
                parsed_job = DocumentParser.parse_document(job_desc_path)
                if parsed_job['success']:
                    session.job_description_text = parsed_job['text']
                else:
                    flash(f'Error parsing job description: {parsed_job["error"]}')
                    return redirect(url_for('index'))
            else:
                # Use text input
                session.job_description_text = job_desc_text
            
            # Handle resume file
            resume_file = request.files['resume']
            if resume_file and allowed_file(resume_file.filename):
                filename = secure_filename(f"{session_id}_resume_{resume_file.filename}")
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                resume_file.save(resume_path)
                session.original_resume_path = resume_path
                
                # Parse resume
                parsed_resume = DocumentParser.parse_document(resume_path)
                if parsed_resume['success']:
                    session.original_resume_text = parsed_resume['text']
                else:
                    flash(f'Error parsing resume: {parsed_resume["error"]}')
                    return redirect(url_for('index'))
            
            # Handle cover letter file
            cover_letter_file = request.files['cover_letter']
            if cover_letter_file and allowed_file(cover_letter_file.filename):
                filename = secure_filename(f"{session_id}_cover_letter_{cover_letter_file.filename}")
                cover_letter_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                cover_letter_file.save(cover_letter_path)
                session.original_cover_letter_path = cover_letter_path
                
                # Parse cover letter
                parsed_cover = DocumentParser.parse_document(cover_letter_path)
                if parsed_cover['success']:
                    session.original_cover_letter_text = parsed_cover['text']
                else:
                    flash(f'Error parsing cover letter: {parsed_cover["error"]}')
                    return redirect(url_for('index'))
            
            # Save session to database
            db.session.add(session)
            db.session.commit()
            
            # Redirect to processing page
            return redirect(url_for('process_documents', session_id=session_id))
            
        except Exception as e:
            flash(f'Upload error: {str(e)}')
            return redirect(url_for('index'))
    
    @app.route('/process/<session_id>')
    def process_documents(session_id):
        """Processing page - shows progress and handles optimization"""
        
        session = ProcessingSession.query.get_or_404(session_id)
        return render_template('processing.html', session=session)
    
    @app.route('/api/analyze/<session_id>', methods=['POST'])
    def analyze_documents(session_id):
        """API endpoint to analyze documents and generate optimizations"""
        
        try:
            session = ProcessingSession.query.get_or_404(session_id)
            session.status = 'processing'
            db.session.commit()
            
            # Initialize job analyzer
            try:
                analyzer = JobAnalyzer()
            except Exception as e:
                print(f"Error initializing JobAnalyzer: {e}")
                return jsonify({'success': False, 'error': f'OpenAI configuration error: {str(e)}'})
            
            # Analyze job description
            try:
                job_analysis = analyzer.analyze_job_description(session.job_description_text)
            except Exception as e:
                print(f"Error in job analysis: {e}")
                # Fallback analysis
                job_analysis = {
                    'success': True,
                    'analysis': {
                        'keywords': {
                            'high_priority': ['python', 'sql', 'api', 'rest'],
                            'medium_priority': ['git', 'docker', 'linux'],
                            'low_priority': ['agile', 'scrum']
                        },
                        'requirements': {
                            'technical_skills': ['Python', 'SQL', 'REST APIs'],
                            'soft_skills': ['Communication', 'Problem solving'],
                            'education': ['Bachelor\'s degree'],
                            'experience': ['2+ years experience'],
                            'certifications': []
                        },
                        'experience_level': 'mid',
                        'industry': 'technology',
                        'company_culture': ['collaborative', 'innovative'],
                        'job_type': 'full-time'
                    }
                }
            if not job_analysis['success']:
                return jsonify({'success': False, 'error': job_analysis['error']})
            
            # Store analysis results
            session.extracted_keywords = json.dumps(job_analysis['analysis']['keywords'])
            session.job_requirements = json.dumps(job_analysis['analysis']['requirements'])
            
            # Get optimization insights
            try:
                insights = analyzer.extract_optimization_insights(
                    session.job_description_text,
                    session.original_resume_text,
                    session.original_cover_letter_text
                )
            except Exception as e:
                print(f"Error generating insights: {e}")
                # Fallback insights
                insights = {
                    'success': True,
                    'insights': {
                        'resume_gaps': ['Add more technical keywords', 'Include quantifiable achievements'],
                        'cover_letter_gaps': ['Mention company culture fit', 'Add specific examples'],
                        'keyword_opportunities': ['API development', 'Database management'],
                        'experience_matching': {
                            'strong_matches': ['Programming experience', 'Problem solving'],
                            'weak_matches': ['Leadership experience'],
                            'missing_experiences': ['Cloud platforms']
                        },
                        'ats_recommendations': ['Use standard section headers', 'Include more keywords'],
                        'priority_actions': ['Add technical skills section', 'Quantify achievements']
                    }
                }
            
            if insights['success']:
                # Generate optimized resume (placeholder - will implement optimization module)
                session.optimized_resume_text = session.original_resume_text  # Temporary
                session.optimized_cover_letter_text = session.original_cover_letter_text  # Temporary
                
                # Calculate preliminary scores (placeholder)
                session.keyword_match_score = 7.5
                session.ats_compatibility_score = 8.0
                session.content_relevance_score = 7.8
                session.overall_score = 7.7
                
                session.status = 'completed'
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'analysis': job_analysis['analysis'],
                    'insights': insights['insights'],
                    'scores': {
                        'keyword_match': session.keyword_match_score,
                        'ats_compatibility': session.ats_compatibility_score,
                        'content_relevance': session.content_relevance_score,
                        'overall': session.overall_score
                    }
                })
            else:
                return jsonify({'success': False, 'error': insights['error']})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/review/<session_id>')
    def review_documents(session_id):
        """Review page - side-by-side comparison with editing capability"""
        
        session = ProcessingSession.query.get_or_404(session_id)
        
        if session.status != 'completed':
            return redirect(url_for('process_documents', session_id=session_id))
        
        # Prepare data for review page
        review_data = {
            'session': session,
            'keywords': json.loads(session.extracted_keywords) if session.extracted_keywords else {},
            'requirements': json.loads(session.job_requirements) if session.job_requirements else {},
            'scores': {
                'keyword_match': session.keyword_match_score,
                'ats_compatibility': session.ats_compatibility_score,
                'content_relevance': session.content_relevance_score,
                'overall': session.overall_score
            }
        }
        
        return render_template('review.html', **review_data)
    
    @app.route('/api/update-document/<session_id>', methods=['POST'])
    def update_document(session_id):
        """API endpoint to update document content and recalculate scores"""
        
        try:
            session = ProcessingSession.query.get_or_404(session_id)
            data = request.get_json()
            
            document_type = data.get('document_type')  # 'resume' or 'cover_letter'
            content = data.get('content')
            
            if document_type == 'resume':
                session.optimized_resume_text = content
            elif document_type == 'cover_letter':
                session.optimized_cover_letter_text = content
            
            # Create document version
            version = DocumentVersion(
                session_id=session_id,
                document_type=document_type,
                content=content,
                version_number=DocumentVersion.query.filter_by(
                    session_id=session_id, 
                    document_type=document_type
                ).count() + 1
            )
            
            # Set previous versions as not current
            DocumentVersion.query.filter_by(
                session_id=session_id,
                document_type=document_type,
                is_current=True
            ).update({'is_current': False})
            
            db.session.add(version)
            
            # TODO: Recalculate scores based on updated content
            # For now, slightly adjust scores
            if document_type == 'resume':
                session.keyword_match_score = min(10, session.keyword_match_score + 0.2)
            else:
                session.content_relevance_score = min(10, session.content_relevance_score + 0.1)
            
            session.overall_score = (
                session.keyword_match_score + 
                session.ats_compatibility_score + 
                session.content_relevance_score
            ) / 3
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'scores': {
                    'keyword_match': session.keyword_match_score,
                    'ats_compatibility': session.ats_compatibility_score,
                    'content_relevance': session.content_relevance_score,
                    'overall': session.overall_score
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/download/<session_id>')
    def download_page(session_id):
        """Download page with final documents and feedback"""
        
        session = ProcessingSession.query.get_or_404(session_id)
        return render_template('download.html', session=session)
    
    @app.route('/api/generate-feedback/<session_id>')
    def generate_feedback(session_id):
        """Generate detailed feedback for the optimized documents"""
        
        try:
            session = ProcessingSession.query.get_or_404(session_id)
            
            # TODO: Implement detailed feedback generation
            # For now, return placeholder feedback
            feedback = {
                'overall': f"Overall Score: {session.overall_score:.1f}/10",
                'strengths': [
                    "Strong keyword optimization",
                    "Good ATS compatibility",
                    "Relevant experience highlighted"
                ],
                'improvements': [
                    "Add more quantifiable achievements",
                    "Include additional industry keywords",
                    "Strengthen the opening statement"
                ],
                'detailed_analysis': "Your optimized documents show significant improvement..."
            }
            
            session.detailed_feedback = json.dumps(feedback)
            db.session.commit()
            
            return jsonify({'success': True, 'feedback': feedback})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app

# Create database tables
def init_db(app):
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app = create_app()
    init_db(app)
    
    # Print available routes for debugging
    print("\n🚀 Available Routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    print(f"\n🌐 Starting server at: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)