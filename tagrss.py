"""
Copyright (c) 2023-present Arjun Satarkar <me@arjunsatarkar.net>.
Licensed under the GNU Affero General Public License v3.0. See LICENSE.txt in
the root of this repository for the text of the license.
"""
import feedparser
import requests

import abc
import calendar
import contextlib
import dataclasses
import io
import pathlib
import sqlite3
import threading
import time
import typing


class StorageError(Exception):
    pass


class FeedSourceAlreadyExistsError(StorageError):
    pass


class FeedTitleAlreadyInUseError(StorageError):
    pass


class StorageConstraintViolationError(StorageError):
    def __init__(self, error):
        super().__init__(error)


class SqliteMissingForeignKeySupportError(StorageError):
    pass


class NetworkError(Exception):
    pass


class FeedFetchError(NetworkError):
    def __init__(self, feed_source: str, status_code: int):
        super().__init__(f"Get {feed_source} returned HTTP {status_code}")


FeedId = int
Epoch = int
ParsedFeed = feedparser.FeedParserDict


@dataclasses.dataclass(kw_only=True)
class PartialFeed:
    id: typing.Optional[FeedId] = None
    source: typing.Optional[str] = None
    title: typing.Optional[str] = None
    tags: typing.Optional[list[str]] = None


@dataclasses.dataclass(kw_only=True)
class Entry:
    id: int
    feed_id: FeedId
    title: str
    link: str
    epoch_published: Epoch
    epoch_updated: Epoch


class StorageProvider(abc.ABC):
    pass


