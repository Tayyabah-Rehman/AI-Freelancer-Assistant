from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

EXPERIENCE_CHOICES = [
    ("beginner", "Beginner"),
    ("intermediate", "Intermediate"),
    ("expert", "Expert"),
]


class GigDescriptionForm(FlaskForm):
    service_category = StringField("Service Category", validators=[DataRequired(), Length(max=150)])
    skills = StringField("Skills (comma separated)", validators=[DataRequired(), Length(max=500)])
    experience_level = SelectField("Experience Level", choices=EXPERIENCE_CHOICES, default="intermediate")
    delivery_time = StringField("Delivery Time (e.g. 3 days)", validators=[DataRequired(), Length(max=50)])
    features = TextAreaField("Features / What's Included", validators=[DataRequired(), Length(max=1000)])
    revisions = StringField("Revisions (e.g. 2 revisions)", validators=[DataRequired(), Length(max=50)])
    submit = SubmitField("Generate Gig Description")
