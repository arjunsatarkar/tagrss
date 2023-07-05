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


class SqliteMissingForeignKeySupportError(Exception):
    pass


class TagRss:
    def __init__(self, *, storage_path: str | pathlib.Path):
        self.connection: sqlite3.Connection = sqlite3.connect(storage_path)

        with self.connection:
            with open("setup.sql", "r") as setup_script:
                self.connection.executescript(setup_script.read())
            if (1,) not in self.connection.execute("PRAGMA foreign_keys;").fetchmany(1):
                raise SqliteMissingForeignKeySupportError

    def add_feed(self, feed_source: str, tags: list[str]) -> None:
        response = requests.get(feed_source)
        if response.status_code != requests.codes.ok:
            raise FeedFetchError(feed_source, response.status_code)
        try:
            base: str = response.headers["Content-Location"]
        except KeyError:
            base: str = feed_source
        parsed = feedparser.parse(
            io.BytesIO(bytes(response.text, encoding="utf-8")),
            response_headers={"Content-Location": base},
        )
        with self.connection:
            feed_title: str = parsed.feed.get("title", "")
            try:
                self.connection.execute(
                    "INSERT INTO feeds(source, title) VALUES(?, ?);",
                    (feed_source, feed_title),
                )  # Note: ensure no more INSERTs between this and the last_insert_rowid() call
            except sqlite3.IntegrityError:
                raise FeedAlreadyAddedError
            feed_id: int = int(
                self.connection.execute("SELECT last_insert_rowid();").fetchone()[0]
            )
            self.connection.executemany(
                "INSERT INTO feed_tags(feed_id, tag) VALUES(?, ?);",
                ((feed_id, tag) for tag in tags),
            )
            self.store_feed_entries(feed_id, parsed)

    def get_entries(self, *, limit: int) -> list[dict[str, typing.Any]]:
        with self.connection:
            resp = self.connection.execute(
                "SELECT feed_id, title, link, epoch_published, epoch_updated FROM entries \
                    ORDER BY epoch_stored DESC LIMIT ?;",
                (limit,),
            ).fetchall()

        entries = []
        for entry in resp:
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

    def get_feed_source(self, feed_id: int) -> str:
        with self.connection:
            return self.connection.execute(
                "SELECT source FROM feeds WHERE id = ?;", (feed_id,)
            ).fetchone()[0]

    def get_feed_title(self, feed_id: int) -> str:
        with self.connection:
            return self.connection.execute(
                "SELECT title FROM feeds WHERE id = ?;", (feed_id,)
            ).fetchone()[0]

    def get_feed_tags(self, feed_id: int) -> list[str]:
        with self.connection:
            return [
                t[0]
                for t in self.connection.execute(
                    "SELECT tag FROM feed_tags WHERE feed_id = ?;", (feed_id,)
                ).fetchall()
            ]

    def set_feed_source(self, feed_id: int, feed_source: str):
        with self.connection:
            self.connection.execute(
                "UPDATE feeds SET source = ? WHERE id = ?;", (feed_source, feed_id)
            )

    def set_feed_title(self, feed_id: int, feed_title: str):
        with self.connection:
            self.connection.execute(
                "UPDATE feeds SET title = ? WHERE id = ?;", (feed_title, feed_id)
            )

    def set_feed_tags(self, feed_id: int, feed_tags: list[str]):
        with self.connection:
            self.connection.execute(
                "DELETE FROM feed_tags WHERE feed_id = ?;", (feed_id,)
            )
            self.connection.executemany(
                "INSERT INTO feed_tags(feed_id, tag) VALUES(?, ?);",
                ((feed_id, tag) for tag in feed_tags),
            )

    def delete_feed(self, feed_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM feeds WHERE id = ?;", (feed_id,))

    def fetch_all_new_feed_entries(self) -> None:
        with self.connection:
            resp = self.connection.execute("SELECT id, source FROM feeds;")
            while True:
                row = resp.fetchone()
                if not row:
                    break
                feed_id = row[0]
                feed_source = row[1]
                response = requests.get(feed_source)
                if response.status_code != requests.codes.ok:
                    continue  # TODO: log this somehow
                try:
                    base: str = response.headers["Content-Location"]
                except KeyError:
                    base: str = feed_source
                parsed = feedparser.parse(
                    io.BytesIO(bytes(response.text, encoding="utf-8")),
                    response_headers={"Content-Location": base},
                )
                self.store_feed_entries(feed_id, parsed)

    def store_feed_entries(self, feed_id: int, parsed_feed):
        for entry in reversed(parsed_feed.entries):
            link: str = entry.get("link", None)
            title: str = entry.get("title", None)
            try:
                epoch_published: typing.Optional[int] = calendar.timegm(
                    entry.get("published_parsed", None)
                )
            except TypeError:
                epoch_published = None
            try:
                epoch_updated: typing.Optional[int] = calendar.timegm(
                    entry.get("updated_parsed", None)
                )
            except TypeError:
                epoch_updated = None
            with self.connection:
                self.connection.execute(
                    "INSERT INTO entries(feed_id, title, link, epoch_published, epoch_updated, epoch_stored) \
                        VALUES(?, ?, ?, ?, ?, ?);",
                    (
                        feed_id,
                        title,
                        link,
                        epoch_published,
                        epoch_updated,
                        int(time.time()),
                    ),
                )


    def close(self) -> None:
        with self.connection:
            self.connection.executescript(
                """
PRAGMA analysis_limit=1000;
PRAGMA optimize;
                """
            )
        self.connection.close()
