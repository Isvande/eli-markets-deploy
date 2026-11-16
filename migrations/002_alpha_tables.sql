-- Adds the Alpha tables to a database that already has users, markets and trades.
-- These definitions must match schema.sql exactly because IF NOT EXISTS skips a 
-- table that already exists even if its columns differ

BEGIN;

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY, 
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS market_tags (
    market_id INTEGER REFERENCES markets (id),
    tag_id INTEGER REFERENCES tags (id),
    PRIMARY KEY (market_id, tag_id)
);

CREATE TABLE IF NOT EXISTS forecasts (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users (id),
    market_id    INTEGER NOT NULL REFERENCES markets(id),
    probability   NUMERIC NOT NULL CHECK (probability BETWEEN 0 AND 1),
    justification TEXT,
    made_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS comments (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users (id),
    market_id  INTEGER NOT NULL REFERENCES markets(id),
    body       TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS disputes (
    id         SERIAL PRIMARY KEY,
    market_id  INTEGER NOT NULL REFERENCES markets (id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    reason     TEXT,
    status     TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'upheld', 'overturned')),
    decided_by INTEGER REFERENCES users (id),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (market_id, user_id)
);

CREATE INDEX IF NOT EXISTS comments_market_id_created_at_index ON comments (market_id, created_at);

CREATE INDEX IF NOT EXISTS forecasts_market_id_user_id_index ON forecasts (market_id, user_id, made_at);

COMMIT;