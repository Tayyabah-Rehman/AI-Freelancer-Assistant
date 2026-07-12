from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Optional, Length, NumberRange, Email


class InvoiceForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired(), Length(max=150)])
    client_email = StringField(
        "Client Email (optional)", validators=[Optional(), Email(), Length(max=150)]
    )
    project_details = TextAreaField("Project Details", validators=[DataRequired(), Length(max=2000)])
    services = TextAreaField("Services / Line Items", validators=[DataRequired(), Length(max=2000)])
    amount = FloatField("Amount (USD)", validators=[InputRequired(), NumberRange(min=0.01, max=1000000)])
    tax_percent = FloatField(
        "Tax % (enter 0 if none)", validators=[InputRequired(), NumberRange(min=0, max=100)], default=0
    )
    due_date = DateField("Due Date", validators=[DataRequired()], format="%Y-%m-%d")
    submit = SubmitField("Generate Invoice")
