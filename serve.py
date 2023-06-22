#!/usr/bin/env python3
import gevent.monkey

gevent.monkey.patch_all()
import bottle
import feedparser
import gevent.lock

import argparse
import os
import pathlib
import time

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default=8000, type=int)
args = parser.parse_args()

feeds_lock = gevent.lock.RLock()
feeds = {}

feed_items_lock = gevent.lock.RLock()
feed_items = []


def parse_space_separated_tags(inp: str) -> list[str]:
    tags = []
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
                    tags.append(tag)
                    tag = ""
                    continue
        escaped = False
        tag += c
    if tag:
        tags.append(tag)
    return tags


@bottle.route("/")
def index():
    with feed_items_lock:
        return bottle.template("index", items=feed_items)


@bottle.get("/add_feed")
def add_feed_ui():
    return bottle.template("add_feed")


@bottle.post("/add_feed")
def add_feed_effect():
    feed_source = bottle.request.forms.get("feed_source")
    tags = parse_space_separated_tags(bottle.request.forms.get("tags"))

    already_present: bool = False
    with feeds_lock:
        if feed_source not in feeds:
            feeds[feed_source] = {"tags": tags}
        else:
            already_present = True

    feed = feedparser.parse(feed_source)
    with feed_items_lock:
        for entry in reversed(feed.entries):
            try:
                date_published = time.strftime("%x %X", entry.published_parsed)
            except AttributeError:
                date_published = None
            try:
                date_updated = time.strftime("%x %X", entry.updated_parsed)
            except AttributeError:
                date_updated = None
            if date_updated == date_published:
                date_updated = None
            feed_items.append(
                {
                    "title": entry["title"],
                    "link": entry["link"],
                    "date_published": date_published,
                    "date_updated": date_updated,
                    "feed": {
                        "tags": tags,
                    },
                }
            )

    return bottle.template(
        "add_feed",
        after_add=True,
        feed_source=feed_source,
        already_present=already_present,
    )


@bottle.get("/static/<path:path>")
def serve_static(path):
    return bottle.static_file(path, pathlib.Path(os.getcwd(), "static"))


bottle.run(host=args.host, port=args.port, server="gevent")
