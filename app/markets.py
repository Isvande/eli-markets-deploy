from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from flask_wtf.csrf import generate_csrf

from .compute import mean_brier, payout_cents, price_yes, trade_cost_cents
from .chart import odds_points
from .db import get_conn, query_all, query_one

markets = Blueprint("markets", __name__)


class TradeError(ValueError):
    pass


def buy_shares(conn, user_id, market_id, side, shares, expected_cost_cents):
    if side not in ("yes", "no") or isinstance(shares, bool) or not isinstance(shares, int) or shares <= 0:
        raise TradeError("Choose a side and enter a positive number of shares.")
    if isinstance(expected_cost_cents, bool) or not isinstance(expected_cost_cents, int) or expected_cost_cents < 0:
        raise TradeError("Review the price before buying.")

    with conn.transaction():
        market = conn.execute(
            "SELECT id, q_yes, q_no, b FROM markets WHERE id = %s AND status = 'open' AND closes_at > now() FOR UPDATE",
            (market_id,),
        ).fetchone()
        if market is None:
            raise TradeError("This market is closed or does not exist.")
        user = conn.execute("SELECT balance_cents FROM users WHERE id = %s FOR UPDATE", (user_id,)).fetchone()
        if user is None:
            raise TradeError("Please log in again.")

        q_yes, q_no, b = (float(market[key]) for key in ("q_yes", "q_no", "b"))
        charge = trade_cost_cents(q_yes, q_no, side, shares, b)
        if charge != expected_cost_cents:
            raise TradeError("The price changed. Please review the new price before buying.")
        if charge > user["balance_cents"]:
            raise TradeError("You do not have enough coins.")

        before = price_yes(q_yes, q_no, b)
        yes_shares = shares if side == "yes" else 0
        no_shares = shares if side == "no" else 0
        after = price_yes(q_yes + yes_shares, q_no + no_shares, b)
        conn.execute("UPDATE users SET balance_cents = balance_cents - %s WHERE id = %s", (charge, user_id))
        conn.execute("UPDATE markets SET q_yes = q_yes + %s, q_no = q_no + %s WHERE id = %s", (yes_shares, no_shares, market_id))
        conn.execute(
            "INSERT INTO positions (user_id, market_id, shares_yes, shares_no) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (user_id, market_id) DO UPDATE SET shares_yes = positions.shares_yes + EXCLUDED.shares_yes, "
            "shares_no = positions.shares_no + EXCLUDED.shares_no",
            (user_id, market_id, yes_shares, no_shares),
        )
        conn.execute(
            "INSERT INTO trades (user_id, market_id, side, shares, cost_cents, price_before, price_after) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, market_id, side, shares, charge, before, after),
        )
    return charge


SORTS = {
    "closing": "m.closes_at, m.id",
    "newest": "m.created_at DESC, m.id DESC",
    "popular": "trade_count DESC, m.closes_at",
    "likely": "(m.q_yes - m.q_no) / m.b DESC, m.closes_at",
}


def open_markets(tag=None, sort="closing"):
    order = SORTS.get(sort, SORTS["closing"])
    rows = query_all(
        "SELECT m.id, m.question, m.closes_at AT TIME ZONE 'America/New_York' AS closes_local, m.q_yes, m.q_no, m.b, "
        "(SELECT count(*) FROM trades t WHERE t.market_id = m.id) AS trade_count, "
        "ARRAY(SELECT tg.name FROM market_tags mt JOIN tags tg ON tg.id = mt.tag_id "
        "WHERE mt.market_id = m.id ORDER BY tg.name) AS tags "
        "FROM markets m WHERE m.status = 'open' AND m.closes_at > now() "
        "AND (%(tag)s::text IS NULL OR EXISTS (SELECT 1 FROM market_tags mt JOIN tags tg ON tg.id = mt.tag_id "
        "WHERE mt.market_id = m.id AND tg.name = %(tag)s)) "
        f"ORDER BY {order}",
        {"tag": tag},
    )
    return [{**row, "probability": price_yes(float(row["q_yes"]), float(row["q_no"]), float(row["b"]))} for row in rows]


