import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

UPLOAD_DIR = '/var/www/html/docrepo/uploads'
DOCUMENTS_DIR = '/var/www/html/docrepo/documents'


def create_app():
    app = Flask(__name__)

    # Config
    from . import key
    app.config['SECRET_KEY'] = key.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024
    app.config['UPLOAD_EXTENSIONS'] = ['.zip', '.tar']
    app.config['UPLOAD_DIR'] = UPLOAD_DIR
    app.config['DOCUMENTS_DIR'] = DOCUMENTS_DIR

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db + migrate
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Alembic sees them
    from . import models

    # Register routes
    from .views import main_bp
    app.register_blueprint(blueprint)

    return app
