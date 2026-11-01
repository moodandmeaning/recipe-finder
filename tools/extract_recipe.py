"""Reads the schema.org Recipe data that most recipe sites embed in their pages.

Usage: python tools/extract_recipe.py URL [URL ...]
Prints one JSON object per URL: title, image, ingredients, steps, times (minutes), servings,
nutrition, site name. If a page has no Recipe data, prints {"url": ..., "error": ...}.
Pages are only parsed as JSON/HTML text; nothing from them is executed.
"""
import html
import json
import re
import sys
import urllib.request
from urllib.parse import urlparse

UA = "RecipeFinderBot/1.0 (personal recipe app; +https://github.com/moodandmeaning/recipe-finder)"
LD_RE = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "he,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode(res.headers.get_content_charset() or "utf-8", errors="replace")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", str(s)))).strip()


def walk(node):
    """Yields every dict inside a JSON-LD structure (handles @graph and nested lists)."""
    if isinstance(node, list):
        for item in node:
            yield from walk(item)
    elif isinstance(node, dict):
        yield node
        for key in ("@graph", "mainEntity", "itemListElement"):
            if key in node:
                yield from walk(node[key])


def is_recipe(d):
    t = d.get("@type")
    return t == "Recipe" or (isinstance(t, list) and "Recipe" in t)


def minutes(iso):
    """ISO-8601 duration (PT1H30M, P0DT45M) to minutes."""
    if not iso or not isinstance(iso, str):
        return None
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?", iso.strip().upper())
    if not m:
        return None
    d, h, mi = (int(x) if x else 0 for x in m.groups())
    total = d * 1440 + h * 60 + mi
    return total or None


def image(img):
    if isinstance(img, list):
        img = img[0] if img else None
    if isinstance(img, dict):
        img = img.get("url") or img.get("contentUrl")
    return img if isinstance(img, str) and img.startswith("http") else None


def steps(instr):
    out = []
    if isinstance(instr, str):
        return [s for s in (clean(x) for x in re.split(r"\n+|(?<=\.)\s+(?=\d+\.)", instr)) if s]
    for item in instr or []:
        if isinstance(item, str):
            out.append(clean(item))
        elif isinstance(item, dict):
            if item.get("@type") == "HowToSection":
                out.extend(steps(item.get("itemListElement")))
            else:
                out.append(clean(item.get("text") or item.get("name") or ""))
    return [s for s in out if s]


def servings(y):
    if isinstance(y, list):
        y = y[0] if y else None
    m = re.search(r"\d+", str(y or ""))
    return int(m.group()) if m else None


def number(s):
    m = re.search(r"\d+(?:\.\d+)?", str(s or ""))
    return round(float(m.group())) if m else None


def extract(url):
    page = fetch(url)
    for block in LD_RE.findall(page):
        try:
            data = json.loads(html.unescape(block.strip()) if block.strip().startswith("&") else block.strip())
        except json.JSONDecodeError:
            continue
        for d in walk(data):
            if not is_recipe(d):
                continue
            n = d.get("nutrition") or {}
            site = None
            for s in walk(data):
                if s.get("@type") in ("WebSite", "Organization") and s.get("name"):
                    site = s["name"]
                    break
            author = d.get("author")
            if isinstance(author, list):
                author = author[0] if author else None
            return {
                "url": url,
                "site": site or urlparse(url).hostname.removeprefix("www."),
                "author": (clean(author.get("name") or "") if isinstance(author, dict) else clean(author or "")) or None,
                "title": clean(d.get("name", "")),
                "description": clean(d.get("description", "")),
                "image": image(d.get("image")),
                "ingredients": [clean(x) for x in d.get("recipeIngredient") or [] if clean(x)],
                "steps": steps(d.get("recipeInstructions")),
                "prepMinutes": minutes(d.get("prepTime")),
                "cookMinutes": minutes(d.get("cookTime")),
                "totalMinutes": minutes(d.get("totalTime")),
                "servings": servings(d.get("recipeYield")),
                "calories": number(n.get("calories")),
                "protein": number(n.get("proteinContent")),
                "category": d.get("recipeCategory"),
                "language": d.get("inLanguage"),
            }
    return {"url": url, "error": "no schema.org Recipe data on this page"}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for u in sys.argv[1:]:
        try:
            result = extract(u)
        except Exception as e:  # network errors, blocked sites
            result = {"url": u, "error": f"{type(e).__name__}: {e}"}
        print(json.dumps(result, ensure_ascii=False))
