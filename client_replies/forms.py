from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

TONE_CHOICES = [
    ("professional", "Professional"),
    ("friendly", "Friendly"),
    ("firm", "Firm"),
    ("apologetic", "Apologetic"),
    ("assertive", "Assertive"),
]


class ClientReplyForm(FlaskForm):
    client_message = TextAreaField(
        "Client's Message", validators=[DataRequired(), Length(max=3000)]
    )
    tone = SelectField("Reply Tone", choices=TONE_CHOICES, default="professional")
    submit = SubmitField("Generate Reply")
