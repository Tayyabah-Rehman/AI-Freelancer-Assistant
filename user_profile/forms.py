from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, TextAreaField, FloatField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, URL, EqualTo


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=1000)])
    skills = StringField("Skills (comma separated)", validators=[Optional(), Length(max=500)])
    portfolio_url = StringField(
        "Portfolio URL", validators=[Optional(), URL(require_tld=True), Length(max=300)]
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    hourly_rate = FloatField("Hourly Rate (USD)", validators=[Optional()])
    avatar = FileField(
        "Profile Picture",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only (jpg, png, webp)."),
            FileSize(max_size=2 * 1024 * 1024, message="Image must be under 2MB."),
        ],
    )
    submit = SubmitField("Save Profile")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change Password")
