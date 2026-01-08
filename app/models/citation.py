from datetime import datetime
from app import db


class Citation(db.Model):
    """Model for storing citations extracted from ChatGPT responses."""
    __tablename__ = 'citations'

    id = db.Column(db.Integer, primary_key=True)
    job_run_id = db.Column(db.Integer, db.ForeignKey('job_runs.id'), nullable=False)
    query_id = db.Column(db.Integer, db.ForeignKey('queries.id'), nullable=False)
    url = db.Column(db.String(2000), nullable=False)
    domain = db.Column(db.String(255), nullable=False, index=True)
    page_type = db.Column(db.String(50), nullable=True)
    position = db.Column(db.Integer, nullable=False)
    snippet = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Index for faster domain queries
    __table_args__ = (
        db.Index('ix_citations_domain_created', 'domain', 'created_at'),
    )

    def __repr__(self):
        return f'<Citation {self.id}: {self.domain}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'job_run_id': self.job_run_id,
            'query_id': self.query_id,
            'url': self.url,
            'domain': self.domain,
            'page_type': self.page_type,
            'position': self.position,
            'snippet': self.snippet,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
