from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, URL


class CoverLetterForm(FlaskForm):
    job_title = StringField("Job Title", validators=[DataRequired(), Length(max=200)])
    company_name = StringField("Company Name", validators=[DataRequired(), Length(max=200)])
    experience = TextAreaField(
        "Relevant Experience", validators=[DataRequired(), Length(max=3000)]
    )
    skills = StringField(
        "Skills (comma separated)", validators=[DataRequired(), Length(max=500)]
    )
    portfolio_url = StringField(
        "Portfolio URL", validators=[Optional(), URL(require_tld=True), Length(max=300)]
    )
    submit = SubmitField("Generate Cover Letter")
