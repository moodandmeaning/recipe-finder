"""Lists recent posts from the feeds in config/sources.json that are not in data/recipes.json yet.

Usage: python tools/latest_posts.py [--days 14]
Prints one JSON line per post: {"source", "title", "url", "date"}.
"""
import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
UA = "RecipeFinderBot/1.0 (personal recipe app; +https://github.com/moodandmeaning/recipe-finder)"


def normalize(url):
    """Same recipe → same key: no query string, no fragment, no trailing slash, no www."""
    p = urlsplit(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    return urlunsplit(("https", host, p.path.rstrip("/"), "", ""))


def known_urls():
    path = ROOT / "data" / "recipes.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {normalize(r["url"]) for r in data.get("recipes", []) if r.get("url")}


def read_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as res:
        root = ET.fromstring(res.read())
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        try:
            date = parsedate_to_datetime(item.findtext("pubDate") or "")
        except (TypeError, ValueError):
            date = None
        yield title, link, date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    sources = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
    seen = known_urls()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    for s in sources.get("feeds", []):
        try:
            for title, link, date in read_feed(s["feed"]):
                if not link or normalize(link) in seen:
                    continue
                if date and date < cutoff:
                    continue
                print(json.dumps({"source": s["name"], "title": title, "url": link.split("?utm_")[0],
                                  "date": date.date().isoformat() if date else None}, ensure_ascii=False))
        except Exception as e:  # one broken feed shouldn't stop the rest
            print(json.dumps({"source": s["name"], "error": f"{type(e).__name__}: {e}"}), file=sys.stderr)


if __name__ == "__main__":
    main()
