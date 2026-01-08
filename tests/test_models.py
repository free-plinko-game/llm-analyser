import pytest
from app import db
from app.models import Query, Citation, JobRun, IntentType, JobStatus


class TestQueryModel:
    """Tests for Query model."""

    def test_create_query(self, app):
        """Test creating a query."""
        with app.app_context():
            query = Query(
                query_text="test query",
                intent_type=IntentType.INFORMATIONAL,
                category="test category"
            )
            db.session.add(query)
            db.session.commit()

            assert query.id is not None
            assert query.query_text == "test query"
            assert query.intent_type == IntentType.INFORMATIONAL
            assert query.is_active is True

    def test_query_to_dict(self, app, sample_query):
        """Test query serialization."""
        with app.app_context():
            query = Query.query.get(sample_query)
            data = query.to_dict()

            assert data['id'] == sample_query
            assert data['query_text'] == "best betting apps australia 2025"
            assert data['intent_type'] == 'commercial'
            assert data['category'] == "sports betting"
            assert data['is_active'] is True


class TestCitationModel:
    """Tests for Citation model."""

    def test_create_citation(self, app, sample_query, sample_job_run):
        """Test creating a citation."""
        with app.app_context():
            citation = Citation(
                job_run_id=sample_job_run,
                query_id=sample_query,
                url="https://test.com/page",
                domain="test.com",
                position=1
            )
            db.session.add(citation)
            db.session.commit()

            assert citation.id is not None
            assert citation.domain == "test.com"

    def test_citation_to_dict(self, app, sample_citation):
        """Test citation serialization."""
        with app.app_context():
            citation = Citation.query.get(sample_citation)
            data = citation.to_dict()

            assert data['domain'] == "example.com.au"
            assert data['position'] == 1
            assert data['page_type'] == "article"


class TestJobRunModel:
    """Tests for JobRun model."""

    def test_create_job_run(self, app):
        """Test creating a job run."""
        with app.app_context():
            job = JobRun(status=JobStatus.PENDING)
            db.session.add(job)
            db.session.commit()

            assert job.id is not None
            assert job.status == JobStatus.PENDING
            assert job.queries_processed == 0

    def test_job_run_to_dict(self, app, sample_job_run):
        """Test job run serialization."""
        with app.app_context():
            job = JobRun.query.get(sample_job_run)
            data = job.to_dict()

            assert data['status'] == 'completed'
            assert data['queries_processed'] == 5
            assert data['citations_found'] == 15
