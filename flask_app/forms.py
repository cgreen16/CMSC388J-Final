import re

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import (
    InputRequired,
    Length,
    Email,
    EqualTo,
    ValidationError,
)

from .models import User

class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(min=1, max=40)]
    )
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=12, max=100)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[InputRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_password(self, password):
        for c in password.data:
            if ord(c) < 32:
                raise ValidationError("Invalid text (ascii <32)")
        if not re.search(r'[A-Z]', password.data) or not re.search(r'[a-z]', password.data) or not re.search(r'[^A-Za-z]', password.data):
            raise ValidationError("At least one uppercase, lowercase, and other character must be used.")
        if re.match(r'^ .*$', password.data) or re.match(r'^.* $', password.data):
            raise ValidationError("Cannot begin or end with a space.")

    def validate_username(self, username):
        user = User.objects(username=username.data).first()
        if user is not None:
            raise ValidationError("Username is taken")

    def validate_email(self, email):
        user = User.objects(email=email.data).first()
        if user is not None:
            raise ValidationError("Email is taken")


class UpdateUsernameForm(FlaskForm):
    username = StringField(
        "New Username", validators=[InputRequired(), Length(min=1, max=40)]
    )
    submit = SubmitField("Update Username")

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.objects(username=username.data).first()
            if user is not None:
                raise ValidationError("That username is already taken")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")

class ImageCreateForm(FlaskForm):
    prompt = StringField("Prompt", validators=[InputRequired(), Length(max=500)])
    submit = SubmitField("Create Image")

class InitiateChatForm(FlaskForm):
    prompt = StringField("Prompt", validators=[InputRequired(), Length(max=500)])
    submit = SubmitField("Create Chatbot")

class SendChatForm(FlaskForm):
    message = TextAreaField("Message", validators=[InputRequired(), Length(max=500)])
    submit = SubmitField("Send Message")
