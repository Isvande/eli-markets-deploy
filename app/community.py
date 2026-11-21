from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_conn, query_all, query_one

community = Blueprint("community", __name__)


def _back(market_id):
    return redirect(url_for("markets.market_detail", market_id=market_id))


@community.post("/markets/<int:market_id>/forecast")
def forecast(market_id):
    market = query_one(
        "SELECT id FROM markets WHERE id = %s AND status = 'open' AND closes_at > now()", (market_id,)
    )
    if market is None:
        flash("Forecasts are only accepted while a question is open.", "error")
        return _back(market_id)
    try:
        percent = float(request.form.get("probability", ""))
    except ValueError:
        percent = -1
    justification = request.form.get("justification", "").strip()
    if not 0 <= percent <= 100:
        flash("Enter a probability from 0 to 100.", "error")
    elif len(justification) > 500:
        flash("Keep your reasoning under 500 characters.", "error")
    else:
        get_conn().execute(
            "INSERT INTO forecasts (user_id, market_id, probability, justification) VALUES (%s, %s, %s, %s)",
            (g.user["id"], market_id, round(percent / 100, 4), justification or None),
        )
        flash("Forecast saved. Your last forecast before the question closes is the one that's scored.", "success")
    return _back(market_id)


@community.post("/markets/<int:market_id>/comments")
def comment(market_id):
    body = request.form.get("body", "").strip()
    if query_one("SELECT id FROM markets WHERE id = %s", (market_id,)) is None:
        flash("That question does not exist.", "error")
        return redirect(url_for("index"))
    if not 1 <= len(body) <= 2000:
        flash("Comments must be 1 to 2,000 characters.", "error")
    else:
        get_conn().execute(
            "INSERT INTO comments (user_id, market_id, body) VALUES (%s, %s, %s)",
            (g.user["id"], market_id, body),
        )
    return _back(market_id)


@community.post("/markets/<int:market_id>/dispute")
def dispute(market_id):
    reason = request.form.get("reason", "").strip()
    market = query_one("SELECT status FROM markets WHERE id = %s", (market_id,))
    if market is None or market["status"] != "resolved":
        flash("You can only flag a question after it has been settled.", "error")
    elif not 10 <= len(reason) <= 1000:
        flash("Explain in 10 to 1,000 characters why the result is wrong.", "error")
    else:
        row = query_one(
            "INSERT INTO disputes (market_id, user_id, reason) VALUES (%s, %s, %s) "
            "ON CONFLICT (market_id, user_id) DO NOTHING RETURNING id",
            (market_id, g.user["id"], reason),
        )
        if row is None:
            flash("You have already flagged this result.", "error")
        else:
            flash("Thanks. An admin will review the result.", "success")
    return _back(market_id)


@community.get("/leaderboard")
def leaderboard():
    by = "brier" if request.args.get("by") == "brier" else "coins"
    if by == "coins":
        rows = query_all(
            "SELECT id, display_name, balance_cents FROM users "
            "WHERE yale_email IS NOT NULL AND is_admin IS NOT TRUE ORDER BY balance_cents DESC, id LIMIT 50"
        )
    else:
        rows = query_all(
            """
            WITH last AS (
                SELECT DISTINCT ON (f.user_id, f.market_id) f.user_id, f.probability, m.outcome
                FROM forecasts f JOIN markets m ON m.id = f.market_id
                WHERE m.status = 'resolved' AND f.made_at < m.closes_at
                ORDER BY f.user_id, f.market_id, f.made_at DESC
            )
            SELECT u.id, u.display_name,
                   AVG(power(last.probability - CASE WHEN last.outcome = 'yes' THEN 1 ELSE 0 END, 2)) AS brier,
                   count(*) AS scored
            FROM last JOIN users u ON u.id = last.user_id
            WHERE u.is_admin IS NOT TRUE
            GROUP BY u.id, u.display_name
            ORDER BY brier, scored DESC, u.id
            LIMIT 50
            """
        )
    return render_template("leaderboard.html", rows=rows, by=by)
