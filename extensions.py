from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
csrf = CSRFProtect()

# Rate limiting - protects login/register from brute force and AI routes from
# credit-draining abuse. Storage defaults to in-memory, which is fine for a
# single-process deployment; swap in Redis (storage_uri) if you scale to
# multiple workers/instances.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
