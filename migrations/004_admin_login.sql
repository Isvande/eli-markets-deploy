-- Gives the existing Eli Markets admin account the demo login from seed.sql.
-- Run after 003. Safe to rerun

BEGIN;

DO $$
BEGIN
    IF (SELECT count(*) FROM users WHERE display_name = 'Eli Markets' AND is_admin) <> 1 THEN
        RAISE EXCEPTION 'Expected exactly one Eli Markets admin account. Nothing was changed';
    END IF;
    IF EXISTS (SELECT 1 FROM users WHERE yale_email = 'elimarkets-admin@yale.edu'
               AND NOT (display_name = 'Eli Markets' AND is_admin)) THEN
        RAISE EXCEPTION 'Another account already uses elimarkets-admin@yale.edu. Nothing was changed';
    END IF;
END $$;

UPDATE users
SET yale_email = 'elimarkets-admin@yale.edu',
    password_hash = '$2b$12$38eniizFK30DJVeEKt4RM.3zhZfP3baW73vE4stcek5Lp5jFihWJi'
WHERE display_name = 'Eli Markets' AND is_admin;

COMMIT;
