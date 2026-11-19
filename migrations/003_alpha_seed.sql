-- Adds the Alpha seed data to a database that already has the 5 MVP questions
-- Run after 002. Everything here must match seed.sql exactly, so a
-- migrated database ends up the same as a fresh schema.sql + seed.sql one

BEGIN;

-- Stop before changing anything unless this database has the admin account and
-- the 5 original questions word for word, since everything below finds them by
-- their text. RAISE EXCEPTION aborts the whole transaction
DO $$
BEGIN
    IF (SELECT count(*) FROM users WHERE display_name = 'Eli Markets' AND is_admin) <> 1 THEN
        RAISE EXCEPTION 'Expected exactly one Eli Markets admin account. Nothing was changed';
    END IF;
    IF (SELECT count(*) FROM markets WHERE question IN (
            'Will classes be cancelled for snow during the spring 2027 semester?',
            'Will New Haven hit 0 degrees F or colder in January 2027?',
            'Will New Haven get 12 or more inches of snow in a single day this winter?',
            'Will Yale win "The Game" in 2027?',
            'Will Yale''s admission rate for the Class of 2031 be under 4%?'
        )) <> 5 THEN
        RAISE EXCEPTION 'Expected the 5 original questions word for word. Nothing was changed';
    END IF;
END $$;

-- The categories. ON CONFLICT skips any tag that's already there
INSERT INTO tags (name)
VALUES ('sports'), ('weather'), ('campus'), ('dining'), ('academics')
ON CONFLICT (name) DO NOTHING;

-- The Game now closes at kickoff instead of 11:59 pm
UPDATE markets
SET closes_at = '2027-11-20 12:00:00 America/New_York'
WHERE question = 'Will Yale win "The Game" in 2027?';

-- The admit rate rule now names the decision-day announcement, and the question
-- closes before decisions go out on Ivy Day
UPDATE markets
SET resolution_rule = 'Resolves YES if the overall admission rate for the Class of 2031 (all rounds combined) in Yale''s decision-day announcement is below 4.00%. If the announcement gives only counts, admits divided by applicants is used. Resolves NO if it is 4.00% or higher, or if Yale has not announced it by May 1, 2027.',
    closes_at = '2027-03-25 18:00:00 America/New_York'
WHERE question = 'Will Yale''s admission rate for the Class of 2031 be under 4%?';

-- Tag the 5 original questions. ON CONFLICT skips pairs that already exist
INSERT INTO market_tags (market_id, tag_id)
SELECT markets.id, tags.id
FROM (VALUES
    ('Will classes be cancelled for snow during the spring 2027 semester?', 'weather'),
    ('Will classes be cancelled for snow during the spring 2027 semester?', 'campus'),
    ('Will New Haven hit 0 degrees F or colder in January 2027?', 'weather'),
    ('Will New Haven get 12 or more inches of snow in a single day this winter?', 'weather'),
    ('Will Yale win "The Game" in 2027?', 'sports'),
    ('Will Yale''s admission rate for the Class of 2031 be under 4%?', 'academics')
) AS v (question, tag)
JOIN markets ON markets.question = v.question
JOIN tags ON tags.name = v.tag
ON CONFLICT DO NOTHING;

