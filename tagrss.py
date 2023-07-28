"""
Copyright (c) 2023-present Arjun Satarkar <me@arjunsatarkar.net>.
Licensed under the GNU Affero General Public License v3.0. See LICENSE.txt in
the root of this repository for the text of the license.
"""
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


class Sqlite3NotSerializedModeError(Exception):
    pass


def fetch_parsed_feed(feed_source: str) -> tuple[feedparser.FeedParserDict, int]:
    response = requests.get(feed_source)
    epoch_downloaded: int = int(time.time())
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
    return (parsed, epoch_downloaded)


class TagRss:
    def __init__(self, *, storage_path: str | pathlib.Path):
        if sqlite3.threadsafety != 3:
            raise Sqlite3NotSerializedModeError

        self.connection: sqlite3.Connection = sqlite3.connect(
            storage_path, check_same_thread=False
        )

        with self.connection:
            with open("setup.sql", "r") as setup_script:
                self.connection.executescript(setup_script.read())
            if (1,) not in self.connection.execute("PRAGMA foreign_keys;").fetchmany(1):
                raise SqliteMissingForeignKeySupportError

    def add_feed(
        self,
        *,
        feed_source: str,
        parsed_feed: feedparser.FeedParserDict,
        epoch_downloaded: int,
        tags: list[str],
    ) -> None:
        with self.connection:
            feed_title: str = parsed_feed.feed.get("title", "")  # type: ignore
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
            self.store_feed_entries(feed_id, parsed_feed, epoch_downloaded)

    def get_entries(
        self,
        *,
        limit: int,
        offset: int = 0,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> list[dict[str, typing.Any]]:
        where_clause: str = ""
        if included_feeds or included_tags:
            where_clause = "WHERE 1"
        if included_feeds:
            where_clause += f" AND feed_id IN ({','.join('?' * len(included_feeds))})"
        if included_tags:
            where_clause += (
                " AND feed_id IN (SELECT feed_id FROM feed_tags WHERE tag = ?)"
                * len(included_tags)
            )
        with self.connection:
            resp = self.connection.execute(
                f"SELECT id, feed_id, title, link, epoch_published, epoch_updated FROM entries \
                    {where_clause} \
                    ORDER BY id DESC LIMIT ? OFFSET ?;",
                (
                    *(included_feeds if included_feeds else ()),
                    *(included_tags if included_tags else ()),
                    limit,
                    offset,
                ),
            ).fetchall()

        entries = []
        for entry in resp:
            entries.append(
                {
                    "id": entry[0],
                    "feed_id": entry[1],
                    "title": entry[2],
                    "link": entry[3],
                    "epoch_published": entry[4],
                    "epoch_updated": entry[5],
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

    def get_feeds(self, *, limit: int, offset: int = 0) -> list[dict[str, typing.Any]]:
        with self.connection:
            resp = self.connection.execute(
                "SELECT id, source, title FROM feeds \
                ORDER BY id ASC LIMIT ? OFFSET ?;",
                (limit, offset),
            ).fetchall()
        feeds = []
        for row in resp:
            feeds.append(
                {
                    "id": row[0],
                    "source": row[1],
                    "title": row[2],
                }
            )
        return feeds

    def get_entry_count(
        self,
        *,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> int:
        if not (included_feeds or included_tags):
            with self.connection:
                return self.connection.execute(
                    "SELECT count from entry_count;"
                ).fetchone()[0]
        else:
            where_clause: str = "WHERE 1"
            if included_feeds:
                where_clause += (
                    f" AND feed_id IN ({','.join('?' * len(included_feeds))})"
                )
            if included_tags:
                where_clause += (
                    " AND feed_id IN (SELECT feed_id FROM feed_tags WHERE tag = ?)"
                    * len(included_tags)
                )
            with self.connection:
                return self.connection.execute(
                    f"SELECT COUNT(*) FROM entries {where_clause};",
                    (
                        *(included_feeds if included_feeds else ()),
                        *(included_tags if included_tags else ()),
                    ),
                ).fetchone()[0]

    def get_feed_count(self) -> int:
        with self.connection:
            return self.connection.execute("SELECT count from feed_count;").fetchone()[
                0
            ]

    def store_feed_entries(self, feed_id: int, parsed_feed, epoch_downloaded: int):
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
                    "INSERT INTO entries(feed_id, title, link, epoch_published, epoch_updated, epoch_downloaded) \
                        VALUES(?, ?, ?, ?, ?, ?);",
                    (
                        feed_id,
                        title,
                        link,
                        epoch_published,
                        epoch_updated,
                        epoch_downloaded,
                    ),
                )

    def close(self) -> None:
        self.connection.close()
