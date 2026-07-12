from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class ContractForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired(), Length(max=150)])
    freelancer_name = StringField("Freelancer Name", validators=[DataRequired(), Length(max=150)])
    project_scope = TextAreaField("Project Scope", validators=[DataRequired(), Length(max=3000)])
    timeline = StringField("Timeline (e.g. 4 weeks, starting Aug 1)", validators=[DataRequired(), Length(max=150)])
    payment_terms = TextAreaField("Payment Terms", validators=[DataRequired(), Length(max=1000)])
    terms_conditions = TextAreaField(
        "Additional Terms & Conditions (optional)", validators=[Optional(), Length(max=2000)]
    )
    submit = SubmitField("Generate Contract")
