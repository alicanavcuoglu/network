from flask import g, redirect, request, session, url_for

from app.extensions import db
from app.models import User
from app.routes.auth_routes import logout
from app.services.notifications import get_unread_notifications
from app.services.queries import has_unread_messages
from app.extensions import db


def register_handlers(app):
    """Before Requests"""

    @app.before_request
    def load_user():
        user_id = session.get("user_id")
        if user_id:
            g.user = db.get_or_404(User, user_id)  # Load the user or 404 if not found
        else:
            g.user = None  # Set to None if no user is in session

    # Instead of passing @login_required routes manually
    @app.before_request
    def require_login():
        # Don't require login
        public_endpoints = ["auth.login", "auth.register", "static", "auth.logout"]

        if request.endpoint in public_endpoints:
            return

        # Check if user is not logged in
        if g.user is None:
            return redirect(url_for("auth.login"))

        # Check if profile is incomplete
        if not g.user.is_completed and request.endpoint != "auth.complete_profile":
            return redirect(url_for("auth.complete_profile"))

    @app.before_request
    def load_unread_message_status():
        user_id = session.get("user_id")

        if user_id:
            current_user = User.query.get(user_id)
            if current_user:
                g.has_unread_messages = has_unread_messages(current_user.id)
            else:
                g.has_unread_messages = False
        else:
            g.has_unread_messages = False

    @app.before_request
    def load_unread_notifications():
        user_id = session.get("user_id")

        if user_id:
            current_user = User.query.get(user_id)
            if current_user:
                g.unread_notifications = get_unread_notifications(current_user.id)
            else:
                g.unread_notifications = []
        else:
            g.unread_notifications = None

    """ Context Processor """

    # Inject user variable to all pages
    # https://flask.palletsprojects.com/en/3.0.x/templating/#context-processors
    @app.context_processor
    def inject_user():
        if "user_id" in session:
            user = User.query.get(session["user_id"])
            return dict(current_user=user)
        return dict(current_user=None)

    """ After Request """

    @app.after_request
    def after_request(response):
        """Ensure responses aren't cached"""
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response
