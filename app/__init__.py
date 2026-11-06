from flask import Flask
from dotenv import load_dotenv
import os

from .db import close_conn
from flask_wtf.csrf import CSRFProtect

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    CSRFProtect(app)
    from .markets import markets
    app.register_blueprint(markets)

    app.teardown_appcontext(close_conn)

    @app.route("/")
    def index():
        return "Hello from Eli Markets!"

    return app
