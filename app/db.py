"""Database access for Eli Markets.

Use query_one for a SELECT that returns one row, and query_all for one that
returns several. Both return dicts keyed by column name.
"""

import os

import psycopg
from psycopg.rows import dict_row
from flask import g

def get_conn():
    """Return this request's database connection, opening it on first use."""
    if "db_conn" not in g:
        g.db_conn = psycopg.connect(
            os.environ["DATABASE_URL"],
            autocommit=True,
            row_factory=dict_row,
        )
    return g.db_conn

def close_conn(e=None):
    """Close this request's connection, if one was opened (flask uses for teardown)."""
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()

def query_one(sql, params=None):
    """Run a SELECT and return its first row as a dict or None if nothing matched."""
    return get_conn().execute(sql, params).fetchone()

def query_all(sql, params=None):
    """Run a SELECT and return every row as a list of dicts, or [] if nothing matched."""
    return get_conn().execute(sql, params).fetchall()
