#!/usr/bin/env python3
"""
Copyright (c) 2023-present Arjun Satarkar <me@arjunsatarkar.net>.
Licensed under the GNU Affero General Public License v3.0. See LICENSE.txt in
the root of this repository for the text of the license.
"""
import bottle
import schedule

import argparse
import logging
import math
import pathlib
import threading
import time
import typing

import tagrss

MAX_PER_PAGE_ENTRIES = 1000
DEFAULT_PER_PAGE_ENTRIES = 50
MAX_TAGS = 100

logging.basicConfig(
    format='%(levelname)s:%(name)s:"%(asctime)s":%(message)s',
    datefmt="%Y-%m-%d %H:%M:%S %z",
    level=logging.INFO,
)

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default=8000, type=int)
parser.add_argument("--storage-path", required=True)
parser.add_argument("--update-seconds", default=3600, type=int)
args = parser.parse_args()

storage_path: pathlib.Path = pathlib.Path(args.storage_path)

core = tagrss.TagRss(storage_path=storage_path)


def parse_space_separated_tags(inp: str) -> list[str]:
    tags: set[str] = set()
    tag = ""
    escaped = False
    for c in inp:
        match c:
            case "\\":
                if not escaped:
                    escaped = True
                    continue
            case " ":
                if not escaped:
                    tags.add(tag)
                    tag = ""
                    continue
        escaped = False
        tag += c
    if tag:
        tags.add(tag)
    return list(sorted(tags))


def serialise_tags(tags: list[str]) -> str:
    result = ""
    for i, tag in enumerate(tags):
        if i > 0:
            result += " "
        result += (tag.replace("\\", "\\\\")).replace(" ", "\\ ")
    return result


@bottle.get("/")
def index():
    per_page: int = min(
        MAX_PER_PAGE_ENTRIES,
        int(bottle.request.query.get("per_page", DEFAULT_PER_PAGE_ENTRIES)),  # type: ignore
    )
    page_num = int(bottle.request.query.get("page_num", 1))  # type: ignore
    offset = (page_num - 1) * per_page
    included_feeds_str: typing.Optional[str] = bottle.request.query.get(  # type: ignore
        "included_feeds", None
    )
    included_feeds: typing.Optional[list[int]] = None
    if included_feeds_str:
        try:
            included_feeds = [int(feed_id) for feed_id in included_feeds_str.split(" ")]
        except ValueError:
            pass
    included_tags_str: typing.Optional[str] = bottle.request.query.get(  # type: ignore
        "included_tags", None
    )
    included_tags: typing.Optional[list[str]] = None
    if included_tags_str:
        included_tags = parse_space_separated_tags(included_tags_str)
    total_pages: int = max(
        1,
        math.ceil(
            core.get_entry_count(
                included_feeds=included_feeds, included_tags=included_tags
            )
            / per_page
        ),
    )
    entries = core.get_entries(
        limit=per_page,
        offset=offset,
        included_feeds=included_feeds,
        included_tags=included_tags,
    )
    referenced_feed_ids = list({entry.feed_id for entry in entries})
    referenced_feeds_list = core.get_feeds(
        limit=len(referenced_feed_ids),
        included_feeds=referenced_feed_ids,
        get_tags=True,
    )
    referenced_feeds = {}
    for feed in referenced_feeds_list:
        referenced_feeds[feed.id] = feed
    return bottle.template(
        "index",
        entries=entries,
        offset=offset,
        page_num=page_num,
        total_pages=total_pages,
        per_page=per_page,
        max_per_page=MAX_PER_PAGE_ENTRIES,
        included_feeds=included_feeds,
        included_tags=included_tags,
        included_feeds_str=included_feeds_str,
        included_tags_str=included_tags_str,
        referenced_feeds=referenced_feeds,
    )


@bottle.get("/list_feeds")
def list_feeds():
    per_page: int = min(
        MAX_PER_PAGE_ENTRIES,
        int(bottle.request.query.get("per_page", DEFAULT_PER_PAGE_ENTRIES)),  # type: ignore
    )
    page_num = int(bottle.request.query.get("page_num", 1))  # type: ignore
    offset = (page_num - 1) * per_page
    total_pages: int = max(1, math.ceil(core.get_feed_count() / per_page))
    feeds = core.get_feeds(limit=per_page, offset=offset, get_tags=True)
    return bottle.template(
        "list_feeds",
        feeds=feeds,
        offset=offset,
        page_num=page_num,
        total_pages=total_pages,
        per_page=per_page,
        max_per_page=MAX_PER_PAGE_ENTRIES,
    )


@bottle.get("/add_feed")
def add_feed_view():
    return bottle.template("add_feed")


