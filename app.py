import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, redirect, flash, request, url_for
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import db, login_manager, csrf, limiter


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Make sure the instance folder (holds the SQLite file) exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Trust the reverse proxy's headers (X-Forwarded-Proto, X-Forwarded-For)
    # when deployed behind Render/Railway/nginx/etc. Without this, Flask
    # thinks every request is plain HTTP even when the browser used HTTPS,
    # which breaks secure cookies and url_for(_external=True).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from auth.routes import auth_bp
    from dashboard.routes import dashboard_bp
    from modules.routes import modules_bp
    from proposals.routes import proposals_bp
    from cover_letters.routes import cover_letters_bp
    from gigs.routes import gigs_bp
    from pricing.routes import pricing_bp
    from client_replies.routes import client_replies_bp
    from invoices.routes import invoices_bp
    from contracts.routes import contracts_bp
    from user_profile.routes import user_profile_bp
    from settings.routes import settings_bp
    from history.routes import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(modules_bp, url_prefix="/modules")
    app.register_blueprint(proposals_bp, url_prefix="/proposals")
    app.register_blueprint(cover_letters_bp, url_prefix="/cover-letters")
    app.register_blueprint(gigs_bp, url_prefix="/gigs")
    app.register_blueprint(pricing_bp, url_prefix="/pricing")
    app.register_blueprint(client_replies_bp, url_prefix="/client-replies")
    app.register_blueprint(invoices_bp, url_prefix="/invoices")
    app.register_blueprint(contracts_bp, url_prefix="/contracts")
    app.register_blueprint(user_profile_bp, url_prefix="/profile")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(history_bp, url_prefix="/history")

    # Make current_user available in every template automatically
    @app.context_processor
    def inject_user():
        return {"current_user": current_user}

    # --- Security hardening ---
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB upload cap (avatar images)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    # Cookies only travel over HTTPS once deployed. Off in local dev (plain
    # HTTP on 127.0.0.1) since browsers won't set/send secure cookies there.
    app.config.setdefault("SESSION_COOKIE_SECURE", not app.debug)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not app.debug:
            # HSTS: once a browser has loaded this site over HTTPS, force
            # HTTPS for the next year. Harmless locally since debug is on.
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def file_too_large(error):
        flash("That file is too large. Please upload something under 2MB.", "danger")
        return redirect(request.referrer or url_for("dashboard.index")), 302

    @app.errorhandler(429)
    def rate_limited(error):
        flash("Too many attempts. Please wait a moment and try again.", "danger")
        return render_template("errors/429.html"), 429

    # --- Logging ---
    # Writes to instance/app.log (rotates at 1MB, keeps 3 backups) so a
    # production deployment has a trail to debug from instead of nothing.
    # Console logging still happens by default via Flask/Werkzeug.
    if not app.debug and not app.testing:
        log_path = os.path.join(app.instance_path, "app.log")
        file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # --- Health check (for Render/Railway uptime monitoring) ---
    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
