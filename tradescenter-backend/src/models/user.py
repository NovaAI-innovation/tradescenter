from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .auth import PasswordManager

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    user_type = db.Column(db.String(20), nullable=False, default='homeowner')  # 'homeowner', 'contractor', 'admin'
    profile_image = db.Column(db.String(255))
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    contractor_profile = db.relationship('Contractor', backref='user', uselist=False)
    projects_created = db.relationship('Project', foreign_keys='Project.client_id', backref='client')
    reviews_written = db.relationship('Review', foreign_keys='Review.client_id', backref='reviewer')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient')
    
    def __init__(self, email, password, first_name, last_name, **kwargs):
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def check_password(self, password):
        """Verify password against stored hash"""
        return PasswordManager.verify_password(self.password_hash, password)
    
    def set_password(self, password):
        """Set new password"""
        self.password_hash = PasswordManager.hash_password(password)
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_contractor(self):
        """Check if user is a contractor"""
        return self.user_type == 'contractor'
    
    @property
    def is_homeowner(self):
        """Check if user is a homeowner"""
        return self.user_type == 'homeowner'
    
    @property
    def is_admin(self):
        """Check if user is an admin"""
        return self.user_type == 'admin'
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'user_type': self.user_type,
            'profile_image': self.profile_image,
            'bio': self.bio,
            'location': self.location,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find user by ID"""
        return cls.query.get(user_id)
    
    def save(self):
        """Save user to database"""
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Delete user from database"""
        db.session.delete(self)
        db.session.commit()

