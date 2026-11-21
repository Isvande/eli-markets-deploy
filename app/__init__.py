import os
from datetime import timedelta

import click
from dotenv import load_dotenv
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from .auth import auth_bp
from .db import close_conn, query_all, query_one
from .sessions import PostgresSessionInterface

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    secure_cookie = os.getenv("SESSION_COOKIE_SECURE")
    if secure_cookie is None:
        secure_cookie = "false" if os.getenv("FLASK_DEBUG") == "1" else "true"
    app.config["SESSION_COOKIE_SECURE"] = secure_cookie.lower() in {"1", "true", "yes"}

    app.session_interface = PostgresSessionInterface()
    app.teardown_appcontext(close_conn)
    CSRFProtect(app)
    app.register_blueprint(auth_bp)

    from .admin import admin
    from .community import community
    from .markets import SORTS, markets, open_markets

    app.register_blueprint(markets)
    app.register_blueprint(admin)
    app.register_blueprint(community)

    @app.cli.command("make-admin")
    @click.argument("email")
    def make_admin(email):
        """Give an existing account admin rights: flask --app wsgi make-admin you@yale.edu"""
        user = query_one(
            "UPDATE users SET is_admin = TRUE WHERE yale_email = %s RETURNING display_name",
            (email.strip().lower(),),
        )
        click.echo(f"{user['display_name']} is now an admin." if user else "No account has that email.")

    @app.before_request
    def load_logged_in_user():
        if request.endpoint == "static":
            return

        user_id = session.get("user_id")
        g.user = (
            query_one(
                """
                SELECT id, yale_email, display_name, balance_cents, is_admin
                FROM users
                WHERE id = %s AND is_ai = FALSE
                """,
                (user_id,),
            )
            if user_id is not None
            else None
        )
        if user_id is not None and g.user is None:
            session.clear()

        public_endpoints = {"auth.login", "auth.signup", "how_it_works"}
        if request.endpoint not in public_endpoints and g.user is None:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth.login"))

    @app.route("/")
    def index():
        tag = request.args.get("tag") or None
        sort = request.args.get("sort") if request.args.get("sort") in SORTS else "closing"
        tags = [row["name"] for row in query_all("SELECT name FROM tags ORDER BY name")]
        return render_template(
            "index.html", markets=open_markets(tag, sort), tags=tags, current_tag=tag, sort=sort
        )

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        return f"Form security check failed: {error.description}", 400

    return app
