from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import generate_csrf

from .compute import price_yes, trade_cost_cents
from .db import get_conn

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


@markets.get("/markets/<int:market_id>")
def market_detail(market_id):
    market = get_conn().execute(
        "SELECT *, (status = 'open' AND closes_at > now()) AS is_open FROM markets WHERE id = %s", (market_id,)
    ).fetchone()
    if market is None:
        abort(404)
    return render_template("market.html", market=market, probability=price_yes(float(market["q_yes"]), float(market["q_no"]), float(market["b"])), csrf_token=generate_csrf)


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
