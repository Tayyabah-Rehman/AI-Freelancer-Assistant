import os
import warnings
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

FLASK_ENV = os.environ.get("FLASK_ENV", "development")
_DEFAULT_SECRET = "dev-secret-key-change-me"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", _DEFAULT_SECRET)

    # DEBUG must be off in production: Flask's debugger lets anyone who can
    # trigger a 500 error run arbitrary Python on your server.
    DEBUG = FLASK_ENV != "production"
    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(basedir, "instance", "app.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

    # AI settings - wired up starting Day 2
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Default AI credits given to a new user
    DEFAULT_AI_CREDITS = 50


if FLASK_ENV == "production" and Config.SECRET_KEY == _DEFAULT_SECRET:
    warnings.warn(
        "SECRET_KEY is still the default placeholder in a production environment. "
        "Set a real random SECRET_KEY in your platform's environment variables.",
        RuntimeWarning,
    )
