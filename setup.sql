/*
 Copyright (c) 2023-present Arjun Satarkar <me@arjunsatarkar.net>.
 Licensed under the GNU Affero General Public License v3.0. See LICENSE.txt in
 the root of this repository for the text of the license.
 */
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tagrss_info(info_key TEXT PRIMARY KEY, value TEXT) STRICT;

INSERT
    OR REPLACE INTO tagrss_info(info_key, value)
VALUES
    ("version", "0.12.0");

CREATE TABLE IF NOT EXISTS feed_count(
    id INTEGER PRIMARY KEY CHECK (id = 0),
    count INTEGER CHECK(count >= 0)
) STRICT;

INSERT
    OR IGNORE INTO feed_count(id, count)
VALUES
    (0, 0);

CREATE TABLE IF NOT EXISTS feeds(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT UNIQUE,
    title TEXT UNIQUE
) STRICT;

CREATE TRIGGER IF NOT EXISTS trig_feeds__increment_feed_count_after_insert
AFTER
INSERT
    ON feeds BEGIN
UPDATE
    feed_count
SET
    count = count + 1;

END;

CREATE TRIGGER IF NOT EXISTS trig_feeds__decrement_feed_count_after_delete
AFTER
    DELETE ON feeds BEGIN
UPDATE
    feed_count
SET
    count = count - 1;

END;

CREATE TABLE IF NOT EXISTS feed_tags(
    feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
    tag TEXT
) STRICT;

CREATE INDEX IF NOT EXISTS idx_feed_tags__feed_id__tag ON feed_tags(feed_id, tag);

CREATE INDEX IF NOT EXISTS idx_feed_tags__tag__feed_id ON feed_tags(tag, feed_id);

CREATE TABLE IF NOT EXISTS entry_count(
    id INTEGER PRIMARY KEY CHECK (id = 0),
    count INTEGER CHECK(count >= 0)
) STRICT;

INSERT
    OR IGNORE INTO entry_count(id, count)
VALUES
    (0, 0);

CREATE TABLE IF NOT EXISTS entries(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
    title TEXT,
    link TEXT,
    epoch_published INTEGER,
    epoch_updated INTEGER,
    epoch_downloaded INTEGER
) STRICT;

CREATE INDEX IF NOT EXISTS idx_entries__feed_id__title__link__epoch_published__epoch_updated ON entries(
    feed_id,
    title,
    link,
    epoch_published,
    epoch_updated
);

CREATE TRIGGER IF NOT EXISTS trig_entries__ensure_unique_with_identical_nulls_before_insert BEFORE
INSERT
    ON entries BEGIN
SELECT
    RAISE(IGNORE)
WHERE
    EXISTS (
        SELECT
            1
        FROM
            entries
        WHERE
            feed_id = NEW.feed_id
            AND title IS NEW.title
            AND link IS NEW.link
            AND epoch_published IS NEW.epoch_published
            AND epoch_updated IS NEW.epoch_updated
    );

END;

CREATE TRIGGER IF NOT EXISTS trig_entries__increment_entry_count_after_insert
AFTER
INSERT
    ON entries BEGIN
UPDATE
    entry_count
SET
    count = count + 1;

END;

CREATE TRIGGER IF NOT EXISTS trig_entries__decrement_entry_count_after_delete
AFTER
    DELETE ON entries BEGIN
UPDATE
    entry_count
SET
    count = count - 1;

END;