from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
import pandas as pd
from sqlalchemy import func

from app import db
from app.models import Citation, Query, JobRun, IntentType, JobStatus


class DomainAnalyser:
    """Analyses citation patterns across domains, intents, and time periods."""

    @staticmethod
    def get_top_domains(
        limit: int = 20,
        intent_type: Optional[IntentType] = None,
        category: Optional[str] = None,
        days: Optional[int] = None
    ) -> List[Dict]:
        """
        Get top cited domains with optional filters.

        Args:
            limit: Maximum number of domains to return
            intent_type: Filter by intent type
            category: Filter by business category
            days: Only include citations from last N days

        Returns:
            List of dicts with domain, count, and percentage
        """
        query = db.session.query(
            Citation.domain,
            func.count(Citation.id).label('count')
        )

        # Apply filters
        if intent_type or category:
            query = query.join(Query)
            if intent_type:
                query = query.filter(Query.intent_type == intent_type)
            if category:
                query = query.filter(Query.category == category)

        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Citation.created_at >= cutoff)

        results = query.group_by(Citation.domain) \
            .order_by(func.count(Citation.id).desc()) \
            .limit(limit) \
            .all()

        # Calculate total for percentages
        total = sum(r.count for r in results)

        return [
            {
                'domain': r.domain,
                'count': r.count,
                'percentage': round(r.count / total * 100, 2) if total > 0 else 0
            }
            for r in results
        ]

    @staticmethod
    def get_domain_by_intent(limit: int = 10) -> Dict[str, List[Dict]]:
        """
        Get top domains broken down by intent type.

        Returns:
            Dict mapping intent types to lists of top domains
        """
        results = {}

        for intent in IntentType:
            results[intent.value] = DomainAnalyser.get_top_domains(
                limit=limit,
                intent_type=intent
            )

        return results

    @staticmethod
    def get_domain_by_category(limit: int = 10) -> Dict[str, List[Dict]]:
        """
        Get top domains broken down by business category.

        Returns:
            Dict mapping categories to lists of top domains
        """
        # Get unique categories
        categories = db.session.query(Query.category).distinct().all()
        categories = [c[0] for c in categories]

        results = {}
        for category in categories:
            results[category] = DomainAnalyser.get_top_domains(
                limit=limit,
                category=category
            )

        return results

    @staticmethod
    def get_citation_trends(
        domain: Optional[str] = None,
        days: int = 30,
        granularity: str = 'day'
    ) -> List[Dict]:
        """
        Get citation count trends over time.

        Args:
            domain: Optional specific domain to track
            days: Number of days to look back
            granularity: 'day' or 'week'

        Returns:
            List of dicts with date and count
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = db.session.query(
            func.date(Citation.created_at).label('date'),
            func.count(Citation.id).label('count')
        ).filter(Citation.created_at >= cutoff)

        if domain:
            query = query.filter(Citation.domain == domain)

        results = query.group_by(func.date(Citation.created_at)) \
            .order_by(func.date(Citation.created_at)) \
            .all()

        return [
            {'date': str(r.date), 'count': r.count}
            for r in results
        ]

    @staticmethod
    def get_position_stats(domain: Optional[str] = None) -> Dict:
        """
        Get statistics about citation positions.

        Args:
            domain: Optional specific domain to analyse

        Returns:
            Dict with avg_position, position_distribution, etc.
        """
        query = db.session.query(Citation.position)
        if domain:
            query = query.filter(Citation.domain == domain)

        positions = [r[0] for r in query.all()]

        if not positions:
            return {'avg_position': None, 'distribution': {}}

        avg = sum(positions) / len(positions)

        # Position distribution
        distribution = defaultdict(int)
        for pos in positions:
            if pos == 1:
                distribution['first'] += 1
            elif pos <= 3:
                distribution['top_3'] += 1
            elif pos <= 5:
                distribution['top_5'] += 1
            else:
                distribution['other'] += 1

        return {
            'avg_position': round(avg, 2),
            'total_citations': len(positions),
            'distribution': dict(distribution)
        }

    @staticmethod
    def get_page_type_breakdown(domain: Optional[str] = None) -> List[Dict]:
        """
        Get breakdown of page types being cited.

        Args:
            domain: Optional specific domain to analyse

        Returns:
            List of dicts with page_type and count
        """
        query = db.session.query(
            Citation.page_type,
            func.count(Citation.id).label('count')
        )

        if domain:
            query = query.filter(Citation.domain == domain)

        results = query.group_by(Citation.page_type) \
            .order_by(func.count(Citation.id).desc()) \
            .all()

        return [
            {'page_type': r.page_type or 'unknown', 'count': r.count}
            for r in results
        ]

    @staticmethod
    def export_to_dataframe() -> pd.DataFrame:
        """
        Export all citation data to a pandas DataFrame for analysis.

        Returns:
            DataFrame with all citation data joined with query info
        """
        query = db.session.query(
            Citation.id,
            Citation.url,
            Citation.domain,
            Citation.page_type,
            Citation.position,
            Citation.snippet,
            Citation.created_at.label('citation_date'),
            Query.query_text,
            Query.intent_type,
            Query.category,
            JobRun.id.label('job_id'),
            JobRun.started_at.label('job_date')
        ).join(Query).join(JobRun)

        results = query.all()

        return pd.DataFrame([
            {
                'citation_id': r.id,
                'url': r.url,
                'domain': r.domain,
                'page_type': r.page_type,
                'position': r.position,
                'snippet': r.snippet,
                'citation_date': r.citation_date,
                'query_text': r.query_text,
                'intent_type': r.intent_type.value if r.intent_type else None,
                'category': r.category,
                'job_id': r.job_id,
                'job_date': r.job_date
            }
            for r in results
        ])

    @staticmethod
    def get_summary_stats() -> Dict:
        """
        Get high-level summary statistics.

        Returns:
            Dict with overall stats about citations, domains, etc.
        """
        total_citations = db.session.query(Citation).count()
        unique_domains = db.session.query(
            func.count(func.distinct(Citation.domain))
        ).scalar()
        total_queries = db.session.query(Query).filter_by(is_active=True).count()
        total_jobs = db.session.query(JobRun).count()
        completed_jobs = db.session.query(JobRun).filter_by(status=JobStatus.COMPLETED).count()

        # Get most recent job
        latest_job = db.session.query(JobRun).order_by(JobRun.started_at.desc()).first()

        return {
            'total_citations': total_citations,
            'unique_domains': unique_domains,
            'active_queries': total_queries,
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'latest_job': latest_job.to_dict() if latest_job else None
        }
