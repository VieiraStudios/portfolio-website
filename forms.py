"""Web forms.

Flask-WTF adds two safety features automatically:
- A hidden CSRF token, so other websites cannot submit the form on a
  visitor's behalf.
- Server-side validation, so bad or oversized input is rejected even if
  someone bypasses the browser's checks.
"""

from flask_wtf import FlaskForm
from wtforms import EmailField, SelectField, StringField, TextAreaField
from wtforms.fields import SelectChoice
from wtforms.validators import DataRequired, Email, Length, Optional

from content import PROJECT_TYPES


class ContactForm(FlaskForm):
    name = StringField(
        "Your name",
        validators=[DataRequired(message="Please tell me your name."), Length(max=100)],
    )
    email = EmailField(
        "Email",
        validators=[
            DataRequired(message="Please enter your email so I can reply."),
            Email(message="That email address doesn't look right."),
            Length(max=254),
        ],
    )
    project_type = SelectField(
        "What can I help with?",
        choices=[SelectChoice(value, label) for value, label in PROJECT_TYPES],
    )
    message = TextAreaField(
        "Tell me about your project",
        validators=[
            DataRequired(message="Please add a short message."),
            Length(min=10, max=5000, message="Messages need to be between 10 and 5,000 characters."),
        ],
    )
    # Honeypot: hidden from people with CSS. Spam bots tend to fill in every
    # field, so if this one has a value we quietly ignore the submission.
    website = StringField("Leave this field empty", validators=[Optional()])
