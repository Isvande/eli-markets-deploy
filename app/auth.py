import re
import bcrypt
import psycopg
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    session,
    url_for,
)
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from .db import query_one

auth_bp = Blueprint("auth", __name__)
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())


def validate_yale_email(_form, field):
    email = field.data.strip().lower()
    if not re.fullmatch(r"[^@\s]+@yale\.edu", email):
        raise ValidationError("Enter an email address ending in @yale.edu.")
    field.data = email


def validate_password_bytes(_form, field):
    if len(field.data.encode("utf-8")) > 72:
        raise ValidationError("Password must be no more than 72 bytes.")


class SignupForm(FlaskForm):
    email = StringField(
        "Yale email",
        validators=[DataRequired(), Length(max=254), validate_yale_email],
    )
    display_name = StringField(
        "Display name",
        validators=[DataRequired(), Length(min=1, max=80)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8), validate_password_bytes],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField(
        "Yale email",
        validators=[DataRequired(), Length(max=254), validate_yale_email],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), validate_password_bytes],
    )
    submit = SubmitField("Log in")


def _start_user_session(user_id):
    session.clear()
    current_app.session_interface.regenerate(session)
    session["user_id"] = user_id
    session.permanent = True


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if g.user is not None:
        return redirect(url_for("index"))

    form = SignupForm()
    if form.validate_on_submit():
        existing_user = query_one(
            "SELECT id FROM users WHERE yale_email = %s",
            (form.email.data,),
        )
        if existing_user is not None:
            form.email.errors.append("An account with that email already exists.")
        else:
            password_hash = bcrypt.hashpw(
                form.password.data.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("ascii")
            try:
                user = query_one(
                    """
                    INSERT INTO users (yale_email, password_hash, display_name)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (form.email.data, password_hash, form.display_name.data.strip()),
                )
            except psycopg.errors.UniqueViolation:
                form.email.errors.append("An account with that email already exists.")
            else:
                _start_user_session(user["id"])
                flash("Your account is ready. You have 1,000 coins.", "success")
                return redirect(url_for("index"))

    return render_template("signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = query_one(
            """
            SELECT id, password_hash, is_ai
            FROM users
            WHERE yale_email = %s
            """,
            (form.email.data,),
        )
        stored_hash = (
            user["password_hash"].encode("ascii")
            if user is not None and not user["is_ai"] and user["password_hash"]
            else _DUMMY_PASSWORD_HASH
        )
        password_matches = bcrypt.checkpw(form.password.data.encode("utf-8"), stored_hash)

        if user is None or user["is_ai"] or not user["password_hash"] or not password_matches:
            flash("Invalid email or password.", "error")
        else:
            _start_user_session(user["id"])
            flash("You are now logged in.", "success")
            return redirect(url_for("index"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    current_app.session_interface.regenerate(session)
    flash("You are now logged out.", "success")
    return redirect(url_for("auth.login"))
