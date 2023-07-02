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

import tagrss

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default=8000, type=int)
parser.add_argument("--storage-path", required=True)
args = parser.parse_args()

storage_path: pathlib.Path = pathlib.Path(args.storage_path)

tagrss_lock = gevent.lock.RLock()
tagrss_backend = tagrss.TagRss(storage_path=storage_path)


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
    return tuple(sorted(tags))


@bottle.route("/")
def index():
    with tagrss_lock:
        entries = tagrss_backend.get_entries(limit=100)
        return bottle.template("index", entries=entries, tagrss_backend=tagrss_backend)


@bottle.get("/add_feed")
def add_feed_ui():
    return bottle.template("add_feed")


@bottle.post("/add_feed")
def add_feed_effect():
    feed_source = bottle.request.forms.get("feed_source")
    tags = parse_space_separated_tags(bottle.request.forms.get("tags"))

    already_present: bool = False
    with tagrss_lock:
        try:
            tagrss_backend.add_feed(feed_source=feed_source, tags=tags)
        except tagrss.FeedAlreadyAddedError:
            already_present = True
        # TODO: handle FeedFetchError too
    return bottle.template(
        "add_feed",
        after_add=True,
        feed_source=feed_source,
        already_present=already_present
    )


@bottle.get("/static/<path:path>")
def serve_static(path):
    return bottle.static_file(path, pathlib.Path(os.getcwd(), "static"))


bottle.run(host=args.host, port=args.port, server="gevent")
