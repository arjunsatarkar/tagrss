PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tagrss_info(info_key TEXT PRIMARY KEY, value TEXT) STRICT;

INSERT
    OR REPLACE INTO tagrss_info(info_key, value)
VALUES
    ("version", "0.9.0");

CREATE TABLE IF NOT EXISTS feeds(
    id INTEGER PRIMARY KEY,
    source TEXT UNIQUE,
    title TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS feed_tags(
    feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
    tag TEXT
) STRICT;

CREATE INDEX IF NOT EXISTS idx_feed_tags__feed_id__tag ON feed_tags(feed_id, tag);

CREATE INDEX IF NOT EXISTS idx_feed_tags__tag__feed_id ON feed_tags(tag, feed_id);

CREATE TABLE IF NOT EXISTS entries(
    id INTEGER PRIMARY KEY,
    feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
    title TEXT,
    link TEXT,
    epoch_published INTEGER,
    epoch_updated INTEGER,
    epoch_stored INTEGER
) STRICT;

CREATE INDEX IF NOT EXISTS idx_entries__epoch_stored ON entries(epoch_stored);

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
