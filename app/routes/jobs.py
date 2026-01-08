from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for

from app import db
from app.models import JobRun, JobStatus, Query
from app.services.chatgpt_runner import ChatGPTRunner

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/jobs')
def list_jobs():
    """List all job runs."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    jobs = JobRun.query.order_by(JobRun.started_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'jobs': [j.to_dict() for j in jobs.items],
            'total': jobs.total,
            'page': jobs.page,
            'pages': jobs.pages
        })

    return render_template('jobs.html', jobs=jobs)


@jobs_bp.route('/jobs/<int:job_id>')
def get_job(job_id):
    """Get details for a specific job run."""
    job = JobRun.query.get_or_404(job_id)

    # Get citations for this job
    citations = job.citations.order_by('query_id', 'position').all()

    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'job': job.to_dict(),
            'citations': [c.to_dict() for c in citations]
        })

    return render_template('job_detail.html', job=job, citations=citations)


@jobs_bp.route('/jobs/run', methods=['POST'])
def run_job():
    """Trigger a new citation collection job."""
    data = request.get_json() if request.is_json else {}

    # Get optional query IDs filter
    query_ids = data.get('query_ids')

    try:
        runner = ChatGPTRunner()

        if query_ids:
            job = runner.run_collection_job(query_ids=query_ids)
        else:
            job = runner.run_collection_job()

        if request.is_json:
            return jsonify(job.to_dict()), 201

        flash(f'Job completed: {job.citations_found} citations from {job.queries_processed} queries', 'success')

    except ValueError as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(str(e), 'error')

    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Job failed: {str(e)}', 'error')

    return redirect(url_for('jobs.list_jobs'))


@jobs_bp.route('/jobs/run/<int:query_id>', methods=['POST'])
def run_single_query_job(query_id):
    """Run collection job for a single query."""
    query = Query.query.get_or_404(query_id)

    try:
        runner = ChatGPTRunner()
        job = runner.run_single_query_job(query_id)

        if request.is_json:
            return jsonify(job.to_dict()), 201

        flash(f'Job completed: {job.citations_found} citations found', 'success')

    except ValueError as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(str(e), 'error')

    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Job failed: {str(e)}', 'error')

    return redirect(url_for('queries.get_query', query_id=query_id))


@jobs_bp.route('/jobs/<int:job_id>/retry', methods=['POST'])
def retry_job(job_id):
    """Retry a failed job with the same queries."""
    original_job = JobRun.query.get_or_404(job_id)

    if original_job.status != JobStatus.FAILED:
        if request.is_json:
            return jsonify({'error': 'Can only retry failed jobs'}), 400
        flash('Can only retry failed jobs', 'error')
        return redirect(url_for('jobs.get_job', job_id=job_id))

    # Get query IDs from original job's citations
    query_ids = db.session.query(Query.id).join(
        original_job.citations
    ).distinct().all()
    query_ids = [q[0] for q in query_ids]

    if not query_ids:
        # If no citations were created, run all active queries
        query_ids = None

    try:
        runner = ChatGPTRunner()
        job = runner.run_collection_job(query_ids=query_ids)

        if request.is_json:
            return jsonify(job.to_dict()), 201

        flash(f'Retry completed: {job.citations_found} citations from {job.queries_processed} queries', 'success')

    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Retry failed: {str(e)}', 'error')

    return redirect(url_for('jobs.list_jobs'))
