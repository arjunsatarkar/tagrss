import feedparser
import requests

import calendar
import io
import pathlib
import sqlite3
import time
import typing


class FeedAlreadyAddedError(Exception):
    pass


class FeedFetchError(Exception):
    def __init__(self, feed_source: str, status_code: int):
        super().__init__(f"Get {feed_source} returned HTTP {status_code}")


class TagRss:
    def __init__(self, *, storage_path: str | pathlib.Path):
        self.connection: sqlite3.Connection = sqlite3.connect(storage_path)
        with self.connection:
            self.connection.executescript(
                """
CREATE TABLE IF NOT EXISTS feeds(id INTEGER PRIMARY KEY, source TEXT UNIQUE, title TEXT);
CREATE INDEX IF NOT EXISTS feed_source ON feeds(source);

CREATE TABLE IF NOT EXISTS feed_tags(feed_id INTEGER, tag TEXT);
CREATE INDEX IF NOT EXISTS feed_tags_feed_id ON feed_tags(feed_id);

CREATE TABLE IF NOT EXISTS entries(id INTEGER PRIMARY KEY, feed_id INTEGER, title TEXT, link TEXT, epoch_published INTEGER, epoch_updated INTEGER, epoch_downloaded INTEGER);
CREATE INDEX IF NOT EXISTS entry_epoch_downloaded ON entries(epoch_downloaded);
            """
            )

    def add_feed(self, *, feed_source: str, tags: tuple[str]):
        response = requests.get(feed_source)
        if response.status_code != requests.codes.ok:
            raise FeedFetchError(feed_source, response.status_code)
        try:
            base: str = response.headers["Content-Location"]
        except KeyError:
            base: str = feed_source
        parsed = feedparser.parse(
            io.BytesIO(bytes(response.text, encoding="utf-8")), response_headers={"Content-Location": base}
        )
        with self.connection:
            feed_title: str = parsed.feed.get("title", "")
            try:
                self.connection.execute(
                    "INSERT INTO feeds(source, title) VALUES(?, ?);",
                    (feed_source, feed_title),
                )
            except sqlite3.IntegrityError:
                raise FeedAlreadyAddedError
            feed_id: int = int(
                self.connection.execute(
                    "SELECT id FROM feeds WHERE source = ?;", (feed_source,)
                ).fetchone()[0]
            )
            self.connection.executemany(
                f"INSERT INTO feed_tags(feed_id, tag) VALUES({feed_id}, ?);", tuple(((tag,) for tag in tags))
            )
            for entry in reversed(parsed.entries):
                link: str = entry.get("link", "")
                try:
                    epoch_published: typing.Optional[int] = calendar.timegm(
                        entry.get("published_parsed", None)
                    )
                except ValueError:
                    epoch_published = None
                try:
                    epoch_updated: typing.Optional[int] = calendar.timegm(
                        entry.get("updated_parsed", None)
                    )
                except ValueError:
                    epoch_updated = None
                self.connection.execute(
                    "INSERT INTO entries(feed_id, title, link, epoch_published, epoch_updated, epoch_downloaded) VALUES(?, ?, ?, ?, ?, ?);",
                    (
                        feed_id,
                        feed_title,
                        link,
                        epoch_published,
                        epoch_updated,
                        int(time.time()),
                    ),
                )

    def get_entries(self, *, limit: int):
        with self.connection:
            result = self.connection.execute(
                "SELECT feed_id, title, link, epoch_published, epoch_updated FROM entries ORDER BY epoch_downloaded DESC LIMIT ?;",
                (limit,),
            ).fetchall()

        entries = []
        for entry in result:
            entries.append(
                {
                    "feed_id": entry[0],
                    "title": entry[1],
                    "link": entry[2],
                    "epoch_published": entry[3],
                    "epoch_updated": entry[4],
                }
            )
        return entries
    def get_feed_tags(self, feed_id: int) -> tuple[str]:
        with self.connection:
            return tuple((t[0] for t in self.connection.execute("SELECT tag FROM feed_tags WHERE feed_id = ?;", (feed_id,)).fetchall()))