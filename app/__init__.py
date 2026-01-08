import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.config import config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """Application factory for creating Flask app."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.queries import queries_bp
    from app.routes.jobs import jobs_bp
    from app.routes.analysis import analysis_bp

    app.register_blueprint(queries_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(analysis_bp)

    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
