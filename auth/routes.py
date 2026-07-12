from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from extensions import db, limiter
from models import User, UserProfile
from auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")

RESET_TOKEN_MAX_AGE = 3600  # 1 hour
RESET_SALT = "password-reset"


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_reset_token(user):
    return _get_serializer().dumps(user.id, salt=RESET_SALT)


def verify_reset_token(token):
    try:
        user_id = _get_serializer().loads(token, salt=RESET_SALT, max_age=RESET_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(user_id)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("An account with that email already exists. Please log in instead.", "danger")
            return redirect(url_for("auth.login"))

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            ai_credits=current_app.config.get("DEFAULT_AI_CREDITS", 50),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

        login_user(user)
        flash("Account created successfully. Welcome to AI Freelancer Assistant!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    form = ForgotPasswordForm()
    reset_link = None

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        # Always show the same message whether or not the account exists,
        # so this endpoint can't be used to check which emails are registered.
        flash(
            "If an account exists with that email, a password reset link has been generated below.",
            "info",
        )

        if user:
            token = generate_reset_token(user)
            reset_link = url_for("auth.reset_password", token=token, _external=True)
            current_app.logger.info(f"Password reset requested for user_id={user.id}")

        # NOTE: No email provider is wired up in this build, so the reset
        # link is shown directly on the page instead of being emailed. To
        # go to production, replace this block with an email send (e.g.
        # Flask-Mail or an API like Resend/SendGrid) and stop displaying
        # the link here.

    return render_template("auth/forgot_password.html", form=form, reset_link=reset_link)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash("This password reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
