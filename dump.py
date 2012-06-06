#!/usr/bin/env python

import os
import time
import re
import urllib.request
import json
import argparse

user_url = "http://api-fotki.yandex.ru/api/users/{}/albums/?format=json"
album_url = "http://api-fotki.yandex.ru/api/users/{}/album/{}/photos/?format=json"

CREATED = 1
PUBLISHED = 2

def grab(user_id, album_id, dest, use_title, use_date, next = None):
    url = (next is not None) and next or album_url.format(user_id, album_id)
    album = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
    if not "entries" in album:
        return
    album_dir = os.path.join(dest, album["title"])
    if not os.path.isdir(album_dir):
        os.makedirs(album_dir)
    if next is None:
        print('Downloading album "{}" (id: {})...'.format(album["title"], album_id))
    for image in album["entries"]:
        if use_date == CREATED and "created" in image:
            t = time.mktime(time.strptime(image["created"], "%Y-%m-%dT%H:%M:%SZ"))
        elif use_date == PUBLISHED:
            t = time.mktime(time.strptime(image["published"], "%Y-%m-%dT%H:%M:%SZ"))
        else:
            t = time.time()
        if use_title and image["title"].lower() not in ["", ".jpg"]:
            filename = os.path.join(album_dir, image["title"])
            if not image["title"].lower().endswith(".jpg"):
                filename += ".jpg"
            if os.path.exists(filename):
                print('"{}" already exists. Skipped.'.format(filename))
                continue
            try:
                f = open(filename, mode="wb")
                f.write(urllib.request.urlopen(image["img"]["orig"]["href"]).read())
                f.close()
                os.utime(filename, (time.time(), t))
                continue
            except IOError:
                pass
        filename = os.path.join(album_dir, re.search("\d+$", image["id"]).group() + ".jpg")
        if os.path.exists(filename):
            print('"{}" already exists. Skipped.'.format(filename))
            continue
        try:
            f = open(filename, mode="wb")
            f.write(urllib.request.urlopen(image["img"]["orig"]["href"]).read())
            f.close()
            os.utime(filename, (time.time(), t))
        except IOError:
            print('"{}" cannot be saved. Skipped.'.format(filename))
    if "next" in album["links"]:
        grab(user_id, album_id, dest, use_title, use_date, album["links"]["next"] + "?format=json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downloads albums from Yandex.Fotki. Skips files that already exist.")
    parser.add_argument("user")
    parser.add_argument("-a", "--albums", nargs="*", metavar="ID", help="list of album ids to proceed (download all if empty, prompt for every album if the argument is omitted)")
    parser.add_argument("-d", "--dest", default="", metavar="DIR", help="output directory")
    parser.add_argument("-t", "--use-title", action="store_true", help="use title as file name (if possible)")
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument("-c", "--use-cdate", dest="use_date", action="store_const", const=CREATED, help="use creation date as modification date (if available)")
    date_group.add_argument("-p", "--use-pdate", dest="use_date", action="store_const", const=PUBLISHED, help="use publishing date as modification date")
    args = parser.parse_args()

    url = user_url.format(args.user)
    user = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
    if "entries" in user:
        for album in user["entries"]:
            if album["imageCount"] == 0:
                continue
            album_id = re.search("\d+$", album["id"]).group()
            if (args.albums is None and input('Download album "{}" (id: {})? '.format(album["title"], album_id)) in ["y", "Y"]) or (args.albums is not None and (args.albums == [] or album_id in args.albums)):
                grab(args.user, album_id, args.dest, args.use_title, args.use_date)