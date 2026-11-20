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
