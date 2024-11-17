from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils.helpers import array_to_str, logout_required, upload_file_to_s3
from app.models import User
from app.routes import auth_bp


@auth_bp.route("/register", methods=["GET", "POST"])
@logout_required
def register():
    if request.method == "POST":
        # Form values
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirmation = request.form["confirmation"]
        terms = request.form.get("terms")

        # Ensure fullname was submitted
        if not username or not email or not password or not confirmation:
            flash("Please fill all fields!", "error")
            return redirect(url_for("auth.register"))

        # Check username
        if User.query.filter_by(username=username).first():
            flash("Username exists!", "error")
            return redirect(url_for("auth.register"))

        # Check email
        if User.query.filter_by(email=email).first():
            flash("Email exists!", "error")
            return redirect(url_for("auth.register"))

        # Check passwords
        if password != confirmation:
            flash("Passwords should match!", "error")
            return redirect(url_for("auth.register"))

        # Check password for minimum length
        if len(password) < 8:
            flash("New password must be at least 8 characters long.", "error")
            return redirect(url_for("auth.register"))

        if not terms:
            flash("You must accept the Terms of Use to register.", "error")
            return redirect(url_for("auth.register"))

        # Generate hash password to ensure safety
        hashed_password = generate_password_hash(password)

        # User model
        user = User(username=username, email=email, password=hashed_password)

        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id

        # Send email
        # token = generate_token(email)
        # confirm_url = url_for("confirm_email", token=token, _external=True)
        # html = render_template("auth/email_confirmation.html", confirm_url=confirm_url)
        # subject = "Please confirm your email"
        # send_email(user.email, subject, html)

        return redirect(url_for("auth.complete_profile"))

    return render_template("auth/register.html")


@auth_bp.route("/register/complete", methods=["GET", "POST"])
def complete_profile():
    current_user = db.get_or_404(User, session["user_id"])
    if current_user.is_completed:
        return redirect(url_for("main.feed"))

    if request.method == "POST":
        # Ensure user exists
        user = db.get_or_404(User, session["user_id"])
        if not user:
            return redirect(url_for("auth.login"))

        # Form values
        image = request.files["image"]
        name = request.form["name"]
        surname = request.form["surname"]
        location = request.form["location"]
        about = request.form["about-me"]
        working_on = request.form["working-on"]
        interests = array_to_str(request.form.getlist("interests[]"))
        classes = array_to_str(request.form.getlist("classes[]"))
        links = array_to_str(request.form.getlist("link[]"))

        # Check required fields exists
        if not name or not surname or not about:
            flash("Please fill the required fields!", "error")
            return redirect(url_for("auth.complete_profile"))

        image_path = upload_file_to_s3(image)

        # Update user
        user.image = image_path
        user.name = name
        user.surname = surname
        user.location = location
        user.about = about
        user.working_on = working_on
        user.interests = interests
        user.classes = classes
        user.links = links
        user.is_completed = True

        # Save changes
        try:
            db.session.commit()
            flash("Successfully created an account.", "success")
            return redirect(url_for("main.feed"))
        except:
            db.session.rollback()
            flash("Something went wrong, try again.", "error")
            return redirect(url_for("auth.complete_profile"))

    return render_template("auth/complete.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@logout_required
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.password, password):
            flash("Invalid username or password!", "error")
            return redirect(url_for("auth.login"))

        # Remember which user has logged in
        session["user_id"] = user.id

        # Redirect user to home page
        return redirect(url_for("main.feed"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for("main.feed"))


# # Email confirmation from https://www.freecodecamp.org/news/setup-email-verification-in-flask-app/
# @app.route("/confirm/<token>")
# def confirm_email(token):
#     current_user = User.query.get(session["user_id"])
#     if current_user.is_confirmed:
#         flash("Account already confirmed.", "success")
#         return redirect(url_for("main.feed"))
#     email = confirm_token(token)
#     user = User.query.filter_by(email=current_user.email).first_or_404()
#     if user.email == email:
#         user.is_confirmed = True
#         user.confirmed_on = datetime.now()
#         db.session.add(user)
#         db.session.commit()
#         flash("You have confirmed your account. Thanks!", "success")
#     else:
#         flash("The confirmation link is invalid or has expired.", "error")
#     return redirect(url_for("main.feed"))
