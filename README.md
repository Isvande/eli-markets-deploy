# cpsc-4190-26fa-project-group-1

# Eli Markets

A play-money prediction market for Yale students. CPSC 4190, Fall 2026.

## Run it locally

1. Install PostgreSQL (Mac):

   ```bash
   brew install postgresql@16
   brew services start postgresql@16
   createdb elimarkets
   ```

2. Set up Python:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. Load the database:

   ```bash
   psql elimarkets -f schema.sql
   psql elimarkets -f seed.sql
   ```

   **Warning:** `schema.sql` drops and recreates the app tables, including users
   and sessions. Run it only when you are willing to erase that database's data.
   If your app tables already exist, apply the safe sessions migration instead:

   ```bash
   psql elimarkets -f migrations/001_sessions.sql
   ```

4. Start the app:

   ```bash
   flask --app wsgi run
   ```

   Then open http://127.0.0.1:5000. To go straight to account creation, visit
   http://127.0.0.1:5000/signup.

   Sign up with a `@yale.edu` email address to create an account with 1,000 coins.
   Signup and login require the exact `@yale.edu` domain, but do not yet send a
   confirmation email to verify mailbox ownership.
   The local `.env.example` uses non-secure cookies for HTTP development; set
   `SESSION_COOKIE_SECURE=true` when serving the app over HTTPS.
