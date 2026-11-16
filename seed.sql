-- Eli Markets seed data: the admin account, 5 tags and 20 questions
-- Run after schema.sql: schema wipes the tables so the pair can be rerun
-- Dates marked "estimated" aren't announced yet so will have to double check

BEGIN;

-- The admin account: no email or password hash so nobody can log in as it
INSERT INTO users (display_name, yale_email, password_hash, is_admin)
VALUES ('Eli Markets', NULL, NULL, TRUE);

-- The categories for the home page filter
INSERT INTO tags (name)
VALUES ('sports'), ('weather'), ('campus'), ('dining'), ('academics');

-- Each question below is one statement: the WITH part inserts the question and
-- hands back its new id, then the second part tags that id.
-- No hand typed ids = no question tagging mistakes

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will classes be cancelled for snow during the spring 2027 semester?',
        'Snow days are rare, will we get one this winter?',
        'Resolves YES if Yale officially cancels all in-person undergraduate classes for at least one full day because of weather between January 1 and April 30, 2027. Resolves NO otherwise, including delayed openings or cancellations of only some classes.',
        '2027-04-30 23:59:00 America/New_York'  -- classes end April 30
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('weather', 'campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will New Haven hit 0 degrees F or colder in January 2027?',
        'How cold does January get this year?',
        'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows a minimum temperature of 0 degrees F or lower on any day from January 1 through January 31, 2027. Resolves NO otherwise.',
        '2027-01-31 23:59:00 America/New_York'
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('weather');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will New Haven get 12 or more inches of snow in a single day this winter?',
        'One big storm is all it takes.',
        'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows 12.0 inches or more of snowfall on any single calendar day from December 1, 2026 through February 28, 2027. Resolves NO otherwise.',
        '2027-02-28 23:59:00 America/New_York'
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('weather');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale win "The Game" in 2027?',
        'The 143rd edition of the oldest rivalry in college football.',
        'Resolves YES if Yale defeats Harvard in their 2027 varsity football game, according to the official final score posted by Yale Athletics. Resolves NO if Harvard wins or if the game is not played by December 31, 2027.',
        '2027-11-20 12:00:00 America/New_York'   -- estimated kickoff
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale''s admission rate for the Class of 2031 be under 4%?',
        'Admission keeps getting more competitive, will the trend continue?',
        'Resolves YES if the overall admission rate for the Class of 2031 (all rounds combined) in Yale''s decision-day announcement is below 4.00%. If the announcement gives only counts, admits divided by applicants is used. Resolves NO if it is 4.00% or higher, or if Yale has not announced it by May 1, 2027.',
        '2027-03-25 18:00:00 America/New_York'   -- estimated Ivy Day, decisions go out at 7 pm
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale men''s hockey beat Harvard at Ingalls on January 1, 2027?',
        'New Year''s Day rivalry game at the Whale.',
        'Resolves YES if Yale has more goals than Harvard at the end of regulation or overtime in the men''s ice hockey game at Ingalls Rink scheduled for January 1, 2027, according to the final box score on yalebulldogs.com. A shootout does not count. Resolves NO if Harvard wins or the game ends tied, or if it is not played by January 31, 2027.',
        '2027-01-01 19:00:00 America/New_York'   -- scheduled puck drop
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will it snow on the first day of spring classes?',
        'Spring term starts January 19, 2027.',
        'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows 0.1 inches or more of snowfall on January 19, 2027. Resolves NO otherwise, including a trace.',
        '2027-01-18 23:59:00 America/New_York'
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('weather', 'campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale raise the 2027-28 term bill by more than 4%?',
        'The term bill has gone up just under 4% every year since 2015.',
        'Resolves YES if Yale''s official announcement of the 2027-28 Yale College term bill (tuition plus housing and meals) shows an increase of more than 4.0% over 2026-27. Resolves NO if the increase is 4.0% or less, or if Yale has not announced it by June 30, 2027.',
        '2027-01-31 23:59:00 America/New_York'   -- estimated: the 2025-26 bill came out February 10
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale''s housing and meals charge for 2027-28 go up by more than 4%?',
        'What a year of dining hall swipes and a room will cost next year.',
        'Resolves YES if Yale''s official announcement of the 2027-28 Yale College term bill shows the housing and meals charge rising by more than 4.0% over 2026-27. Resolves NO if it rises 4.0% or less, or if Yale has not announced it by June 30, 2027.',
        '2027-01-31 23:59:00 America/New_York'   -- estimated, same announcement as the term bill
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('dining', 'campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale beat Harvard in men''s basketball at Lee Amphitheater on February 12, 2027?',
        'The second Yale-Harvard game of the Ivy season, in New Haven.',
        'Resolves YES if Yale beats Harvard in the men''s basketball game at John J. Lee Amphitheater scheduled for February 12, 2027, according to the final box score on yalebulldogs.com. Resolves NO if Harvard wins or if the game is not played by March 6, 2027.',
        '2027-02-12 17:00:00 America/New_York'   -- estimated: tip time not announced yet
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will the AFC champion win Super Bowl LXI?',
        'February 14, 2027 at SoFi Stadium.',
        'Resolves YES if the AFC team wins Super Bowl LXI, per the NFL''s official final score. Resolves NO if the NFC team wins, or if the game is not played by March 31, 2027.',
        '2027-02-14 18:00:00 America/New_York'   -- estimated: kickoff time not announced yet
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale men''s basketball win or share the 2026-27 Ivy League regular-season title?',
        'The Ivy schedule ends at home against Princeton on March 6.',
        'Resolves YES if Yale finishes with the best Ivy League record, alone or tied, in the final 2026-27 regular-season standings on ivyleague.com. Resolves NO otherwise.',
        '2027-03-05 23:59:00 America/New_York'   -- night before the last regular-season games
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale win the 2027 Ivy League men''s basketball tournament?',
        'Ivy Madness returns to the Palestra for its 100th anniversary, with the NCAA bid on the line.',
        'Resolves YES if Yale wins the championship game of the 2027 Ivy League men''s basketball tournament, according to ivyleague.com. Resolves NO if another team wins, if Yale does not qualify, or if the tournament is not held.',
        '2027-03-12 23:59:00 America/New_York'   -- estimated: tournament is the weekend after March 6
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('sports');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale get more than 55,000 applications for the Class of 2031?',
        'The Class of 2030 drew 54,919 applications as of decision day.',
        'Resolves YES if Yale''s decision-day announcement for the Class of 2031 reports more than 55,000 total applications (all rounds combined). Resolves NO if it reports 55,000 or fewer, or if Yale has not announced it by May 1, 2027.',
        '2027-03-25 18:00:00 America/New_York'   -- estimated Ivy Day, same as the admit rate question
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will a New Haven restaurant or chef be a 2027 James Beard Award finalist?',
        'Pizza town has a shot at the Oscars of food.',
        'Resolves YES if the James Beard Foundation''s list of 2027 Restaurant and Chef Award finalists includes a restaurant in New Haven, CT, or a chef nominated for a New Haven restaurant. Resolves NO otherwise.',
        '2027-03-29 23:59:00 America/New_York'   -- estimated: 2026 finalists came out March 31
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('dining');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will it rain on Commencement, May 24, 2027?',
        'Umbrellas on Old Campus or not.',
        'Resolves YES if the National Weather Service daily climate report for Tweed-New Haven Airport shows 0.01 inches or more of precipitation on May 24, 2027. Resolves NO otherwise, including a trace.',
        '2027-05-23 23:59:00 America/New_York'
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('weather', 'campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale''s endowment return at least 10% for fiscal 2027?',
        'After a 26.3% return in fiscal 2026, can it keep going?',
        'Resolves YES if the investment return Yale reports for the fiscal year ending June 30, 2027 is 10.0% or higher. Resolves NO if it is lower, or if Yale has not reported it by December 31, 2027.',
        '2027-06-30 23:59:00 America/New_York'   -- fiscal year ends: the result is fixed from here
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('campus');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will Yale rank in the top 3 of the next U.S. News national universities list?',
        'Yale was 4th on the list released September 22, 2026.',
        'Resolves YES if the U.S. News & World Report Best National Universities ranking released in fall 2027 places Yale 3rd or higher, including ties. Resolves NO otherwise, or if no new list is released by December 31, 2027.',
        '2027-09-13 23:59:00 America/New_York'   -- estimated: the last two lists came out September 22 and 23
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will a Yale faculty member win a 2027 Nobel Prize?',
        'Six prizes, one week in October.',
        'Resolves YES if any 2027 Nobel Prize, including economics, goes to someone nobelprize.org lists with Yale University as their affiliation at the time of the award. Resolves NO otherwise.',
        '2027-10-04 05:00:00 America/New_York'   -- estimated: first prize is announced at 5:30 am ET
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

WITH m AS (
    INSERT INTO markets (creator_id, question, description, resolution_rule, closes_at)
    VALUES (
        (SELECT id FROM users WHERE display_name = 'Eli Markets'),
        'Will at least two Yalies be named 2028 U.S. Rhodes Scholars?',
        'Three Yalies won for 2026.',
        'Resolves YES if the Rhodes Trust''s announcement of the U.S. Rhodes Scholars-elect for 2028 (expected November 2027) lists at least two Yale students or recent graduates. Resolves NO otherwise.',
        '2027-11-19 23:59:00 America/New_York'   -- estimated: announced the weekend before Thanksgiving
    )
    RETURNING id
)
INSERT INTO market_tags (market_id, tag_id)
SELECT m.id, tags.id FROM m, tags WHERE tags.name IN ('academics');

COMMIT;
