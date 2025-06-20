from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class ProcessingSession(db.Model):
    __tablename__ = 'processing_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, completed, failed
    
    # Original Documents
    job_description = db.Column(db.Text)
    original_resume_path = db.Column(db.String(255))
    original_cover_letter_path = db.Column(db.String(255))
    
    # Extracted Text
    job_description_text = db.Column(db.Text)
    original_resume_text = db.Column(db.Text)
    original_cover_letter_text = db.Column(db.Text)
    
    # Optimized Content
    optimized_resume_text = db.Column(db.Text)
    optimized_cover_letter_text = db.Column(db.Text)
    
    # Analysis Results
    extracted_keywords = db.Column(db.Text)  # JSON string
    job_requirements = db.Column(db.Text)   # JSON string
    
    # Scores
    keyword_match_score = db.Column(db.Float)
    ats_compatibility_score = db.Column(db.Float)
    content_relevance_score = db.Column(db.Float)
    overall_score = db.Column(db.Float)
    
    # Feedback
    detailed_feedback = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'scores': {
                'keyword_match': self.keyword_match_score,
                'ats_compatibility': self.ats_compatibility_score,
                'content_relevance': self.content_relevance_score,
                'overall': self.overall_score
            }
        }

class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('processing_sessions.id'), nullable=False)
    document_type = db.Column(db.String(20), nullable=False)  # resume, cover_letter
    version_number = db.Column(db.Integer, default=1)
    content = db.Column(db.Text)
    is_current = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    session = db.relationship('ProcessingSession', backref=db.backref('document_versions', lazy=True))

class FeedbackHistory(db.Model):
    __tablename__ = 'feedback_history'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('processing_sessions.id'), nullable=False)
    feedback_type = db.Column(db.String(30))  # overall, resume, cover_letter, ats
    score = db.Column(db.Float)
    feedback_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    session = db.relationship('ProcessingSession', backref=db.backref('feedback_history', lazy=True))