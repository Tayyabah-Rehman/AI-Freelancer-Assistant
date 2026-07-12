from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, SubmitField
from wtforms.validators import InputRequired, NumberRange

COMPLEXITY_CHOICES = [
    ("simple", "Simple"),
    ("moderate", "Moderate"),
    ("complex", "Complex"),
]

URGENCY_CHOICES = [
    ("standard", "Standard"),
    ("rush", "Rush (faster delivery)"),
    ("urgent", "Urgent (ASAP)"),
]


class PricingForm(FlaskForm):
    hourly_rate = FloatField("Hourly Rate (USD)", validators=[InputRequired(), NumberRange(min=1, max=1000)])
    estimated_hours = FloatField("Estimated Hours", validators=[InputRequired(), NumberRange(min=0.5, max=2000)])
    complexity = SelectField("Project Complexity", choices=COMPLEXITY_CHOICES, default="moderate")
    urgency = SelectField("Urgency", choices=URGENCY_CHOICES, default="standard")
    additional_charges = FloatField(
        "Additional Charges (USD)", validators=[InputRequired(), NumberRange(min=0, max=100000)], default=0
    )
    tax_percent = FloatField(
        "Tax % (enter 0 if not applicable)", validators=[InputRequired(), NumberRange(min=0, max=100)], default=0
    )
    submit = SubmitField("Calculate & Get AI Suggestions")
