from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Contractor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    business_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(200))
    license_number = db.Column(db.String(100))
    insurance_info = db.Column(db.Text)
    service_areas = db.Column(db.Text)  # JSON string of areas
    specialties = db.Column(db.Text)    # JSON string of specialties
    verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    total_projects = db.Column(db.Integer, default=0)
    response_time_hours = db.Column(db.Integer, default=24)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('contractor_profile', uselist=False))
    projects = db.relationship('Project', backref='contractor', lazy=True)
    reviews = db.relationship('Review', backref='contractor', lazy=True)

    def __repr__(self):
        return f'<Contractor {self.business_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'business_name': self.business_name,
            'description': self.description,
            'phone': self.phone,
            'website': self.website,
            'license_number': self.license_number,
            'insurance_info': self.insurance_info,
            'service_areas': self.service_areas,
            'specialties': self.specialties,
            'verified': self.verified,
            'rating': self.rating,
            'total_reviews': self.total_reviews,
            'total_projects': self.total_projects,
            'response_time_hours': self.response_time_hours,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

