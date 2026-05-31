from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    budget_min = db.Column(db.Float)
    budget_max = db.Column(db.Float)
    status = db.Column(db.String(50), default='open')  # open, assigned, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = db.relationship('User', backref=db.backref('client_projects', lazy=True))
    milestones = db.relationship('ProjectMilestone', backref='project', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('ProjectFile', backref='project', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='project', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'contractor_id': self.contractor_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'location': self.location,
            'budget_min': self.budget_min,
            'budget_max': self.budget_max,
            'status': self.status,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProjectMilestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed
    due_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'order_index': self.order_index,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ProjectFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50))  # image, document, video, etc.
    file_size = db.Column(db.Integer)
    file_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    uploader = db.relationship('User', backref=db.backref('uploaded_files', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'uploader_id': self.uploader_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

