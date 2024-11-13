from flask import Flask, g, redirect, request, session, url_for
from flask_mail import Mail
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from app.config import Config
from app.routes.auth_routes import logout
from app.services.notifications import get_unread_notifications
from app.services.queries import has_unread_messages
from app.extensions import db, mail, migrate, socketio


def create_app():
        
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    mail.init_app(app)

   
    with app.app_context():
        # Import and register blueprints
        from app.routes import auth_bp, errors_bp, filters_bp, main_bp
        app.register_blueprint(errors_bp)
        app.register_blueprint(filters_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)

        # Import and register handlers
        from app.handlers import register_handlers
        register_handlers(app)

        # Initialize Socket.IO events
        from app.events import init_socketio
        init_socketio(socketio)

        return app

app = create_app()