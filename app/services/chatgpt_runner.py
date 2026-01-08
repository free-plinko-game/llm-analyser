import time
import logging
from datetime import datetime
from typing import Optional, List, Dict
from flask import current_app
from openai import OpenAI

from app import db
from app.models import Query, Citation, JobRun, JobStatus
from app.services.citation_parser import CitationParser

logger = logging.getLogger(__name__)


class ChatGPTRunner:
    """Runs queries against ChatGPT API with web search and extracts citations."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or current_app.config.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        self.client = OpenAI(api_key=self.api_key)
        self.rate_limit_delay = current_app.config.get('RATE_LIMIT_DELAY_SECONDS', 6)

    def run_query(self, query: Query) -> List[Dict]:
        """
        Run a single query against ChatGPT with web search enabled.

        Returns list of citation dicts extracted from the response.
        """
        try:
            # Use the responses API with web_search tool
            response = self.client.responses.create(
                model="gpt-4o",
                tools=[{"type": "web_search"}],
                input=query.query_text
            )

            citations = []

            # Extract citations from response
            for output in response.output:
                if output.type == "message":
                    for content in output.content:
                        if hasattr(content, 'annotations') and content.annotations:
                            # Use structured annotations from web search
                            citations.extend(
                                CitationParser.parse_web_search_annotations(
                                    [a.__dict__ for a in content.annotations]
                                )
                            )
                        elif hasattr(content, 'text'):
                            # Fallback to text parsing
                            citations.extend(
                                CitationParser.parse_response(content.text)
                            )

            return citations

        except Exception as e:
            logger.error(f"Error running query {query.id}: {str(e)}")
            raise

    def run_collection_job(self, query_ids: Optional[List[int]] = None) -> JobRun:
        """
        Run a citation collection job for active queries.

        Args:
            query_ids: Optional list of specific query IDs to run.
                      If None, runs all active queries.

        Returns:
            JobRun instance with results.
        """
        # Create job run record
        job_run = JobRun(status=JobStatus.RUNNING, started_at=datetime.utcnow())
        db.session.add(job_run)
        db.session.commit()

        errors = []
        queries_processed = 0
        citations_found = 0

        try:
            # Get queries to process
            if query_ids:
                queries = Query.query.filter(Query.id.in_(query_ids)).all()
            else:
                queries = Query.query.filter_by(is_active=True).all()

            for query in queries:
                try:
                    logger.info(f"Processing query {query.id}: {query.query_text[:50]}...")

                    # Run query and get citations
                    citation_data = self.run_query(query)

                    # Store citations
                    for data in citation_data:
                        citation = Citation(
                            job_run_id=job_run.id,
                            query_id=query.id,
                            url=data['url'],
                            domain=data['domain'],
                            page_type=data.get('page_type'),
                            position=data['position'],
                            snippet=data.get('snippet')
                        )
                        db.session.add(citation)
                        citations_found += 1

                    queries_processed += 1
                    db.session.commit()

                    # Rate limiting
                    time.sleep(self.rate_limit_delay)

                except Exception as e:
                    error_msg = f"Query {query.id} failed: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            # Update job run with results
            job_run.status = JobStatus.COMPLETED
            job_run.completed_at = datetime.utcnow()
            job_run.queries_processed = queries_processed
            job_run.citations_found = citations_found
            if errors:
                job_run.error_log = '\n'.join(errors)

        except Exception as e:
            job_run.status = JobStatus.FAILED
            job_run.completed_at = datetime.utcnow()
            job_run.error_log = str(e)
            logger.error(f"Job run failed: {str(e)}")

        db.session.commit()
        return job_run

    def run_single_query_job(self, query_id: int) -> JobRun:
        """Run collection job for a single query."""
        return self.run_collection_job(query_ids=[query_id])
