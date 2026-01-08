import pytest
from app import create_app, db
from app.models import Query, Citation, JobRun, IntentType, JobStatus


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_query(app):
    """Create a sample query."""
    with app.app_context():
        query = Query(
            query_text="best betting apps australia 2025",
            intent_type=IntentType.COMMERCIAL,
            category="sports betting",
            is_active=True
        )
        db.session.add(query)
        db.session.commit()
        return query.id


@pytest.fixture
def sample_job_run(app):
    """Create a sample job run."""
    with app.app_context():
        job = JobRun(
            status=JobStatus.COMPLETED,
            queries_processed=5,
            citations_found=15
        )
        db.session.add(job)
        db.session.commit()
        return job.id


@pytest.fixture
def sample_citation(app, sample_query, sample_job_run):
    """Create a sample citation."""
    with app.app_context():
        citation = Citation(
            job_run_id=sample_job_run,
            query_id=sample_query,
            url="https://www.example.com.au/betting-apps",
            domain="example.com.au",
            page_type="article",
            position=1,
            snippet="Best betting apps in Australia..."
        )
        db.session.add(citation)
        db.session.commit()
        return citation.id
