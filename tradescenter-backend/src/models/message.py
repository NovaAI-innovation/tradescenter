from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='text')  # text, system, notification
    read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_messages', lazy=True))
    attachments = db.relationship('MessageAttachment', backref='message', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Message {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'subject': self.subject,
            'content': self.content,
            'message_type': self.message_type,
            'read': self.read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MessageAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participant2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    last_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    participant1 = db.relationship('User', foreign_keys=[participant1_id])
    participant2 = db.relationship('User', foreign_keys=[participant2_id])
    last_message = db.relationship('Message', foreign_keys=[last_message_id])

    def to_dict(self):
        return {
            'id': self.id,
            'participant1_id': self.participant1_id,
            'participant2_id': self.participant2_id,
            'project_id': self.project_id,
            'last_message_id': self.last_message_id,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