@markets.get("/markets/<int:market_id>")
def market_detail(market_id):
    market = get_conn().execute(
        "SELECT *, (status = 'open' AND closes_at > now()) AS is_open, "
        "(closes_at <= now()) AS has_closed, now() AS now, "
        "closes_at AT TIME ZONE 'America/New_York' AS closes_local FROM markets WHERE id = %s", (market_id,)
    ).fetchone()
    if market is None:
        abort(404)
    user_id = g.user["id"]
    probability = price_yes(float(market["q_yes"]), float(market["q_no"]), float(market["b"]))
    tags = [row["name"] for row in query_all(
        "SELECT tg.name FROM market_tags mt JOIN tags tg ON tg.id = mt.tag_id WHERE mt.market_id = %s ORDER BY tg.name",
        (market_id,),
    )]
    history = query_all(
        "SELECT traded_at, price_before, price_after FROM trades WHERE market_id = %s ORDER BY traded_at, id",
        (market_id,),
    )
    if market["status"] == "resolved" and market["resolved_at"]:
        chart_end = market["resolved_at"]
    else:
        chart_end = min(market["now"], market["closes_at"])
    chart = odds_points(
        market["created_at"], chart_end,
        [(row["traded_at"], row["price_before"], row["price_after"]) for row in history], probability,
    )
    recent_trades = query_all(
        "SELECT u.display_name, t.side, t.shares, t.cost_cents, t.traded_at AT TIME ZONE 'America/New_York' AS traded_local "
        "FROM trades t JOIN users u ON u.id = t.user_id WHERE t.market_id = %s ORDER BY t.traded_at DESC, t.id DESC LIMIT 10",
        (market_id,),
    )
    comments = query_all(
        "SELECT u.display_name, c.body, c.created_at AT TIME ZONE 'America/New_York' AS created_local "
        "FROM comments c JOIN users u ON u.id = c.user_id WHERE c.market_id = %s ORDER BY c.created_at DESC, c.id DESC",
        (market_id,),
    )
    my_forecast = query_one(
        "SELECT probability, justification FROM forecasts WHERE market_id = %s AND user_id = %s "
        "ORDER BY made_at DESC, id DESC LIMIT 1",
        (market_id, user_id),
    )
    crowd = query_one(
        "SELECT AVG(probability) AS average, count(*) AS people FROM ("
        "SELECT DISTINCT ON (user_id) probability FROM forecasts WHERE market_id = %s ORDER BY user_id, made_at DESC) last",
        (market_id,),
    )
    my_dispute = query_one(
        "SELECT status FROM disputes WHERE market_id = %s AND user_id = %s", (market_id, user_id)
    )
    can_settle = (
        market["status"] != "resolved" and market["has_closed"]
        and (market["creator_id"] == user_id or g.user.get("is_admin"))
    )
    return render_template(
        "market.html", market=market, probability=probability, tags=tags, chart=chart,
        chart_end=chart_end, recent_trades=recent_trades,
        comments=comments, my_forecast=my_forecast, crowd=crowd, my_dispute=my_dispute,
        can_settle=can_settle, csrf_token=generate_csrf,
    )


@markets.post("/markets/<int:market_id>/preview")
def preview(market_id):
    if not session.get("user_id"):
        abort(401)
    market = get_conn().execute("SELECT q_yes, q_no, b FROM markets WHERE id = %s AND status = 'open' AND closes_at > now()", (market_id,)).fetchone()
    if market is None:
        abort(404)
    try:
        shares = int(request.form.get("shares", ""))
        side = request.form.get("side")
        q_yes, q_no, b = (float(market[key]) for key in ("q_yes", "q_no", "b"))
        charge = trade_cost_cents(q_yes, q_no, side, shares, b)
        after = price_yes(q_yes + (shares if side == "yes" else 0), q_no + (shares if side == "no" else 0), b)
    except (ValueError, OverflowError):
        flash("Choose a side and enter a valid positive number of shares.")
        return redirect(url_for("markets.market_detail", market_id=market_id))
    return render_template("trade_preview.html", market_id=market_id, side=side, shares=shares, charge=charge, after=after, csrf_token=generate_csrf)


