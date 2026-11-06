import re
from unittest.mock import Mock

import bcrypt
import pytest

from app import auth
from app import create_app


class FakeSessionStore:
    def __init__(self):
        self.rows = {}

    def execute(self, sql, params):
        if sql.lstrip().startswith("DELETE"):
            self.rows.pop(params[0], None)
        else:
            self.rows[params[0]] = {"session_data": params[1]}


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    application = create_app()
    application.config.update(TESTING=True)
    session_store = FakeSessionStore()

    def load_session(_sql, params):
        return session_store.rows.get(params[0])

    monkeypatch.setattr("app.sessions.get_conn", lambda: session_store)
    monkeypatch.setattr("app.sessions.query_one", load_session)
    return application


def csrf_token(response):
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode()


def test_signup_creates_hashed_password_and_logs_user_in(app, monkeypatch):
    monkeypatch.setattr(auth, "query_one", Mock(side_effect=[None, {"id": 12}]))
    monkeypatch.setattr("app.query_one", Mock(return_value={
        "id": 12,
        "yale_email": "student@yale.edu",
        "display_name": "Student",
        "balance_cents": 100000,
    }))

    client = app.test_client()
    token = csrf_token(client.get("/signup"))
    response = client.post(
        "/signup",
        data={
            "csrf_token": token,
            "email": "STUDENT@YALE.EDU",
            "display_name": "Student",
            "password": "correct horse battery",
            "confirm_password": "correct horse battery",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Welcome, Student." in response.data
    assert b"1,000 coins" in response.data
    assert auth.query_one.call_count == 2
    insert_params = auth.query_one.call_args_list[1].args[1]
    assert insert_params[0] == "student@yale.edu"
    assert insert_params[1] != "correct horse battery"
    assert bcrypt.checkpw(b"correct horse battery", insert_params[1].encode("ascii"))
    assert insert_params[2] == "Student"


def test_signup_rejects_non_yale_email(app, monkeypatch):
    lookup = Mock()
    monkeypatch.setattr(auth, "query_one", lookup)
    client = app.test_client()
    token = csrf_token(client.get("/signup"))

    response = client.post(
        "/signup",
        data={
            "csrf_token": token,
            "email": "student@example.com",
            "display_name": "Student",
            "password": "correct horse battery",
            "confirm_password": "correct horse battery",
        },
    )

    assert response.status_code == 200
    assert b"ending in @yale.edu" in response.data
    lookup.assert_not_called()


def test_signup_requires_csrf_token(app, monkeypatch):
    lookup = Mock()
    monkeypatch.setattr(auth, "query_one", lookup)

    response = app.test_client().post(
        "/signup",
        data={
            "email": "student@yale.edu",
            "display_name": "Student",
            "password": "correct horse battery",
            "confirm_password": "correct horse battery",
        },
    )

    assert response.status_code == 400
    lookup.assert_not_called()


def test_home_page_requires_login(app):
    response = app.test_client().get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_session_cookie_is_http_only_and_secure_when_configured(app):
    app.config["SESSION_COOKIE_SECURE"] = True

    response = app.test_client().get("/signup")
    cookie = response.headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=Lax" in cookie


def test_login_and_logout(app, monkeypatch):
    monkeypatch.setattr(
        auth,
        "query_one",
        Mock(return_value={
            "id": 12,
            "password_hash": bcrypt.hashpw(
                b"correct horse battery",
                bcrypt.gensalt(),
            ).decode("ascii"),
            "is_ai": False,
        }),
    )
    monkeypatch.setattr("app.query_one", Mock(return_value={
        "id": 12,
        "yale_email": "student@yale.edu",
        "display_name": "Student",
        "balance_cents": 100000,
    }))
    client = app.test_client()
    token = csrf_token(client.get("/login"))
    response = client.post(
        "/login",
        data={
            "csrf_token": token,
            "email": "student@yale.edu",
            "password": "correct horse battery",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Welcome, Student." in response.data
    token = csrf_token(response)

    response = client.post(
        "/logout",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Log in" in response.data
    assert b"You are now logged out." in response.data


def test_login_rejects_invalid_password(app, monkeypatch):
    monkeypatch.setattr(
        auth,
        "query_one",
        Mock(return_value={
            "id": 12,
            "password_hash": bcrypt.hashpw(b"right password", bcrypt.gensalt()).decode("ascii"),
            "is_ai": False,
        }),
    )
    client = app.test_client()
    token = csrf_token(client.get("/login"))

    response = client.post(
        "/login",
        data={
            "csrf_token": token,
            "email": "student@yale.edu",
            "password": "wrong password",
        },
    )

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
