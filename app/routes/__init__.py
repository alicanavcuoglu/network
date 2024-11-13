from flask import Blueprint

# Create blueprints
errors_bp = Blueprint('errors', __name__)
filters_bp = Blueprint('filter', __name__)
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)

__all__ = ['errors_bp', 'filters_bp', 'auth_bp', 'main_bp']

# Import routes AFTER blueprint creation
from app.routes import error_routes
from app.routes import filter_routes
from app.routes import auth_routes
from app.routes import main_routes