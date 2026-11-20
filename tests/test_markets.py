from datetime import datetime
from unittest.mock import Mock

import pytest

from app import create_app, markets
from app.markets import TradeError, settle_market


class FakeConn:
    def __init__(self, market, holders):
        self.market = market
        self.holders = holders
        self.updates = []

    def transaction(self):
        conn = self

        class Tx:
            def __enter__(self):
                return conn

            def __exit__(self, *exc):
                return False

        return Tx()

    def execute(self, sql, params):
        result = Mock()
        if sql.startswith("SELECT creator_id"):
            result.fetchone.return_value = self.market
        elif sql.startswith("SELECT user_id"):
            result.fetchall.return_value = self.holders
        else:
            self.updates.append((sql, params))
        return result


def closed_market(**changes):
    return {"creator_id": 1, "status": "open", "has_closed": True, **changes}


def test_settle_pays_each_winning_share_one_coin():
    conn = FakeConn(closed_market(), [
        {"user_id": 2, "shares_yes": 30, "shares_no": 5},
        {"user_id": 3, "shares_yes": 0, "shares_no": 40},
    ])
    assert settle_market(conn, 9, 1, "yes") == 3000
    balance_updates = [params for sql, params in conn.updates if sql.startswith("UPDATE users")]
    assert balance_updates == [(3000, 2)]
    assert conn.updates[-1][1] == ("yes", 9)


def test_settle_no_pays_the_no_holders():
    conn = FakeConn(closed_market(), [
        {"user_id": 2, "shares_yes": 30, "shares_no": 5},
        {"user_id": 3, "shares_yes": 0, "shares_no": 40},
    ])
    assert settle_market(conn, 9, 1, "no") == 4500


@pytest.mark.parametrize("market, message", [
    (None, "does not exist"),
    (closed_market(creator_id=99), "Only the creator"),
    (closed_market(status="resolved"), "already settled"),
    (closed_market(has_closed=False), "after its closing date"),
])
def test_settle_refuses_and_changes_nothing(market, message):
    conn = FakeConn(market, [{"user_id": 2, "shares_yes": 10, "shares_no": 0}])
    with pytest.raises(TradeError, match=message):
        settle_market(conn, 9, 1, "yes")
    assert conn.updates == []


def test_settle_rejects_bad_outcome():
    with pytest.raises(TradeError):
        settle_market(FakeConn(closed_market(), []), 9, 1, "maybe")


class FakeSessionStore:
    def __init__(self):
        self.rows = {}

    def execute(self, sql, params):
        if sql.lstrip().startswith("DELETE"):
            self.rows.pop(params[0], None)
        else:
            self.rows[params[0]] = {"session_data": params[1]}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    app = create_app()
    app.config.update(TESTING=True)
    store = FakeSessionStore()
    monkeypatch.setattr("app.sessions.get_conn", lambda: store)
    monkeypatch.setattr("app.sessions.query_one", lambda _sql, params: store.rows.get(params[0]))
    monkeypatch.setattr("app.query_one", Mock(return_value={
        "id": 12, "yale_email": "student@yale.edu", "display_name": "Student", "balance_cents": 123450,
    }))
    return app.test_client()


def test_profile_requires_login(client, monkeypatch):
    monkeypatch.setattr("app.query_one", Mock(return_value=None))
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_profile_shows_coins_shares_trades_and_brier(client, monkeypatch):
    monkeypatch.setattr(markets, "query_all", Mock(side_effect=[
        [{"id": 4, "question": "Will it snow?", "status": "open", "outcome": None, "shares_yes": 10, "shares_no": 0}],
        [{"traded_local": datetime(2026, 11, 20, 14, 5), "market_id": 4, "question": "Will it snow?",
          "side": "yes", "shares": 10, "cost_cents": 512}],
        [{"probability": 0.7, "outcome": "yes"}, {"probability": 0.2, "outcome": "no"}],
    ]))
    with client.session_transaction() as s:
        s["user_id"] = 12

    page = client.get("/profile").data
    assert b"1,234.50" in page
    assert b"10 yes, 0 no" in page
    assert b"5.12 coins" in page
    assert b"0.065 over 2 questions" in page


def test_profile_without_settled_forecasts(client, monkeypatch):
    monkeypatch.setattr(markets, "query_all", Mock(side_effect=[[], [], []]))
    with client.session_transaction() as s:
        s["user_id"] = 12

    page = client.get("/profile").data
    assert b"no settled forecasts yet" in page
    assert b"No trades yet." in page
