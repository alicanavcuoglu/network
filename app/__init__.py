from flask import Flask

from app.config import Config
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
        from app.routes import auth_bp, errors_bp, filters_bp, main_bp, group_bp

        app.register_blueprint(errors_bp)
        app.register_blueprint(filters_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(group_bp)

        # Import and register handlers
        from app.handlers import register_handlers

        register_handlers(app)

        # Initialize Socket.IO events
        from app.events import init_socketio

        init_socketio(socketio)

        return app


app = create_app()
