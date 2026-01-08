import csv
import click
from flask import current_app
from flask.cli import with_appcontext

from app import db
from app.models import Query, IntentType
from app.services.chatgpt_runner import ChatGPTRunner
from app.services.domain_analyser import DomainAnalyser


def register_commands(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(collect_citations)
    app.cli.add_command(export_analysis)
    app.cli.add_command(add_query)
    app.cli.add_command(list_queries)
    app.cli.add_command(seed_demo_queries)


@click.command('collect-citations')
@click.option('--query-id', '-q', type=int, help='Run for specific query ID only')
@click.option('--category', '-c', help='Run only queries in this category')
@with_appcontext
def collect_citations(query_id, category):
    """Run a citation collection job."""
    try:
        runner = ChatGPTRunner()

        if query_id:
            click.echo(f"Running collection for query {query_id}...")
            job = runner.run_single_query_job(query_id)
        elif category:
            queries = Query.query.filter_by(category=category, is_active=True).all()
            query_ids = [q.id for q in queries]
            click.echo(f"Running collection for {len(query_ids)} queries in category '{category}'...")
            job = runner.run_collection_job(query_ids=query_ids)
        else:
            click.echo("Running collection for all active queries...")
            job = runner.run_collection_job()

        click.echo(f"\nJob completed!")
        click.echo(f"  Status: {job.status.value}")
        click.echo(f"  Queries processed: {job.queries_processed}")
        click.echo(f"  Citations found: {job.citations_found}")

        if job.error_log:
            click.echo(f"\nErrors encountered:")
            click.echo(job.error_log)

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise SystemExit(1)


@click.command('export-analysis')
@click.option('--format', '-f', type=click.Choice(['csv', 'json']), default='csv', help='Export format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@with_appcontext
def export_analysis(format, output):
    """Export citation analysis data."""
    df = DomainAnalyser.export_to_dataframe()

    if df.empty:
        click.echo("No data to export.")
        return

    if output is None:
        output = f"citation_export.{format}"

    if format == 'csv':
        df.to_csv(output, index=False, quoting=csv.QUOTE_NONNUMERIC)
    else:
        df.to_json(output, orient='records', indent=2)

    click.echo(f"Exported {len(df)} citations to {output}")


@click.command('add-query')
@click.option('--text', '-t', required=True, help='Query text')
@click.option('--intent', '-i', required=True,
              type=click.Choice(['informational', 'navigational', 'transactional', 'commercial']),
              help='Intent type')
@click.option('--category', '-c', required=True, help='Business category')
@with_appcontext
def add_query(text, intent, category):
    """Add a new query to the bank."""
    query = Query(
        query_text=text,
        intent_type=IntentType(intent),
        category=category,
        is_active=True
    )
    db.session.add(query)
    db.session.commit()

    click.echo(f"Added query #{query.id}: {text[:50]}...")


@click.command('list-queries')
@click.option('--category', '-c', help='Filter by category')
@click.option('--intent', '-i', help='Filter by intent type')
@click.option('--active/--all', default=True, help='Show only active queries')
@with_appcontext
def list_queries(category, intent, active):
    """List all queries in the bank."""
    query = Query.query

    if category:
        query = query.filter(Query.category == category)
    if intent:
        try:
            query = query.filter(Query.intent_type == IntentType(intent))
        except ValueError:
            click.echo(f"Invalid intent type: {intent}", err=True)
            return
    if active:
        query = query.filter(Query.is_active == True)

    queries = query.order_by(Query.category, Query.created_at.desc()).all()

    if not queries:
        click.echo("No queries found.")
        return

    current_category = None
    for q in queries:
        if q.category != current_category:
            current_category = q.category
            click.echo(f"\n=== {current_category.upper()} ===")

        status = "active" if q.is_active else "inactive"
        click.echo(f"  [{q.id}] ({q.intent_type.value[:4]}) {q.query_text[:60]} [{status}]")


@click.command('seed-demo-queries')
@with_appcontext
def seed_demo_queries():
    """Seed the database with demo queries for Australian gambling market."""
    demo_queries = [
        # Informational
        ("how do betting odds work australia", "informational", "sports betting"),
        ("what is a multi bet", "informational", "sports betting"),
        ("online gambling laws australia 2025", "informational", "regulations"),
        ("responsible gambling resources australia", "informational", "responsible gambling"),
        ("how to read horse racing form guide", "informational", "racing"),

        # Navigational
        ("sportsbet login", "navigational", "sports betting"),
        ("bet365 australia", "navigational", "sports betting"),
        ("tab website", "navigational", "racing"),
        ("pokerstars australia", "navigational", "poker"),

        # Transactional
        ("sign up bonus bet365 australia", "transactional", "sports betting"),
        ("sportsbet new customer offer", "transactional", "sports betting"),
        ("free bet no deposit australia", "transactional", "sports betting"),
        ("best welcome bonus betting australia", "transactional", "sports betting"),

        # Commercial
        ("best betting app australia 2025", "commercial", "sports betting"),
        ("top online casinos australia review", "commercial", "casino"),
        ("betting sites comparison australia", "commercial", "sports betting"),
        ("best afl betting odds", "commercial", "sports betting"),
        ("nrl premiership odds comparison", "commercial", "sports betting"),
        ("melbourne cup betting sites 2025", "commercial", "racing"),
        ("best poker sites australia real money", "commercial", "poker"),
    ]

    added = 0
    for text, intent, category in demo_queries:
        # Check if already exists
        existing = Query.query.filter_by(query_text=text).first()
        if existing:
            continue

        query = Query(
            query_text=text,
            intent_type=IntentType(intent),
            category=category,
            is_active=True
        )
        db.session.add(query)
        added += 1

    db.session.commit()
    click.echo(f"Added {added} demo queries ({len(demo_queries) - added} already existed)")
