from flask import render_template

from app.routes import errors_bp


# @errors_bp.app_errorhandler(400)
# def bad_request(error):
#     title = error.description.get("title")
#     message = error.description.get("message")
#     print(message)
#     return render_template("errors/400.html"), 400

@errors_bp.app_errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@errors_bp.app_errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@errors_bp.app_errorhandler(413)
def too_large(error):
    return render_template("errors/413.html"), 413


@errors_bp.app_errorhandler(422)
def unprocessable(error):
    return render_template("errors/422.html"), 422


@errors_bp.app_errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500
