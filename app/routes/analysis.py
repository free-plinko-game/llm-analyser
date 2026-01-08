import io
import csv
from flask import Blueprint, request, jsonify, render_template, Response

from app.models import IntentType
from app.services.domain_analyser import DomainAnalyser

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/dashboard')
def dashboard():
    """Main analysis dashboard."""
    stats = DomainAnalyser.get_summary_stats()
    top_domains = DomainAnalyser.get_top_domains(limit=10)
    domains_by_intent = DomainAnalyser.get_domain_by_intent(limit=5)
    trends = DomainAnalyser.get_citation_trends(days=30)

    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'stats': stats,
            'top_domains': top_domains,
            'domains_by_intent': domains_by_intent,
            'trends': trends
        })

    return render_template(
        'dashboard.html',
        stats=stats,
        top_domains=top_domains,
        domains_by_intent=domains_by_intent,
        trends=trends
    )


@analysis_bp.route('/analysis')
def analysis_overview():
    """Redirect to dashboard."""
    return dashboard()


@analysis_bp.route('/analysis/domains')
def top_domains():
    """Get top cited domains with filtering options."""
    # Get filter parameters
    limit = request.args.get('limit', 20, type=int)
    intent = request.args.get('intent')
    category = request.args.get('category')
    days = request.args.get('days', type=int)

    intent_type = None
    if intent:
        try:
            intent_type = IntentType(intent)
        except ValueError:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Invalid intent type'}), 400

    results = DomainAnalyser.get_top_domains(
        limit=limit,
        intent_type=intent_type,
        category=category,
        days=days
    )

    if request.headers.get('Accept') == 'application/json':
        return jsonify(results)

    return render_template(
        'analysis_domains.html',
        domains=results,
        intent_types=[i.value for i in IntentType]
    )


@analysis_bp.route('/analysis/intent')
def domains_by_intent():
    """Get domain breakdown by intent type."""
    limit = request.args.get('limit', 10, type=int)
    results = DomainAnalyser.get_domain_by_intent(limit=limit)

    if request.headers.get('Accept') == 'application/json':
        return jsonify(results)

    return render_template('analysis_intent.html', data=results)


@analysis_bp.route('/analysis/category')
def domains_by_category():
    """Get domain breakdown by business category."""
    limit = request.args.get('limit', 10, type=int)
    results = DomainAnalyser.get_domain_by_category(limit=limit)

    if request.headers.get('Accept') == 'application/json':
        return jsonify(results)

    return render_template('analysis_category.html', data=results)


@analysis_bp.route('/analysis/trends')
def citation_trends():
    """Get citation trends over time."""
    domain = request.args.get('domain')
    days = request.args.get('days', 30, type=int)

    results = DomainAnalyser.get_citation_trends(domain=domain, days=days)

    if request.headers.get('Accept') == 'application/json':
        return jsonify(results)

    return render_template('analysis_trends.html', trends=results, domain=domain)


@analysis_bp.route('/analysis/domain/<domain>')
def domain_detail(domain):
    """Get detailed analysis for a specific domain."""
    position_stats = DomainAnalyser.get_position_stats(domain=domain)
    page_types = DomainAnalyser.get_page_type_breakdown(domain=domain)
    trends = DomainAnalyser.get_citation_trends(domain=domain, days=90)

    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'domain': domain,
            'position_stats': position_stats,
            'page_types': page_types,
            'trends': trends
        })

    return render_template(
        'analysis_domain_detail.html',
        domain=domain,
        position_stats=position_stats,
        page_types=page_types,
        trends=trends
    )


@analysis_bp.route('/analysis/export')
def export_data():
    """Export all citation data as CSV."""
    format = request.args.get('format', 'csv')

    df = DomainAnalyser.export_to_dataframe()

    if df.empty:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': 'No data to export'}), 404
        return "No data to export", 404

    if format == 'json':
        return jsonify(df.to_dict(orient='records'))

    # Default to CSV
    output = io.StringIO()
    df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=citation_export.csv'
        }
    )


@analysis_bp.route('/analysis/summary')
def summary_stats():
    """Get summary statistics."""
    stats = DomainAnalyser.get_summary_stats()

    if request.headers.get('Accept') == 'application/json':
        return jsonify(stats)

    return render_template('analysis_summary.html', stats=stats)
