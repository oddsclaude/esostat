#!/usr/bin/env python3
"""Fetch esolang data from the esolangs.org MediaWiki API and cache to data.json."""

import json
import time
import requests

API = "https://esolangs.org/w/api.php"
CACHE = "data.json"

session = requests.Session()
session.headers["User-Agent"] = "esostat/1.0 (stats tool)"

def api(**params):
    params.setdefault("format", "json")
    r = session.get(API, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def get_category_members(category, ns=0):
    """Yield all page titles in a category."""
    cmcontinue = None
    while True:
        p = dict(action="query", list="categorymembers",
                 cmtitle=f"Category:{category}", cmnamespace=ns,
                 cmlimit=500)
        if cmcontinue:
            p["cmcontinue"] = cmcontinue
        data = api(**p)
        for m in data["query"]["categorymembers"]:
            yield m["title"]
        if "continue" not in data:
            break
        cmcontinue = data["continue"]["cmcontinue"]
        time.sleep(0.1)

def get_page_categories(titles):
    """Return {title: [cat, ...]} for up to 50 titles at a time."""
    result = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i+50]
        data = api(action="query", titles="|".join(chunk),
                   prop="categories", cllimit=500)
        for page in data["query"]["pages"].values():
            title = page["title"]
            cats = [c["title"].removeprefix("Category:") for c in page.get("categories", [])]
            result[title] = cats
        time.sleep(0.1)
    return result

def fetch():
    print("Fetching all languages from Category:Languages...")
    langs = list(get_category_members("Languages"))
    print(f"  Found {len(langs)} pages")

    print("Fetching categories for each language (batches of 50)...")
    cats = {}
    for i in range(0, len(langs), 50):
        chunk = langs[i:i+50]
        cats.update(get_page_categories(chunk))
        print(f"  {min(i+50, len(langs))}/{len(langs)}", end="\r")
    print()

    print(f"Writing {CACHE}...")
    with open(CACHE, "w") as f:
        json.dump(cats, f)
    print("Done.")

if __name__ == "__main__":
    fetch()
