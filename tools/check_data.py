"""Checks data/recipes.json before it is pushed. Exits with an error if anything is wrong.

Usage: python tools/check_data.py [--skip-images]
- every recipe has an id (unique), url (unique), category, added date, and both "he" and "en" with
  title, ingredients, steps and whyFits
- a quick scan of ingredients for words that break the rules (dairy, grains, sugar, pork/shellfish)
- every photo link loads (unless --skip-images)
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "RecipeFinderBot/1.0 (personal recipe app; +https://github.com/moodandmeaning/recipe-finder)"
CATEGORIES = {"salad", "soup", "chicken", "meat", "fish", "vegetables", "legumes", "eggs", "pashtida", "dessert"}

# A safety net only: the real check is reading the recipe against config/rules.md.
# Words that are fine in context (coconut milk, almond butter, cauliflower rice...) are excluded first.
ALLOWED = re.compile(
    r"coconut milk|coconut cream|almond milk|oat-free|nut butter|almond butter|cashew butter|peanut butter|"
    r"sunflower butter|seed butter|cocoa butter|cauliflower rice|riced cauliflower|almond flour|coconut flour|"
    r"tapioca flour|arrowroot flour|cassava flour|tigernut flour|chickpea flour|nutritional yeast|cream of tartar|"
    r"buckwheat-free|dairy[- ]free|sugar[- ]free|no added sugar|no sugar added|egg ?plant|"
    r"חלב קוקוס|קרם קוקוס|חלב שקדים|חמאת שקדים|חמאת בוטנים|חמאת קשיו|אורז כרובית|קמח שקדים|קמח קוקוס|קמח טפיוקה|"
    r"wheat-free|dairy-free 'sour cream'|״שמנת חמוצה״ בלי חלב|קמח חומוס|שמרי בירה|גבינתי|שעועית לבנה|פלפל חלבי|חלבונים|חלבון|soy milk|plant milk|במקום אבקת מרק|במקום כפית אבקת מרק|ללא סוכר|בלי סוכר|בלי תוספת סוכר", re.I)
BANNED = re.compile(
    r"\b(milk|cheese|butter|ghee|cream|yogurt|yoghurt|labneh|kefir|whey|parmesan|feta|ricotta|mozzarella|"
    r"wheat|flour|bread|breadcrumbs?|panko|pasta|noodles?|couscous|bulgur|rice|oats?|oatmeal|quinoa|barley|"
    r"cornmeal|polenta|corn ?starch|buckwheat|millet|freekeh|spelt|sugar|corn syrup|"
    r"pork|bacon|ham|prosciutto|shrimp|prawns?|crab|lobster|mussels?|clams?|squid|scallops?|catfish|"
    r"sausages?|salami|pastrami|margarine|ketchup|bouillon)\b|"
    r"חלב|גבינ|חמאה|שמנת|יוגורט|לבנה|קמח|לחם|פירורי לחם|פסטה|אטריות|קוסקוס|בורגול|אורז|שיבולת שועל|קינואה|"
    r"סוכר|חזיר|בייקון|שרימפס|סרטן|קלמרי|נקניק|מרגרינה|קטשופ|אבקת מרק", re.I)


def fail(errors, msg):
    errors.append(msg)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    skip_images = "--skip-images" in sys.argv
    data = json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
    errors, warnings = [], []
    ids, urls = set(), set()
    for r in data.get("recipes", []):
        rid = r.get("id", "?")
        for key in ("id", "url", "source", "sourceLang", "added", "category"):
            if not r.get(key):
                fail(errors, f"{rid}: missing {key}")
        if rid in ids:
            fail(errors, f"{rid}: duplicate id")
        if r.get("url") in urls:
            fail(errors, f"{rid}: duplicate url {r.get('url')}")
        ids.add(rid)
        urls.add(r.get("url"))
        if r.get("category") not in CATEGORIES:
            fail(errors, f"{rid}: unknown category {r.get('category')}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r.get("added", "")):
            fail(errors, f"{rid}: added must be YYYY-MM-DD")
        for lang in ("he", "en"):
            x = r.get(lang) or {}
            for key in ("title", "ingredients", "steps", "whyFits"):
                if not x.get(key):
                    fail(errors, f"{rid}: missing {lang}.{key}")
            for ing in x.get("ingredients", []):
                hit = BANNED.search(ALLOWED.sub(" ", ing))
                if hit:
                    warnings.append(f"{rid}: check {lang} ingredient '{ing}' (matched '{hit.group(0)}')")
        if not skip_images and r.get("image"):
            try:
                req = urllib.request.Request(r["image"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=20) as res:
                    if not res.headers.get("Content-Type", "").startswith("image/"):
                        fail(errors, f"{rid}: image is not an image ({res.headers.get('Content-Type')})")
            except Exception as e:
                fail(errors, f"{rid}: image doesn't load: {e}")

    for w in warnings:
        print("WARNING", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(data.get('recipes', []))} recipes, {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
