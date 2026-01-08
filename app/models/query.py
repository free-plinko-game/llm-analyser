import enum
from datetime import datetime
from app import db


class IntentType(enum.Enum):
    """Search intent types for categorizing queries."""
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    TRANSACTIONAL = "transactional"
    COMMERCIAL = "commercial"


class Query(db.Model):
    """Model for storing search queries to analyse."""
    __tablename__ = 'queries'

    id = db.Column(db.Integer, primary_key=True)
    query_text = db.Column(db.String(500), nullable=False)
    intent_type = db.Column(db.Enum(IntentType), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    citations = db.relationship('Citation', backref='query', lazy='dynamic')

    def __repr__(self):
        return f'<Query {self.id}: {self.query_text[:50]}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'query_text': self.query_text,
            'intent_type': self.intent_type.value,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'citation_count': self.citations.count()
        }
