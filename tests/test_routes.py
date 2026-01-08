import pytest
import json
from app import db
from app.models import Query, IntentType


class TestQueriesRoutes:
    """Tests for query routes."""

    def test_list_queries_html(self, client, sample_query):
        """Test listing queries returns HTML."""
        response = client.get('/queries')
        assert response.status_code == 200
        assert b'Query Bank' in response.data

    def test_list_queries_json(self, client, sample_query):
        """Test listing queries returns JSON."""
        response = client.get('/queries', headers={'Accept': 'application/json'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1

    def test_create_query_json(self, client, app):
        """Test creating a query via JSON."""
        response = client.post(
            '/queries',
            json={
                'query_text': 'new test query',
                'intent_type': 'informational',
                'category': 'test'
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['query_text'] == 'new test query'

    def test_create_query_form(self, client, app):
        """Test creating a query via form."""
        response = client.post(
            '/queries',
            data={
                'query_text': 'form test query',
                'intent_type': 'commercial',
                'category': 'sports betting'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Query added successfully' in response.data

    def test_create_query_missing_fields(self, client):
        """Test creating a query with missing fields."""
        response = client.post(
            '/queries',
            json={'query_text': 'incomplete'},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_delete_query(self, client, sample_query):
        """Test deleting a query."""
        response = client.delete(
            f'/queries/{sample_query}',
            headers={'Accept': 'application/json'}
        )
        assert response.status_code == 200

    def test_toggle_query(self, client, app, sample_query):
        """Test toggling query active status."""
        with app.app_context():
            query = Query.query.get(sample_query)
            original_status = query.is_active

        response = client.post(
            f'/queries/{sample_query}/toggle',
            headers={'Accept': 'application/json'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['is_active'] != original_status


class TestAnalysisRoutes:
    """Tests for analysis routes."""

    def test_dashboard(self, client):
        """Test dashboard loads."""
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Citation Analysis Dashboard' in response.data

    def test_dashboard_json(self, client):
        """Test dashboard JSON response."""
        response = client.get('/dashboard', headers={'Accept': 'application/json'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'stats' in data
        assert 'top_domains' in data

    def test_top_domains(self, client, sample_citation):
        """Test top domains endpoint."""
        response = client.get('/analysis/domains', headers={'Accept': 'application/json'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_export_empty(self, client):
        """Test export with no data."""
        response = client.get('/analysis/export')
        assert response.status_code == 404

    def test_export_csv(self, client, sample_citation):
        """Test CSV export."""
        response = client.get('/analysis/export?format=csv')
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'

    def test_export_json(self, client, sample_citation):
        """Test JSON export."""
        response = client.get('/analysis/export?format=json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)


class TestJobsRoutes:
    """Tests for job routes."""

    def test_list_jobs(self, client, sample_job_run):
        """Test listing jobs."""
        response = client.get('/jobs')
        assert response.status_code == 200
        assert b'Collection Jobs' in response.data

    def test_list_jobs_json(self, client, sample_job_run):
        """Test listing jobs JSON."""
        response = client.get('/jobs', headers={'Accept': 'application/json'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'jobs' in data
        assert len(data['jobs']) >= 1

    def test_get_job_detail(self, client, sample_job_run):
        """Test getting job details."""
        response = client.get(f'/jobs/{sample_job_run}')
        assert response.status_code == 200

    def test_get_job_detail_json(self, client, sample_job_run, sample_citation):
        """Test getting job details JSON."""
        response = client.get(
            f'/jobs/{sample_job_run}',
            headers={'Accept': 'application/json'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'job' in data
        assert 'citations' in data
