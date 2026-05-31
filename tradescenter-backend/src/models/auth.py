from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import jwt
from flask import current_app

class AuthToken:
    """Authentication token management"""
    
    @staticmethod
    def generate_token(user_id, expires_in=3600):
        """Generate JWT token for user authentication"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, current_app.config.get('SECRET_KEY', 'dev-secret'), algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, current_app.config.get('SECRET_KEY', 'dev-secret'), algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class PasswordManager:
    """Password hashing and verification"""
    
    @staticmethod
    def hash_password(password):
        """Hash password using werkzeug"""
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify password against hash"""
        return check_password_hash(password_hash, password)

class SessionManager:
    """User session management"""
    
    def __init__(self):
        self.active_sessions = {}
    
    def create_session(self, user_id):
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        return session_id
    
    def get_session(self, session_id):
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def update_activity(self, session_id):
        """Update last activity timestamp"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['last_activity'] = datetime.utcnow()
    
    def delete_session(self, session_id):
        """Delete session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def cleanup_expired_sessions(self, max_age_hours=24):
        """Remove expired sessions"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_sessions = [
            sid for sid, session in self.active_sessions.items()
            if session['last_activity'] < cutoff
        ]
        for sid in expired_sessions:
            del self.active_sessions[sid]

# Global session manager instance
session_manager = SessionManager()

