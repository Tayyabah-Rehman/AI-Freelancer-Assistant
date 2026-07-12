from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

TONE_CHOICES = [
    ("professional", "Professional"),
    ("friendly", "Friendly"),
    ("confident", "Confident"),
    ("persuasive", "Persuasive"),
    ("formal", "Formal"),
]


class ProposalForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired(), Length(max=150)])
    project_title = StringField("Project Title", validators=[DataRequired(), Length(max=200)])
    project_description = TextAreaField(
        "Project Description", validators=[DataRequired(), Length(max=3000)]
    )
    skills = StringField(
        "Relevant Skills (comma separated)", validators=[DataRequired(), Length(max=500)]
    )
    budget = StringField("Budget", validators=[Optional(), Length(max=100)])
    timeline = StringField("Timeline", validators=[Optional(), Length(max=100)])
    tone = SelectField("Tone", choices=TONE_CHOICES, default="professional")
    submit = SubmitField("Generate Proposal")
