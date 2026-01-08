import pytest
from datetime import datetime, timedelta
from app import db
from app.models import Query, Citation, JobRun, IntentType, JobStatus
from app.services.domain_analyser import DomainAnalyser


class TestDomainAnalyser:
    """Tests for DomainAnalyser service."""

    @pytest.fixture
    def populated_db(self, app):
        """Create test data."""
        with app.app_context():
            # Create queries
            q1 = Query(
                query_text="best betting apps",
                intent_type=IntentType.COMMERCIAL,
                category="sports betting"
            )
            q2 = Query(
                query_text="how odds work",
                intent_type=IntentType.INFORMATIONAL,
                category="sports betting"
            )
            q3 = Query(
                query_text="poker sites review",
                intent_type=IntentType.COMMERCIAL,
                category="poker"
            )
            db.session.add_all([q1, q2, q3])
            db.session.commit()

            # Create job
            job = JobRun(status=JobStatus.COMPLETED)
            db.session.add(job)
            db.session.commit()

            # Create citations
            citations = [
                Citation(job_run_id=job.id, query_id=q1.id, url="https://sportsbet.com.au", domain="sportsbet.com.au", position=1, page_type="homepage"),
                Citation(job_run_id=job.id, query_id=q1.id, url="https://bet365.com.au/app", domain="bet365.com.au", position=2, page_type="product"),
                Citation(job_run_id=job.id, query_id=q1.id, url="https://sportsbet.com.au/promo", domain="sportsbet.com.au", position=3, page_type="product"),
                Citation(job_run_id=job.id, query_id=q2.id, url="https://bet365.com.au/help", domain="bet365.com.au", position=1, page_type="guide"),
                Citation(job_run_id=job.id, query_id=q3.id, url="https://pokerstars.com.au", domain="pokerstars.com.au", position=1, page_type="homepage"),
            ]
            db.session.add_all(citations)
            db.session.commit()

            yield

    def test_get_top_domains(self, app, populated_db):
        """Test getting top domains."""
        with app.app_context():
            results = DomainAnalyser.get_top_domains(limit=10)

            assert len(results) == 3
            # sportsbet appears twice, bet365 twice, pokerstars once
            assert results[0]['domain'] in ['sportsbet.com.au', 'bet365.com.au']
            assert results[0]['count'] == 2

    def test_get_top_domains_by_intent(self, app, populated_db):
        """Test filtering by intent type."""
        with app.app_context():
            results = DomainAnalyser.get_top_domains(
                limit=10,
                intent_type=IntentType.COMMERCIAL
            )

            # Only commercial queries
            assert len(results) >= 1
            domains = [r['domain'] for r in results]
            assert 'sportsbet.com.au' in domains

    def test_get_top_domains_by_category(self, app, populated_db):
        """Test filtering by category."""
        with app.app_context():
            results = DomainAnalyser.get_top_domains(
                limit=10,
                category="poker"
            )

            assert len(results) == 1
            assert results[0]['domain'] == 'pokerstars.com.au'

    def test_get_domain_by_intent(self, app, populated_db):
        """Test breakdown by intent."""
        with app.app_context():
            results = DomainAnalyser.get_domain_by_intent(limit=5)

            assert 'commercial' in results
            assert 'informational' in results
            assert len(results['commercial']) >= 1

    def test_get_domain_by_category(self, app, populated_db):
        """Test breakdown by category."""
        with app.app_context():
            results = DomainAnalyser.get_domain_by_category(limit=5)

            assert 'sports betting' in results
            assert 'poker' in results

    def test_get_position_stats(self, app, populated_db):
        """Test position statistics."""
        with app.app_context():
            stats = DomainAnalyser.get_position_stats()

            assert stats['total_citations'] == 5
            assert stats['avg_position'] is not None
            assert 'distribution' in stats

    def test_get_position_stats_for_domain(self, app, populated_db):
        """Test position stats for specific domain."""
        with app.app_context():
            stats = DomainAnalyser.get_position_stats(domain='sportsbet.com.au')

            assert stats['total_citations'] == 2

    def test_get_page_type_breakdown(self, app, populated_db):
        """Test page type breakdown."""
        with app.app_context():
            results = DomainAnalyser.get_page_type_breakdown()

            page_types = {r['page_type']: r['count'] for r in results}
            assert 'homepage' in page_types
            assert 'product' in page_types

    def test_get_summary_stats(self, app, populated_db):
        """Test summary statistics."""
        with app.app_context():
            stats = DomainAnalyser.get_summary_stats()

            assert stats['total_citations'] == 5
            assert stats['unique_domains'] == 3
            assert stats['active_queries'] == 3
            assert stats['total_jobs'] == 1

    def test_export_to_dataframe(self, app, populated_db):
        """Test DataFrame export."""
        with app.app_context():
            df = DomainAnalyser.export_to_dataframe()

            assert len(df) == 5
            assert 'domain' in df.columns
            assert 'query_text' in df.columns
            assert 'intent_type' in df.columns

    def test_get_citation_trends(self, app, populated_db):
        """Test citation trends."""
        with app.app_context():
            trends = DomainAnalyser.get_citation_trends(days=30)

            # Should have at least one data point for today
            assert len(trends) >= 1
            assert all('date' in t and 'count' in t for t in trends)
