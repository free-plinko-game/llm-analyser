import enum
from datetime import datetime
from app import db


class JobStatus(enum.Enum):
    """Status of a job run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRun(db.Model):
    """Model for tracking citation collection job executions."""
    __tablename__ = 'job_runs'

    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(JobStatus), default=JobStatus.PENDING)
    queries_processed = db.Column(db.Integer, default=0)
    citations_found = db.Column(db.Integer, default=0)
    error_log = db.Column(db.Text, nullable=True)

    # Relationships
    citations = db.relationship('Citation', backref='job_run', lazy='dynamic')

    def __repr__(self):
        return f'<JobRun {self.id}: {self.status.value}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status.value,
            'queries_processed': self.queries_processed,
            'citations_found': self.citations_found,
            'error_log': self.error_log,
            'duration_seconds': self._calculate_duration()
        }

    def _calculate_duration(self):
        """Calculate job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
