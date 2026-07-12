from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, BooleanField, SubmitField
from wtforms.validators import Optional, Length

THEME_CHOICES = [("dark", "Dark"), ("light", "Light")]

LANGUAGE_CHOICES = [
    ("en", "English"),
    ("ur", "Urdu (interface translation not yet implemented)"),
]


class SettingsForm(FlaskForm):
    theme = SelectField("Theme", choices=THEME_CHOICES, default="dark")
    language = SelectField("Language", choices=LANGUAGE_CHOICES, default="en")
    groq_api_key = StringField(
        "Your Groq API Key (optional)",
        validators=[Optional(), Length(max=200)],
        description="If set, this is used instead of the app's shared key from .env.",
    )
    email_notifications = BooleanField("Email notifications", default=True)
    submit = SubmitField("Save Settings")
