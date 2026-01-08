import csv
import io
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for

from app import db
from app.models import Query, IntentType

queries_bp = Blueprint('queries', __name__)


@queries_bp.route('/')
def index():
    """Redirect root to dashboard."""
    return redirect(url_for('analysis.dashboard'))


@queries_bp.route('/queries')
def list_queries():
    """List all queries with optional filtering."""
    # Get filter parameters
    intent = request.args.get('intent')
    category = request.args.get('category')
    active_only = request.args.get('active', 'true').lower() == 'true'

    # Build query
    query = Query.query

    if intent:
        try:
            intent_type = IntentType(intent)
            query = query.filter(Query.intent_type == intent_type)
        except ValueError:
            pass

    if category:
        query = query.filter(Query.category == category)

    if active_only:
        query = query.filter(Query.is_active == True)

    queries = query.order_by(Query.created_at.desc()).all()

    # Get unique categories for filter dropdown
    categories = db.session.query(Query.category).distinct().all()
    categories = [c[0] for c in categories]

    # Check if API request
    if request.headers.get('Accept') == 'application/json':
        return jsonify([q.to_dict() for q in queries])

    return render_template(
        'queries.html',
        queries=queries,
        categories=categories,
        intent_types=[i.value for i in IntentType]
    )


@queries_bp.route('/queries', methods=['POST'])
def create_query():
    """Create a new query."""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    # Validate required fields
    if not data.get('query_text'):
        if request.is_json:
            return jsonify({'error': 'query_text is required'}), 400
        flash('Query text is required', 'error')
        return redirect(url_for('queries.list_queries'))

    if not data.get('intent_type'):
        if request.is_json:
            return jsonify({'error': 'intent_type is required'}), 400
        flash('Intent type is required', 'error')
        return redirect(url_for('queries.list_queries'))

    if not data.get('category'):
        if request.is_json:
            return jsonify({'error': 'category is required'}), 400
        flash('Category is required', 'error')
        return redirect(url_for('queries.list_queries'))

    # Validate intent type
    try:
        intent_type = IntentType(data['intent_type'])
    except ValueError:
        if request.is_json:
            return jsonify({'error': f"Invalid intent_type. Must be one of: {[i.value for i in IntentType]}"}), 400
        flash('Invalid intent type', 'error')
        return redirect(url_for('queries.list_queries'))

    query = Query(
        query_text=data['query_text'],
        intent_type=intent_type,
        category=data['category'],
        is_active=data.get('is_active', True)
    )

    db.session.add(query)
    db.session.commit()

    if request.is_json:
        return jsonify(query.to_dict()), 201

    flash('Query added successfully', 'success')
    return redirect(url_for('queries.list_queries'))


@queries_bp.route('/queries/bulk', methods=['POST'])
def bulk_upload():
    """Bulk upload queries from CSV file."""
    if 'file' not in request.files:
        if request.is_json:
            return jsonify({'error': 'No file provided'}), 400
        flash('No file provided', 'error')
        return redirect(url_for('queries.list_queries'))

    file = request.files['file']
    if file.filename == '':
        if request.is_json:
            return jsonify({'error': 'No file selected'}), 400
        flash('No file selected', 'error')
        return redirect(url_for('queries.list_queries'))

    if not file.filename.endswith('.csv'):
        if request.is_json:
            return jsonify({'error': 'File must be CSV'}), 400
        flash('File must be CSV', 'error')
        return redirect(url_for('queries.list_queries'))

    # Parse CSV
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)

        added = 0
        errors = []

        for row in reader:
            try:
                intent_type = IntentType(row.get('intent_type', '').lower())
                query = Query(
                    query_text=row['query_text'],
                    intent_type=intent_type,
                    category=row['category'],
                    is_active=row.get('is_active', 'true').lower() == 'true'
                )
                db.session.add(query)
                added += 1
            except (ValueError, KeyError) as e:
                errors.append(f"Row error: {str(e)}")

        db.session.commit()

        if request.is_json:
            return jsonify({
                'added': added,
                'errors': errors
            }), 201

        if errors:
            flash(f'Added {added} queries with {len(errors)} errors', 'warning')
        else:
            flash(f'Successfully added {added} queries', 'success')

    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error processing file: {str(e)}', 'error')

    return redirect(url_for('queries.list_queries'))


@queries_bp.route('/queries/<int:query_id>')
def get_query(query_id):
    """Get a specific query."""
    query = Query.query.get_or_404(query_id)

    if request.headers.get('Accept') == 'application/json':
        return jsonify(query.to_dict())

    return render_template('query_detail.html', query=query)


@queries_bp.route('/queries/<int:query_id>', methods=['PUT', 'PATCH'])
def update_query(query_id):
    """Update a query."""
    query = Query.query.get_or_404(query_id)
    data = request.get_json()

    if 'query_text' in data:
        query.query_text = data['query_text']

    if 'intent_type' in data:
        try:
            query.intent_type = IntentType(data['intent_type'])
        except ValueError:
            return jsonify({'error': 'Invalid intent_type'}), 400

    if 'category' in data:
        query.category = data['category']

    if 'is_active' in data:
        query.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify(query.to_dict())


@queries_bp.route('/queries/<int:query_id>', methods=['DELETE'])
def delete_query(query_id):
    """Delete a query."""
    query = Query.query.get_or_404(query_id)
    db.session.delete(query)
    db.session.commit()

    if request.headers.get('Accept') == 'application/json':
        return jsonify({'message': 'Query deleted'}), 200

    flash('Query deleted', 'success')
    return redirect(url_for('queries.list_queries'))


@queries_bp.route('/queries/<int:query_id>/toggle', methods=['POST'])
def toggle_query(query_id):
    """Toggle query active status."""
    query = Query.query.get_or_404(query_id)
    query.is_active = not query.is_active
    db.session.commit()

    if request.headers.get('Accept') == 'application/json':
        return jsonify(query.to_dict())

    flash(f'Query {"activated" if query.is_active else "deactivated"}', 'success')
    return redirect(url_for('queries.list_queries'))
