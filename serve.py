#!/usr/bin/env python3
import gevent.monkey

gevent.monkey.patch_all()
import bottle
import gevent.lock

import argparse
import pathlib
import schedule
import threading
import time
import typing

import tagrss

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default=8000, type=int)
parser.add_argument("--storage-path", required=True)
parser.add_argument("--update-seconds", default=3600, type=int)
args = parser.parse_args()

storage_path: pathlib.Path = pathlib.Path(args.storage_path)

core_lock = gevent.lock.RLock()
core = tagrss.TagRss(storage_path=storage_path)


def parse_space_separated_tags(inp: str) -> list[str]:
    tags = set()
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


@bottle.route("/")
def index():
    with core_lock:
        entries = core.get_entries(limit=100)
        return bottle.template("index", entries=entries, core=core)


@bottle.get("/add_feed")
def add_feed_view():
    return bottle.template("add_feed")


@bottle.post("/add_feed")
def add_feed_effect():
    feed_source: str = bottle.request.forms.get("feed_source")  # type: ignore
    tags = parse_space_separated_tags(bottle.request.forms.get("tags"))  # type: ignore

    already_present: bool = False
    with core_lock:
        try:
            core.add_feed(feed_source=feed_source, tags=tags)
        except tagrss.FeedAlreadyAddedError:
            already_present = True
        # TODO: handle FeedFetchError too
    return bottle.template(
        "add_feed",
        after_add=True,
        feed_source=feed_source,
        already_present=already_present,
    )


@bottle.get("/manage_feed")
def manage_feed_view():
    try:
        feed_id_raw: str = bottle.request.query["feed"]  # type: ignore
        feed_id: int = int(feed_id_raw)
    except KeyError:
        raise bottle.HTTPError(400, "Feed ID not given.")
    feed: dict[str, typing.Any] = {}
    feed["id"] = feed_id
    with core_lock:
        feed["source"] = core.get_feed_source(feed_id)
        feed["title"] = core.get_feed_title(feed_id)
        feed["tags"] = core.get_feed_tags(feed_id)
    feed["serialised_tags"] = serialise_tags(feed["tags"])
    return bottle.template("manage_feed", feed=feed)


@bottle.post("/manage_feed")
def manage_feed_effect_update():
    feed: dict[str, typing.Any] = {}
    feed["id"] = int(bottle.request.forms["id"])  # type: ignore
    feed["source"] = bottle.request.forms["source"]  # type: ignore
    feed["title"] = bottle.request.forms["title"]  # type: ignore
    feed["tags"] = parse_space_separated_tags(bottle.request.forms["tags"])  # type: ignore
    feed["serialised_tags"] = bottle.request.forms["tags"]  # type: ignore
    with core_lock:
        core.set_feed_source(feed["id"], feed["source"])
        core.set_feed_title(feed["id"], feed["title"])
        core.set_feed_tags(feed["id"], feed["tags"])
    return bottle.template("manage_feed", feed=feed, after_update=True)


@bottle.get("/delete_feed")
def delete_feed_view():
    return bottle.static_file("delete_feed.html", root="views")


@bottle.post("/delete_feed")
def delete_feed_effect():
    feed_id: int = int(bottle.request.forms["id"])  # type: ignore
    with core_lock:
        core.delete_feed(feed_id)
    return bottle.redirect("/delete_feed")


@bottle.get("/static/<path:path>")
def serve_static(path):
    return bottle.static_file(path, "static")


def update_feeds(run_event: threading.Event):
    def inner_update():
        with core_lock:
            core.fetch_all_new_feed_entries()
    inner_update()
    schedule.every(args.update_seconds).seconds.do(inner_update)
    try:
        while run_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        return

run_event = threading.Event()
run_event.set()
threading.Thread(target=update_feeds, args=(run_event,)).start()

bottle.run(host=args.host, port=args.port, server="gevent")
run_event.clear()
with core_lock:
    core.close()