-- The 15 new questions, tagged the same way as in seed.sql. Each one is inserted
-- only if a question with the same text isn't already there, so a rerun adds
-- nothing. 

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale men''s hockey beat Harvard at Ingalls on January 1, 2027?',
        'New Year''s Day rivalry game at the Whale.',
        'Resolves YES if Yale has more goals than Harvard at the end of regulation or overtime in the men''s ice hockey game at Ingalls Rink scheduled for January 1, 2027, according to the final box score on yalebulldogs.com. A shootout does not count. Resolves NO if Harvard wins or the game ends tied, or if it is not played by January 31, 2027.',
        TIMESTAMPTZ '2027-01-01 19:00:00 America/New_York'   -- scheduled puck drop
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale men''s hockey beat Harvard at Ingalls on January 1, 2027?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will it snow on the first day of spring classes?',
        'Spring term starts January 19, 2027.',
        'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows 0.1 inches or more of snowfall on January 19, 2027. Resolves NO otherwise, including a trace.',
        TIMESTAMPTZ '2027-01-18 23:59:00 America/New_York'
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will it snow on the first day of spring classes?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('weather', 'campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale raise the 2027-28 term bill by more than 4%?',
        'The term bill has gone up just under 4% every year since 2015.',
        'Resolves YES if Yale''s official announcement of the 2027-28 Yale College term bill (tuition plus housing and meals) shows an increase of more than 4.0% over 2026-27. Resolves NO if the increase is 4.0% or less, or if Yale has not announced it by June 30, 2027.',
        TIMESTAMPTZ '2027-01-31 23:59:00 America/New_York'   -- estimated: the 2025-26 bill came out February 10
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale raise the 2027-28 term bill by more than 4%?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale''s housing and meals charge for 2027-28 go up by more than 4%?',
        'What a year of dining hall swipes and a room will cost next year.',
        'Resolves YES if Yale''s official announcement of the 2027-28 Yale College term bill shows the housing and meals charge rising by more than 4.0% over 2026-27. Resolves NO if it rises 4.0% or less, or if Yale has not announced it by June 30, 2027.',
        TIMESTAMPTZ '2027-01-31 23:59:00 America/New_York'   -- estimated, same announcement as the term bill
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale''s housing and meals charge for 2027-28 go up by more than 4%?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('dining', 'campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale beat Harvard in men''s basketball at Lee Amphitheater on February 12, 2027?',
        'The second Yale-Harvard game of the Ivy season, in New Haven.',
        'Resolves YES if Yale beats Harvard in the men''s basketball game at John J. Lee Amphitheater scheduled for February 12, 2027, according to the final box score on yalebulldogs.com. Resolves NO if Harvard wins or if the game is not played by March 6, 2027.',
        TIMESTAMPTZ '2027-02-12 17:00:00 America/New_York'   -- estimated: tip time not announced yet
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale beat Harvard in men''s basketball at Lee Amphitheater on February 12, 2027?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will the AFC champion win Super Bowl LXI?',
        'February 14, 2027 at SoFi Stadium.',
        'Resolves YES if the AFC team wins Super Bowl LXI, per the NFL''s official final score. Resolves NO if the NFC team wins, or if the game is not played by March 31, 2027.',
        TIMESTAMPTZ '2027-02-14 18:00:00 America/New_York'   -- estimated: kickoff time not announced yet
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will the AFC champion win Super Bowl LXI?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale men''s basketball win or share the 2026-27 Ivy League regular-season title?',
        'The Ivy schedule ends at home against Princeton on March 6.',
        'Resolves YES if Yale finishes with the best Ivy League record, alone or tied, in the final 2026-27 regular-season standings on ivyleague.com. Resolves NO otherwise.',
        TIMESTAMPTZ '2027-03-05 23:59:00 America/New_York'   -- night before the last regular-season games
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale men''s basketball win or share the 2026-27 Ivy League regular-season title?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale win the 2027 Ivy League men''s basketball tournament?',
        'Ivy Madness returns to the Palestra for its 100th anniversary, with the NCAA bid on the line.',
        'Resolves YES if Yale wins the championship game of the 2027 Ivy League men''s basketball tournament, according to ivyleague.com. Resolves NO if another team wins, if Yale does not qualify, or if the tournament is not held.',
        TIMESTAMPTZ '2027-03-12 23:59:00 America/New_York'   -- estimated: tournament is the weekend after March 6
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale win the 2027 Ivy League men''s basketball tournament?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale get more than 55,000 applications for the Class of 2031?',
        'The Class of 2030 drew 54,919 applications as of decision day.',
        'Resolves YES if Yale''s decision-day announcement for the Class of 2031 reports more than 55,000 total applications (all rounds combined). Resolves NO if it reports 55,000 or fewer, or if Yale has not announced it by May 1, 2027.',
        TIMESTAMPTZ '2027-03-25 18:00:00 America/New_York'   -- estimated Ivy Day, same as the admit rate question
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale get more than 55,000 applications for the Class of 2031?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will a New Haven restaurant or chef be a 2027 James Beard Award finalist?',
        'Pizza town has a shot at the Oscars of food.',
        'Resolves YES if the James Beard Foundation''s list of 2027 Restaurant and Chef Award finalists includes a restaurant in New Haven, CT, or a chef nominated for a New Haven restaurant. Resolves NO otherwise.',
        TIMESTAMPTZ '2027-03-29 23:59:00 America/New_York'   -- estimated: 2026 finalists came out March 31
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will a New Haven restaurant or chef be a 2027 James Beard Award finalist?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('dining');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will it rain on Commencement, May 24, 2027?',
        'Umbrellas on Old Campus or not.',
        'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows 0.01 inches or more of precipitation on May 24, 2027. Resolves NO otherwise, including a trace.',
        TIMESTAMPTZ '2027-05-23 23:59:00 America/New_York'
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will it rain on Commencement, May 24, 2027?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('weather', 'campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale''s endowment return at least 10% for fiscal 2027?',
        'After a 26.3% return in fiscal 2026, can it keep going?',
        'Resolves YES if the investment return Yale reports for the fiscal year ending June 30, 2027 is 10.0% or higher. Resolves NO if it is lower, or if Yale has not reported it by December 31, 2027.',
        TIMESTAMPTZ '2027-06-30 23:59:00 America/New_York'   -- fiscal year ends: the result is fixed from here
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale''s endowment return at least 10% for fiscal 2027?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will Yale rank in the top 3 of the next U.S. News national universities list?',
        'Yale was 4th on the list released September 22, 2026.',
        'Resolves YES if the U.S. News & World Report Best National Universities ranking released in fall 2027 places Yale 3rd or higher, including ties. Resolves NO otherwise, or if no new list is released by December 31, 2027.',
        TIMESTAMPTZ '2027-09-13 23:59:00 America/New_York'   -- estimated: the last two lists came out September 22 and 23
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will Yale rank in the top 3 of the next U.S. News national universities list?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will a Yale faculty member win a 2027 Nobel Prize?',
        'Six prizes, one week in October.',
        'Resolves YES if any 2027 Nobel Prize, including economics, goes to someone nobelprize.org lists with Yale University as their affiliation at the time of the award. Resolves NO otherwise.',
        TIMESTAMPTZ '2027-10-04 05:00:00 America/New_York'   -- estimated: first prize is announced at 5:30 am ET
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will a Yale faculty member win a 2027 Nobel Prize?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    SELECT
        (SELECT id FROM users WHERE display_name = 'Eli Markets' AND is_admin),
        'Will at least two Yalies be named 2028 U.S. Rhodes Scholars?',
        'Three Yalies won for 2026.',
        'Resolves YES if the Rhodes Trust''s announcement of the U.S. Rhodes Scholars-elect for 2028 (expected November 2027) lists at least two Yale students or recent graduates. Resolves NO otherwise.',
        TIMESTAMPTZ '2027-11-19 23:59:00 America/New_York'   -- estimated: announced the weekend before Thanksgiving
    WHERE NOT EXISTS (SELECT 1 FROM markets WHERE question = 'Will at least two Yalies be named 2028 U.S. Rhodes Scholars?')
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

-- Last check: every question must have at least one tag. If one doesn't, the
-- error names it and the whole migration rolls back
DO $$
DECLARE
    untagged TEXT;
BEGIN
    SELECT question INTO untagged
    FROM markets m
    WHERE NOT EXISTS (SELECT 1 FROM market_tags mt WHERE mt.market_id = m.id)
    LIMIT 1;
    IF untagged IS NOT NULL THEN
        RAISE EXCEPTION 'Question has no tag: %. Nothing was changed', untagged;
    END IF;
END $$;

COMMIT;
