from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    ai_credits = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("UserProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    proposals = db.relationship("Proposal", backref="user", cascade="all, delete-orphan")
    cover_letters = db.relationship("CoverLetter", backref="user", cascade="all, delete-orphan")
    gig_descriptions = db.relationship("GigDescription", backref="user", cascade="all, delete-orphan")
    pricing_history = db.relationship("PricingHistory", backref="user", cascade="all, delete-orphan")
    client_replies = db.relationship("ClientReply", backref="user", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", backref="user", cascade="all, delete-orphan")
    contracts = db.relationship("Contract", backref="user", cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    bio = db.Column(db.Text)
    skills = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(300))
    phone = db.Column(db.String(50))
    location = db.Column(db.String(150))
    hourly_rate = db.Column(db.Float)
    avatar_path = db.Column(db.String(300))
    theme = db.Column(db.String(20), default="dark")
    language = db.Column(db.String(20), default="en")
    groq_api_key = db.Column(db.String(200))
    email_notifications = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# The tables below are created now (empty) so Day 1's dashboard can safely
# query real counts, and so Day 2-5 only need to ADD ROWS, never migrate
# the schema.
# ---------------------------------------------------------------------------

class Proposal(db.Model):
    __tablename__ = "proposals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_name = db.Column(db.String(150))
    project_title = db.Column(db.String(200))
    project_description = db.Column(db.Text)
    skills = db.Column(db.String(500))
    budget = db.Column(db.String(100))
    timeline = db.Column(db.String(100))
    tone = db.Column(db.String(50))
    generated_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CoverLetter(db.Model):
    __tablename__ = "cover_letters"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_title = db.Column(db.String(200))
    company_name = db.Column(db.String(200))
    experience = db.Column(db.Text)
    skills = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(300))
    generated_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GigDescription(db.Model):
    __tablename__ = "gig_descriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    service_category = db.Column(db.String(150))
    skills = db.Column(db.String(500))
    experience_level = db.Column(db.String(50))
    delivery_time = db.Column(db.String(50))
    features = db.Column(db.Text)
    revisions = db.Column(db.String(50))
    generated_description = db.Column(db.Text)
    seo_keywords = db.Column(db.String(500))
    faq_suggestions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PricingHistory(db.Model):
    __tablename__ = "pricing_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    hourly_rate = db.Column(db.Float)
    estimated_hours = db.Column(db.Float)
    complexity = db.Column(db.String(50))
    urgency = db.Column(db.String(50))
    additional_charges = db.Column(db.Float)
    tax = db.Column(db.Float)
    suggested_price = db.Column(db.Float)
    recommended_delivery_time = db.Column(db.String(100))
    market_analysis = db.Column(db.Text)
    service_improvement_tips = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClientReply(db.Model):
    __tablename__ = "client_replies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_message = db.Column(db.Text)
    tone = db.Column(db.String(50))
    generated_reply = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    invoice_number = db.Column(db.String(50))
    client_name = db.Column(db.String(150))
    client_email = db.Column(db.String(150))
    project_details = db.Column(db.Text)
    services = db.Column(db.Text)
    amount = db.Column(db.Float)
    tax = db.Column(db.Float)
    due_date = db.Column(db.Date)
    pdf_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_name = db.Column(db.String(150))
    freelancer_name = db.Column(db.String(150))
    project_scope = db.Column(db.Text)
    timeline = db.Column(db.String(150))
    payment_terms = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)
    generated_content = db.Column(db.Text)
    pdf_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