class SqliteStorageProvider(StorageProvider):
    def __init__(self, storage_path: str | pathlib.Path):
        self.__raw_connection = sqlite3.connect(storage_path, check_same_thread=False)
        self.__raw_connection.isolation_level = None

        self.__lock = threading.Lock()

        with self.__get_connection() as conn:
            with open("setup.sql", "r") as setup_script:
                conn.executescript(setup_script.read())
            if (1,) not in conn.execute("PRAGMA foreign_keys;").fetchmany(1):
                raise SqliteMissingForeignKeySupportError

    @contextlib.contextmanager
    def __get_connection(self, *, use_transaction: bool = True):
        self.__lock.acquire()
        try:
            if use_transaction:
                self.__raw_connection.execute("BEGIN;")
            yield self.__raw_connection
        except Exception as e:
            if use_transaction:
                self.__raw_connection.rollback()
            raise e
        else:
            if use_transaction:
                self.__raw_connection.commit()
        finally:
            self.__lock.release()

    def store_feed(
        self,
        *,
        source: str,
        title: str,
        tags: list[str],
    ) -> FeedId:
        with self.__get_connection() as conn:
            try:
                resp = conn.execute(
                    "INSERT INTO feeds(source, title) VALUES(?, ?);", (source, title)
                )
            except sqlite3.IntegrityError:
                resp = conn.execute(
                    "SELECT COUNT(*) FROM feeds WHERE source = ? UNION ALL SELECT "
                    "COUNT(*) FROM feeds WHERE title = ?;",
                    (source, title),
                ).fetchall()
                if resp[0][0]:
                    raise FeedSourceAlreadyExistsError
                elif resp[1][0]:
                    raise FeedTitleAlreadyInUseError(title)
                else:
                    assert False, (
                        "This should be impossible: unknown error when trying to "
                        f'store feed with title "{title}" and source "{source}".'
                    )
            else:
                feed_id: FeedId = conn.execute(
                    "SELECT last_insert_rowid();"
                ).fetchone()[0]
            conn.executemany(
                "INSERT INTO feed_tags(feed_id, tag) VALUES(?, ?);",
                ((feed_id, tag) for tag in tags),
            )
        return feed_id

    def get_feeds(
        self,
        *,
        limit: int,
        offset: int = 0,
        included_feeds: typing.Optional[list[FeedId]] = None,
        included_tags: typing.Optional[list[str]] = None,
        get_tags: bool = False,
    ) -> list[PartialFeed]:
        where_clause = "WHERE 1"
        if included_feeds:
            where_clause += f" AND id IN ({','.join('?' * len(included_feeds))})"
        if included_tags:
            where_clause += " AND id IN (SELECT id FROM feed_tags WHERE tag = ?)" * len(
                included_tags
            )
        with self.__get_connection() as conn:
            resp = conn.execute(
                f"SELECT id, source, title FROM feeds \
                {where_clause} \
                ORDER BY id ASC LIMIT ? OFFSET ?;",
                (
                    *(included_feeds if included_feeds else ()),
                    *(included_tags if included_tags else ()),
                    limit,
                    offset,
                ),
            ).fetchall()
        feeds_dict: dict[FeedId, PartialFeed] = {}
        for row in resp:
            feeds_dict[row[0]] = PartialFeed(source=row[1], title=row[2])
        if get_tags:
            feed_ids = feeds_dict.keys()
            placeholder_str = ",".join("?" * len(feed_ids))
            with self.__get_connection() as conn:
                resp = conn.execute(
                    "SELECT feed_id, tag FROM feed_tags WHERE feed_id in "
                    f"({placeholder_str});",
                    (*feed_ids,),
                ).fetchall()
            for row in resp:
                try:
                    feeds_dict[row[0]].tags.append(row[1])  # type: ignore
                except AttributeError:
                    feeds_dict[row[0]].tags = [row[1]]
        result: list[PartialFeed] = []
        for item in feeds_dict.items():
            feed = PartialFeed(id=item[0], source=item[1].source, title=item[1].title)
            if get_tags:
                feed.tags = item[1].tags
                if not feed.tags:
                    feed.tags = []
            result.append(feed)
        return result

    def get_feed_count(
        self,
        *,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> int:
        if not (included_feeds or included_tags):
            with self.__get_connection(use_transaction=False) as conn:
                return conn.execute("SELECT count from feed_count;").fetchone()[0]
        else:
            where_clause: str = "WHERE 1"
            if included_feeds:
                where_clause += f" AND id IN ({','.join('?' * len(included_feeds))})"
            if included_tags:
                where_clause += (
                    " AND id IN (SELECT id FROM feed_tags WHERE tag = ?)"
                    * len(included_tags)
                )
            with self.__get_connection(use_transaction=False) as conn:
                return conn.execute(
                    f"SELECT COUNT(*) FROM feeds {where_clause}",
                    (
                        *(included_feeds if included_feeds else ()),
                        *(included_tags if included_tags else ()),
                    ),
                ).fetchone()[0]

    def get_feed_source(self, feed_id: FeedId) -> str:
        with self.__get_connection(use_transaction=False) as conn:
            return conn.execute(
                "SELECT source  FROM feeds WHERE id = ?;", (feed_id,)
            ).fetchone()[0]

    def get_feed_title(self, feed_id: FeedId) -> str:
        with self.__get_connection(use_transaction=False) as conn:
            return conn.execute(
                "SELECT title FROM feeds WHERE id = ?;", (feed_id,)
            ).fetchone()[0]

    def get_feed_tags(self, feed_id: FeedId) -> list[str]:
        with self.__get_connection(use_transaction=False) as conn:
            return [
                t[0]
                for t in conn.execute(
                    "SELECT tag FROM feed_tags WHERE feed_id = ?;", (feed_id,)
                ).fetchall()
            ]

    def set_feed_source(self, feed_id: FeedId, feed_source: str) -> None:
        with self.__get_connection() as conn:
            try:
                conn.execute(
                    "UPDATE feeds SET source = ? WHERE id = ?;", (feed_source, feed_id)
                )
            except sqlite3.IntegrityError:
                raise FeedSourceAlreadyExistsError

    def set_feed_title(self, feed_id: FeedId, feed_title: str) -> None:
        with self.__get_connection() as conn:
            try:
                conn.execute(
                    "UPDATE feeds SET title = ? WHERE id = ?;", (feed_title, feed_id)
                )
            except sqlite3.IntegrityError:
                raise FeedTitleAlreadyInUseError

    def set_feed_tags(self, feed_id: FeedId, feed_tags: list[str]) -> None:
        with self.__get_connection() as conn:
            conn.execute("DELETE FROM feed_tags WHERE feed_id = ?;", (feed_id,))
            conn.executemany(
                "INSERT INTO feed_tags(feed_id, tag) VALUES(?, ?);",
                ((feed_id, tag) for tag in feed_tags),
            )

    def delete_feed(self, feed_id: FeedId) -> None:
        with self.__get_connection() as conn:
            conn.execute("DELETE FROM feeds WHERE id = ?;", (feed_id,))

    def store_entries(
        self, *, parsed: ParsedFeed, feed_id: FeedId, epoch_downloaded: Epoch
    ) -> None:
        for entry in reversed(parsed.entries):
            link: typing.Optional[str] = entry.get("link", None)  # type: ignore
            title: typing.Optional[str] = entry.get("title", None)  # type: ignore
            try:
                epoch_published: typing.Optional[Epoch] = calendar.timegm(
                    entry.get("published_parsed", None)  # type: ignore
                )
            except TypeError:
                epoch_published = None
            try:
                epoch_updated: typing.Optional[Epoch] = calendar.timegm(
                    entry.get("updated_parsed", None)  # type: ignore
                )
            except TypeError:
                epoch_updated = None
            with self.__get_connection() as conn:
                try:
                    conn.execute(
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
                except sqlite3.IntegrityError as e:
                    # Probably feed deleted before we got here, so foreign key
                    # constraints would have been violated by the insert.
                    raise StorageConstraintViolationError(e)

    def get_entries(
        self,
        *,
        limit: int,
        offset: int = 0,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> list[Entry]:
        where_clause: str = "WHERE 1"
        if included_feeds:
            where_clause += f" AND feed_id IN ({','.join('?' * len(included_feeds))})"
        if included_tags:
            where_clause += (
                " AND feed_id IN (SELECT feed_id FROM feed_tags WHERE tag = ?)"
                * len(included_tags)
            )
        with self.__get_connection(use_transaction=False) as conn:
            resp = conn.execute(
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
                Entry(
                    id=entry[0],
                    feed_id=entry[1],
                    title=entry[2],
                    link=entry[3],
                    epoch_published=entry[4],
                    epoch_updated=entry[5],
                )
            )
        return entries

    def get_entry_count(
        self,
        *,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> int:
        if not (included_feeds or included_tags):
            with self.__get_connection(use_transaction=False) as conn:
                return conn.execute("SELECT count from entry_count;").fetchone()[0]
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
            with self.__get_connection(use_transaction=False) as conn:
                return conn.execute(
                    f"SELECT COUNT(*) FROM entries {where_clause};",
                    (
                        *(included_feeds if included_feeds else ()),
                        *(included_tags if included_tags else ()),
                    ),
                ).fetchone()[0]

    def close(self):
        with self.__get_connection(use_transaction=False) as conn:
            conn.close()


class TagRss:
    def __init__(self, *, storage_path: str | pathlib.Path):
        self.__storage = SqliteStorageProvider(storage_path)

    def __fetch_and_parse_feed(self, source) -> tuple[ParsedFeed, Epoch]:
        response = requests.get(source)
        epoch_downloaded: int = int(time.time())
        if response.status_code != requests.codes.ok:
            raise FeedFetchError(source, response.status_code)
        try:
            base: str = response.headers["Content-Location"]
        except KeyError:
            base: str = source
        parsed: ParsedFeed = feedparser.parse(
            io.BytesIO(bytes(response.text, encoding="utf-8")),
            response_headers={"Content-Location": base},
        )
        return (parsed, epoch_downloaded)

    def add_feed(
        self,
        source: str,
        tags: list[str],
    ) -> int:
        parsed, epoch_downloaded = self.__fetch_and_parse_feed(source)
        title: str = parsed.feed.get("title", "")  # type: ignore
        feed_id = self.__storage.store_feed(source=source, title=title, tags=tags)
        self.__storage.store_entries(
            parsed=parsed, feed_id=feed_id, epoch_downloaded=epoch_downloaded
        )
        return feed_id

    def get_feed_source(self, feed_id: FeedId) -> str:
        return self.__storage.get_feed_source(feed_id)

    def get_feed_title(self, feed_id: FeedId) -> str:
        return self.__storage.get_feed_title(feed_id)

    def get_feed_tags(self, feed_id: FeedId) -> list[str]:
        return self.__storage.get_feed_tags(feed_id)

    def set_feed_source(self, feed_id: FeedId, feed_source: str):
        self.__storage.set_feed_source(feed_id, feed_source)

    def set_feed_title(self, feed_id: FeedId, feed_title: str) -> None:
        self.__storage.set_feed_title(feed_id, feed_title)

    def set_feed_tags(self, feed_id: FeedId, feed_tags: list[str]):
        self.__storage.set_feed_tags(feed_id, feed_tags)

    def delete_feed(self, feed_id: int) -> None:
        self.__storage.delete_feed(feed_id)

    def get_feeds(
        self,
        *,
        limit: int,
        offset: int = 0,
        included_feeds: typing.Optional[list[int]] = None,
        included_tags: typing.Optional[list[str]] = None,
        get_tags: bool = False,
    ) -> list[PartialFeed]:
        return self.__storage.get_feeds(
            limit=limit,
            offset=offset,
            included_feeds=included_feeds,
            included_tags=included_tags,
            get_tags=get_tags,
        )

    def get_feed_count(
        self,
        *,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> int:
        return self.__storage.get_feed_count(
            included_feeds=included_feeds, included_tags=included_tags
        )

    def get_entries(
        self,
        *,
        limit: int,
        offset: int = 0,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> list[Entry]:
        return self.__storage.get_entries(
            limit=limit,
            offset=offset,
            included_feeds=included_feeds,
            included_tags=included_tags,
        )

    def get_entry_count(
        self,
        *,
        included_feeds: typing.Optional[typing.Collection[int]] = None,
        included_tags: typing.Optional[typing.Collection[str]] = None,
    ) -> int:
        return self.__storage.get_entry_count(
            included_feeds=included_feeds, included_tags=included_tags
        )

    def update_feed(self, feed_id: FeedId) -> None:
        source = self.get_feed_source(feed_id)
        parsed, epoch_downloaded = self.__fetch_and_parse_feed(source)
        self.store_feed_entries(parsed, feed_id, epoch_downloaded)

    def store_feed_entries(
        self, parsed: ParsedFeed, feed_id: FeedId, epoch_downloaded: int
    ):
        self.__storage.store_entries(
            parsed=parsed, feed_id=feed_id, epoch_downloaded=epoch_downloaded
        )

    def close(self) -> None:
        self.__storage.close()
