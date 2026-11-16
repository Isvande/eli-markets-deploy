-- Eli markets schema: the 9 tables plus sessions for logins
-- Rerunnable: the drop below wipes the tables (and their data) every run
-- Money is in integer cents, so 100000 is 1000 coins

DROP TABLE IF EXISTS sessions, disputes, comments, forecasts, market_tags, tags, sessions, positions, trades, markets, users CASCADE;

-- Everyone who can hold coins: students, the admin account, the AI player
CREATE TABLE users (
    id            SERIAL PRIMARY KEY, 
    yale_email    TEXT UNIQUE, 
    password_hash TEXT, 
    display_name  TEXT NOT NULL,
    balance_cents INTEGER NOT NULL DEFAULT 100000 CHECK (balance_cents >= 0),
    is_ai         BOOLEAN DEFAULT FALSE,
    model_name    TEXT,
    is_admin      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT now() 
);

CREATE TABLE sessions (
    session_id   TEXT PRIMARY KEY,
    session_data TEXT NOT NULL,
    expires_at   TIMESTAMPTZ NOT NULL
);

CREATE INDEX sessions_expires_at_index ON sessions (expires_at);

-- One row per question, q_yes, q_no and b are the LMSR parameters 
CREATE TABLE markets (
    id              SERIAL PRIMARY KEY,
    creator_id      INTEGER REFERENCES users (id),
    question        TEXT NOT NULL,
    description     TEXT,
    resolution_rule TEXT NOT NULL,
    closes_at       TIMESTAMPTZ NOT NULL, 
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'resolved')),
    outcome         TEXT NULL CHECK (outcome IN ('yes', 'no')),
    b               NUMERIC NOT NULL DEFAULT 100,                                                    -- liquidity parameter: 100 for every market, changing it after trades exist reprices the market
    q_yes           NUMERIC NOT NULL DEFAULT 0,
    q_no            NUMERIC NOT NULL DEFAULT 0,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Every buy ever made and the price history for the odds chart
CREATE TABLE trades (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users (id),
    market_id    INTEGER NOT NULL REFERENCES markets (id),
    side         TEXT NOT NULL CHECK (side IN ('yes', 'no')),
    shares       INTEGER NOT NULL CHECK (shares > 0),
    cost_cents   INTEGER NOT NULL,
    price_before NUMERIC NOT NULL, 
    price_after  NUMERIC NOT NULL,
    traded_at    TIMESTAMPTZ DEFAULT now()
);

-- What each user currently holds in each market (many-to-many)
CREATE TABLE positions (
    user_id    INTEGER REFERENCES users (id),
    market_id  INTEGER REFERENCES markets (id),
    shares_yes INTEGER NOT NULL DEFAULT 0,
    shares_no  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, market_id)
);

-- Categories for the home page filter (sports, weather, campus, dining, academics)
CREATE TABLE tags (
    id   SERIAL PRIMARY KEY, 
    name TEXT UNIQUE NOT NULL
);

-- Which tags each question has (many-to-many, one row per question-tag pair)
CREATE TABLE market_tags (
    market_id INTEGER REFERENCES markets (id),
    tag_id    INTEGER REFERENCES tags (id),
    PRIMARY KEY (market_id, tag_id)
);

-- Every probability a student posts, not just the latest. The Brier score
-- uses each student's last forecast made before the question closed
CREATE TABLE forecasts (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users (id),
    market(id)    INTEGER NOT NULL REFERENCES markets(id),
    probability   NUMERIC NOT NULL CHECK (probability BETWEEN 0 AND 1),
    justification TEXT,
    made_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Discussion on each question page
CREATE TABLE comments (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users (id),
    market_id  INTEGER NOT NULL REFERENCES markets(id),
    body       TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- A student flagging a settled result for admin review, once per question.
-- decided_by stays NULL until an admin rules on it
CREATE TABLE disputes (
    id         SERIAL PRIMARY KEY,
    market_id  INTEGER NOT NULL REFERENCES markets (id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    reason     TEXT,
    status     TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'upheld', 'overturned')),
    decided_by INTEGER REFERENCES users (id),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (market_id, user_id)
);

-- Home page: open questions, ordered by closing time
CREATE INDEX markets_status_closes_at_index ON markets (status, closes_at);

-- Question page and odds chart: one market's trades, ordered by time made
CREATE INDEX trades_market_id_traded_at_index ON trades (market_id, traded_at);

--Question page: one market's comments, newest first
CREATE INDEX comments_market_id_created_at_index ON comments (market_id, created_at);

-- Brier score: each student's forecasts on one market
CREATE INDEX forecasts_market_id_user_id_index ON forecasts (market_id, uder_id, made_at);
