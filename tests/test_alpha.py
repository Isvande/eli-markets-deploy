from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from app.admin import decide_dispute
from app.chart import odds_points
from app.markets import TradeError

START = datetime(2026, 11, 1)


def test_chart_without_trades_is_flat_at_current_price():
    assert odds_points(START, START + timedelta(days=10), [], 0.5) == "0.0,100.0 600.0,100.0"


def test_chart_steps_at_each_trade():
    trades = [(START + timedelta(days=5), 0.5, 0.75)]
    assert odds_points(START, START + timedelta(days=10), trades, 0.75) == (
        "0.0,100.0 300.0,100.0 300.0,50.0 600.0,50.0"
    )


def test_chart_handles_zero_length_span():
    assert odds_points(START, START, [], 0.5) == "0.0,100.0 0.0,100.0"


class FakeConn:
    def __init__(self, dispute, holders):
        self.dispute = dispute
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
        if sql.startswith("SELECT d.status"):
            result.fetchone.return_value = self.dispute
        elif sql.startswith("SELECT user_id"):
            result.fetchall.return_value = self.holders
        else:
            self.updates.append((sql, params))
        return result


def open_dispute(**changes):
    return {"status": "open", "market_id": 9, "outcome": "yes", **changes}


def test_overturn_moves_payouts_to_the_other_side():
    conn = FakeConn(open_dispute(), [
        {"user_id": 2, "shares_yes": 30, "shares_no": 5},
        {"user_id": 3, "shares_yes": 0, "shares_no": 40},
    ])
    assert decide_dispute(conn, 1, 7, "overturned") == "no"
    balance_updates = [params for sql, params in conn.updates if sql.startswith("UPDATE users")]
    assert balance_updates == [(-2500, 2), (4000, 3)]
    assert ("no", 9) in [params for sql, params in conn.updates if sql.startswith("UPDATE markets")]


def test_uphold_changes_no_balances():
    conn = FakeConn(open_dispute(), [{"user_id": 2, "shares_yes": 30, "shares_no": 0}])
    assert decide_dispute(conn, 1, 7, "upheld") == "yes"
    assert [sql for sql, _ in conn.updates if sql.startswith("UPDATE users")] == []


@pytest.mark.parametrize("dispute, decision, message", [
    (None, "upheld", "does not exist"),
    (open_dispute(status="upheld"), "overturned", "already been decided"),
    (open_dispute(), "maybe", "uphold or overturn"),
])
def test_decide_refuses_and_changes_nothing(dispute, decision, message):
    conn = FakeConn(dispute, [])
    with pytest.raises(TradeError, match=message):
        decide_dispute(conn, 1, 7, decision)
    assert conn.updates == []
