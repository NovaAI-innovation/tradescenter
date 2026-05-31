from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    
    # Detailed ratings
    quality_rating = db.Column(db.Integer)  # 1-5
    communication_rating = db.Column(db.Integer)  # 1-5
    timeliness_rating = db.Column(db.Integer)  # 1-5
    professionalism_rating = db.Column(db.Integer)  # 1-5
    value_rating = db.Column(db.Integer)  # 1-5
    
    # Review metadata
    verified_project = db.Column(db.Boolean, default=False)
    helpful_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref=db.backref('review', uselist=False))
    client = db.relationship('User', backref=db.backref('reviews_written', lazy=True))
    response = db.relationship('ReviewResponse', backref='review', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Review {self.id} - {self.rating} stars>'

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'contractor_id': self.contractor_id,
            'client_id': self.client_id,
            'rating': self.rating,
            'title': self.title,
            'comment': self.comment,
            'quality_rating': self.quality_rating,
            'communication_rating': self.communication_rating,
            'timeliness_rating': self.timeliness_rating,
            'professionalism_rating': self.professionalism_rating,
            'value_rating': self.value_rating,
            'verified_project': self.verified_project,
            'helpful_votes': self.helpful_votes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ReviewResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'), nullable=False)
    response_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'review_id': self.review_id,
            'contractor_id': self.contractor_id,
            'response_text': self.response_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

