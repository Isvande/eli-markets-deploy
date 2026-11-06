-- Eli Markets seed data 
-- Run after schema.sql: schema wipes the tables so the pair can be rerun

BEGIN;

-- The admin account: no email or password hash so nobody can log in as it
INSERT INTO users (display_name, yale_email, password_hash, is_admin)
VALUES ('Eli Markets', NULL, NULL, TRUE);

-- Five starter questions (all created by the admin account)
INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
VALUES 
(
    (SELECT id FROM users WHERE display_name = 'Eli Markets'),
    'Will classes be cancelled for snow during the spring 2027 semester?',
    'Snow days are rare, will we get one this winter?',
    'Resolves YES if Yale officially cancels all in-person undergraduate classes for at least one full day because of weather between January 1 and April 30, 2027. Resolves NO otherwise, including delayed openings or cancellations of only some classes.',
    '2027-04-30 23:59:00 America/New_York'
),
(
    (SELECT id FROM users WHERE display_name = 'Eli Markets'),
    'Will New Haven hit 0 degrees F or colder in January 2027?',
    'How cold does January get this year?',
    'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows a minimum temperature of 0 degrees F or lower on any day from January 1 through January 31, 2027. Resolves NO otherwise.',
    '2027-01-31 23:59:00 America/New_York'
),
(
    (SELECT id FROM users WHERE display_name = 'Eli Markets'),
    'Will New Haven get 12 or more inches of snow in a single day this winter?',
    'One big storm is all it takes.',
    'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows 12.0 inches or more of snowfall on any single calendar day from December 1, 2026 through February 28, 2027. Resolves NO otherwise.',
    '2027-02-28 23:59:00 America/New_York'
),
(
    (SELECT id FROM users WHERE display_name = 'Eli Markets'),
    'Will Yale win "The Game" in 2027?',
    'The 143rd edition of the oldest rivalry in college football.',
    'Resolves YES if Yale defeats Harvard in their 2027 varsity football game, according to the official final score posted by Yale Athletics. Resolves NO if Harvard wins or if the game is not played by December 31, 2027.',
    '2027-11-20 23:59:00 America/New_York'

),
(
    (SELECT id FROM users WHERE display_name = 'Eli Markets'),
    'Will Yale''s admission rate for the Class of 2031 be under 4%?',
    'Admission keeps getting more competitive, will the trend continue?',
    'Resolves YES if the overall admission rate Yale College officially reports for the Class of 2031 (all rounds combined) is below 4.00%. Resolves NO if it is 4.00% or higher, or if Yale has not published a rate by May 1, 2027.',
    '2027-03-30 23:59:00 America/New_York'
);

COMMIT;
