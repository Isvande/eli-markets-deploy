# Connect to PostgreSQL: one connection per request plus 2 query helpers

import os

import psycopg
from psycopg.rows import dict_row
from flask import g

def get_conn():
    if "db_conn" not in g:
        g.db_conn = psycopg.connet(
            os.environ["DATABASE_URL"],
            autocommit=True,
            row_factory=dict_row,
        )
    return g.db_conn

def close_conn(e=None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()

def query_one(sql, params=None):
    return get_conn().execute(sql, params).fetchone()

def query_all(sql, params=None):
    return get_conn().execute(sql, params).fetchall()