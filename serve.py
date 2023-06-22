#!/usr/bin/env python3
from gevent import monkey

monkey.patch_all()
import bottle
import feedparser
import gevent.lock

import argparse
import datetime

parser = argparse.ArgumentParser()
parser.add_argument("host", nargs="?", default="localhost")
parser.add_argument("-p", "--port", default=8000, type=int)
args = parser.parse_args()

feeds_lock = gevent.lock.RLock()
feeds = {}

feed_items_lock = gevent.lock.RLock()
feed_items = []

def store_feed(feed_url: str):
    ...


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
    already_present: bool = False
    with feeds_lock:
        if feed_source not in feeds:
            feeds[feed_source] = {}
        else:
            already_present = True
        print(feeds)
    feed = feedparser.parse(feed_source)
    with feed_items_lock:
        for entry in reversed(feed.entries):
            try:
                date_published = datetime.datetime(*(entry.published_parsed[0:6])).strftime("%x %X")
            except AttributeError:
                date_published = None
            try:
                date_updated = datetime.datetime(*(entry.updated_parsed[0:6])).strftime("%x %X")
            except AttributeError:
                date_updated = None
            if date_updated == date_published:
                date_updated = None
            feed_items.append({
                "title": entry["title"],
                "link": entry["link"],
                "date_published": date_published,
                "date_updated": date_updated,
            })
    return bottle.template("add_feed", after_add=True, feed_source=feed_source, already_present=already_present)


@bottle.get("/modify_feed")
def modify_feed_ui():
    ...


bottle.run(host=args.host, port=args.port, server="gevent")