@bottle.post("/add_feed")
def add_feed_effect():
    feed_source: str = bottle.request.forms.get("feed_source")  # type: ignore
    tags = parse_space_separated_tags(bottle.request.forms.get("tags"))  # type: ignore
    custom_title: str = bottle.request.forms.get("title")  # type: ignore

    if len(tags) > MAX_TAGS:
        raise bottle.HTTPError(400, f"A feed cannot have more than {MAX_TAGS} tags.")

    try:
        feed_id = core.add_feed(
            source=feed_source,
            tags=tags,
            custom_title=custom_title if custom_title else None,
        )
        logging.info(f"Added feed {feed_id} (source: {feed_source}).")
    except tagrss.FeedSourceAlreadyExistsError:
        raise bottle.HTTPError(
            400, f"Cannot add feed from {feed_source} as it was already added."
        )
    except tagrss.FeedTitleAlreadyInUseError as e:
        raise bottle.HTTPError(
            400,
            f'Cannot add feed with title "{str(e)}" as another feed already has that '
            "title.",
        )
    except tagrss.FeedFetchError as e:
        if e.bad_source:
            if getattr(e, "status_code", None):
                raise bottle.HTTPError(
                    400,
                    f'Could not fetch feed: "{feed_source}" returned HTTP status code {e.status_code}.',
                )
            else:
                raise bottle.HTTPError(
                    400,
                    f'Could not fetch feed from "{feed_source}" due to a problem with the source.',
                )
        else:
            raise bottle.HTTPError(500, f"Failed to fetch feed from {feed_source}.")
    return bottle.template(
        "add_feed",
        after_add=True,
        feed_source=feed_source,
    )


@bottle.get("/manage_feed")
def manage_feed_view():
    try:
        feed_id_raw: str = bottle.request.query["feed"]  # type: ignore
    except KeyError:
        raise bottle.HTTPError(400, "Feed ID not given.")
    try:
        feed_id: int = int(feed_id_raw)
    except ValueError:
        raise bottle.HTTPError(400, f'"{feed_id_raw}" is not a valid feed ID.')
    try:
        feed = tagrss.Feed(
            id=feed_id,
            source=core.get_feed_source(feed_id),
            title=core.get_feed_title(feed_id),
        )
    except tagrss.FeedDoesNotExistError:
        raise bottle.HTTPError(404, f"No feed has ID {feed_id}.")
    feed.tags = core.get_feed_tags(feed_id)
    serialised_tags = serialise_tags(feed.tags)
    return bottle.template("manage_feed", feed=feed, serialised_tags=serialised_tags)


@bottle.post("/manage_feed")
def manage_feed_effect():
    serialised_tags = bottle.request.forms["tags"]  # type: ignore
    feed = tagrss.Feed(
        id=int(bottle.request.forms["id"]),  # type: ignore
        source=bottle.request.forms["source"],  # type: ignore
        title=bottle.request.forms["title"],  # type: ignore
        tags=parse_space_separated_tags(serialised_tags),
    )
    assert feed.tags
    if len(feed.tags) > MAX_TAGS:
        raise bottle.HTTPError(400, f"A feed cannot have more than {MAX_TAGS} tags.")
    try:
        core.set_feed_source(feed.id, feed.source)
    except tagrss.FeedSourceAlreadyExistsError:
        raise bottle.HTTPError(
            400,
            f"Cannot change source to {feed.source} as there is already a feed with"
            " that source.",
        )
    try:
        core.set_feed_title(feed.id, feed.title)
    except tagrss.FeedTitleAlreadyInUseError:
        raise bottle.HTTPError(
            400,
            f"Cannot change title to {feed.title} as there is already a feed with"
            " that title.",
        )
    core.set_feed_tags(feed.id, feed.tags)
    logging.info(f"Edited details of feed {feed.id}.")
    return bottle.template(
        "manage_feed", feed=feed, serialised_tags=serialised_tags, after_update=True
    )


@bottle.post("/delete_feed")
def delete_feed():
    feed_id: int = int(bottle.request.forms["id"])  # type: ignore
    core.delete_feed(feed_id)
    logging.info(f"Deleted feed {feed_id}.")
    return bottle.template("delete_feed")


@bottle.get("/static/<path:path>")
def serve_static(path):
    return bottle.static_file(path, "static")


def update_feeds(run_event: threading.Event):
    def inner_update():
        logging.info("Updating all feeds...")
        limit = 100
        feed_count = core.get_feed_count()
        for i in range(math.ceil(feed_count / limit)):
            feeds = core.get_feeds(limit=limit, offset=limit * i)
            for feed in feeds:
                try:
                    core.update_feed(feed.id)
                except tagrss.FeedFetchError as e:
                    logging.error(
                        f"Failed to update feed {feed.id} with source {feed.source} "
                        f"due to the following error: {e}."
                    )
                except tagrss.StorageConstraintViolationError:
                    logging.warning(
                        f"Failed to update feed {feed.id} with source {feed.source} due"
                        "to constraint violation (feed already deleted?)."
                    )
                else:
                    logging.debug(f"Updated feed {feed.id} (source {feed.source}).")
        logging.info("Finished updating all feeds.")

    inner_update()
    schedule.every(args.update_seconds).seconds.do(inner_update)
    while run_event.is_set():
        schedule.run_pending()
        time.sleep(1)


feed_update_run_event = threading.Event()
feed_update_run_event.set()
threading.Thread(target=update_feeds, args=(feed_update_run_event,)).start()

bottle.run(host=args.host, port=args.port, server="cheroot")
logging.info("Exiting...")
feed_update_run_event.clear()
core.close()
