from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .compute import payout_cents
from .db import get_conn, query_all, query_one
from .markets import TradeError

admin = Blueprint("admin", __name__)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None or not g.user.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def parse_market_form(form, tag_ids):
    values = {
        "question": form.get("question", "").strip(),
        "description": form.get("description", "").strip(),
        "resolution_rule": form.get("resolution_rule", "").strip(),
        "closes_at": form.get("closes_at", "").strip(),
        "tags": [int(t) for t in form.getlist("tags") if t.isdigit() and int(t) in tag_ids],
    }
    errors = []
    if not 10 <= len(values["question"]) <= 300:
        errors.append("The question must be 10 to 300 characters.")
    if len(values["description"]) > 1000:
        errors.append("The description must be at most 1,000 characters.")
    if not 10 <= len(values["resolution_rule"]) <= 2000:
        errors.append("Write a resolution rule of 10 to 2,000 characters.")
    try:
        datetime.strptime(values["closes_at"], "%Y-%m-%dT%H:%M")
    except ValueError:
        errors.append("Choose a closing date and time.")
    else:
        # The form's time is New Haven time, and the server may run in UTC
        if not query_one(
            "SELECT %s::timestamp AT TIME ZONE 'America/New_York' > now() AS ok", (values["closes_at"],)
        )["ok"]:
            errors.append("The closing time must be in the future.")
    if not values["tags"]:
        errors.append("Pick at least one category.")
    return values, errors


@admin.route("/markets/new", methods=["GET", "POST"])
@admin_required
def new_market():
    tags = query_all("SELECT id, name FROM tags ORDER BY name")
    values, errors = {"tags": []}, []
    if request.method == "POST":
        values, errors = parse_market_form(request.form, {t["id"] for t in tags})
        if not errors:
            conn = get_conn()
            with conn.transaction():
                market = conn.execute(
                    "INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at) "
                    "VALUES (%s, %s, %s, %s, %s::timestamp AT TIME ZONE 'America/New_York') RETURNING id",
                    (g.user["id"], values["question"], values["description"] or None,
                     values["resolution_rule"], values["closes_at"]),
                ).fetchone()
                for tag_id in values["tags"]:
                    conn.execute(
                        "INSERT INTO market_tags (market_id, tag_id) VALUES (%s, %s)",
                        (market["id"], tag_id),
                    )
            flash("Question created.", "success")
            return redirect(url_for("markets.market_detail", market_id=market["id"]))
    return render_template("new_market.html", tags=tags, values=values, errors=errors)


@admin.get("/admin")
@admin_required
def dashboard():
    to_settle = query_all(
        "SELECT id, question, closes_at AT TIME ZONE 'America/New_York' AS closes_local "
        "FROM markets WHERE status <> 'resolved' AND closes_at <= now() ORDER BY closes_at"
    )
    disputes = query_all(
        "SELECT d.id, d.reason, d.created_at AT TIME ZONE 'America/New_York' AS created_local, "
        "u.display_name, m.id AS market_id, m.question, m.outcome "
        "FROM disputes d JOIN users u ON u.id = d.user_id JOIN markets m ON m.id = d.market_id "
        "WHERE d.status = 'open' ORDER BY d.created_at"
    )
    return render_template("admin.html", to_settle=to_settle, disputes=disputes)


def decide_dispute(conn, dispute_id, admin_id, decision):
    if decision not in ("upheld", "overturned"):
        raise TradeError("Choose uphold or overturn.")

    with conn.transaction():
        dispute = conn.execute(
            "SELECT d.status, d.market_id, m.outcome "
            "FROM disputes d JOIN markets m ON m.id = d.market_id WHERE d.id = %s FOR UPDATE OF d, m",
            (dispute_id,),
        ).fetchone()
        if dispute is None:
            raise TradeError("This dispute does not exist.")
        if dispute["status"] != "open":
            raise TradeError("This dispute has already been decided.")

        if decision == "upheld":
            conn.execute(
                "UPDATE disputes SET status = 'upheld', decided_by = %s WHERE id = %s",
                (admin_id, dispute_id),
            )
            return dispute["outcome"]

        old = dispute["outcome"]
        new = "no" if old == "yes" else "yes"
        holders = conn.execute(
            "SELECT user_id, shares_yes, shares_no FROM positions WHERE market_id = %s",
            (dispute["market_id"],),
        ).fetchall()
        for row in holders:
            change = payout_cents(row["shares_yes"], row["shares_no"], new) - payout_cents(
                row["shares_yes"], row["shares_no"], old
            )
            if change:
                # Someone who already spent a wrong payout can't go below 0 coins
                conn.execute(
                    "UPDATE users SET balance_cents = GREATEST(balance_cents + %s, 0) WHERE id = %s",
                    (change, row["user_id"]),
                )
        conn.execute(
            "UPDATE markets SET outcome = %s, resolved_at = now() WHERE id = %s",
            (new, dispute["market_id"]),
        )
        conn.execute(
            "UPDATE disputes SET status = 'overturned', decided_by = %s WHERE market_id = %s AND status = 'open'",
            (admin_id, dispute["market_id"]),
        )
    return new


@admin.post("/admin/disputes/<int:dispute_id>")
@admin_required
def decide(dispute_id):
    try:
        outcome = decide_dispute(get_conn(), dispute_id, g.user["id"], request.form.get("decision"))
        flash(f"Dispute decided. The question now stands as {outcome.upper()}.", "success")
    except TradeError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.dashboard"))