@markets.post("/markets/<int:market_id>/trade")
def trade(market_id):
    user_id = session.get("user_id")
    if not user_id:
        abort(401)
    try:
        shares = int(request.form.get("shares", ""))
        charge = int(request.form.get("charge", ""))
        buy_shares(get_conn(), user_id, market_id, request.form.get("side"), shares, charge)
        flash("Purchase complete.")
    except (ValueError, OverflowError) as exc:
        flash(str(exc) if isinstance(exc, TradeError) else "Invalid purchase.")
    return redirect(url_for("markets.market_detail", market_id=market_id))


def settle_market(conn, market_id, user_id, outcome, is_admin=False):
    if outcome not in ("yes", "no"):
        raise TradeError("Choose yes or no.")

    with conn.transaction():
        market = conn.execute(
            "SELECT creator_id, status, closes_at <= now() AS has_closed FROM markets WHERE id = %s FOR UPDATE",
            (market_id,),
        ).fetchone()
        if market is None:
            raise TradeError("This market does not exist.")
        if market["creator_id"] != user_id and not is_admin:
            raise TradeError("Only the creator or an admin can settle this market.")
        if market["status"] == "resolved":
            raise TradeError("This market is already settled.")
        if not market["has_closed"]:
            raise TradeError("You can settle a market only after its closing date.")

        holders = conn.execute(
            "SELECT user_id, shares_yes, shares_no FROM positions WHERE market_id = %s",
            (market_id,),
        ).fetchall()
        total = 0
        for row in holders:
            amount = payout_cents(row["shares_yes"], row["shares_no"], outcome)
            if amount > 0:
                conn.execute(
                    "UPDATE users SET balance_cents = balance_cents + %s WHERE id = %s",
                    (amount, row["user_id"]),
                )
                total += amount

        conn.execute(
            "UPDATE markets SET status = 'resolved', outcome = %s, resolved_at = now() WHERE id = %s",
            (outcome, market_id),
        )
    return total


@markets.post("/markets/<int:market_id>/settle")
def settle(market_id):
    user_id = session.get("user_id")
    if not user_id:
        abort(401)
    try:
        paid = settle_market(get_conn(), market_id, user_id, request.form.get("outcome"), bool(g.user.get("is_admin")))
        flash(f"Market settled. {paid / 100:,.2f} coins paid to winners.")
    except TradeError as exc:
        flash(str(exc))
    return redirect(url_for("markets.market_detail", market_id=market_id))


@markets.get("/profile")
def profile():
    user_id = session.get("user_id")
    positions = query_all(
        "SELECT m.id, m.question, m.status, m.outcome, p.shares_yes, p.shares_no "
        "FROM positions p JOIN markets m ON m.id = p.market_id "
        "WHERE p.user_id = %s AND (p.shares_yes > 0 OR p.shares_no > 0) ORDER BY m.closes_at",
        (user_id,),
    )
    trades = query_all(
        "SELECT t.traded_at AT TIME ZONE 'America/New_York' AS traded_local, m.id AS market_id, m.question, "
        "t.side, t.shares, t.cost_cents "
        "FROM trades t JOIN markets m ON m.id = t.market_id "
        "WHERE t.user_id = %s ORDER BY t.traded_at DESC LIMIT 50",
        (user_id,),
    )
    last_forecasts = query_all(
        "SELECT DISTINCT ON (f.market_id) f.probability, m.outcome "
        "FROM forecasts f JOIN markets m ON m.id = f.market_id "
        "WHERE f.user_id = %s AND m.status = 'resolved' AND f.made_at < m.closes_at "
        "ORDER BY f.market_id, f.made_at DESC",
        (user_id,),
    )
    score = mean_brier([(float(row["probability"]), row["outcome"]) for row in last_forecasts])
    return render_template(
        "profile.html", positions=positions, trades=trades, brier=score, scored=len(last_forecasts)
    )
