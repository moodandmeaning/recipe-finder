"""Collect candidate recipes from recipe-site sitemaps by category keyword, extract them, and pre-screen
the ingredients (drops anything with an obvious banned word). Run it from a scratch folder:
    python <repo>/tools/harvest_sitemaps.py cand_soup.jsonl soup 15
Categories are the KEYS below. URLs already tried are remembered in cand_<cat>.seen.
Every candidate still needs a full manual review against config/rules.md.
"""
import json, re, sys, time, urllib.request, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_recipe import extract, UA  # noqa
from check_data import BANNED, ALLOWED  # noqa
from latest_posts import normalize  # noqa

SITEMAPS = {
    "The Paleo Running Momma": ["https://www.paleorunningmomma.com/post-sitemap.xml", "https://www.paleorunningmomma.com/post-sitemap2.xml"],
    "Nom Nom Paleo": ["https://nomnompaleo.com/post-sitemap.xml", "https://nomnompaleo.com/post-sitemap2.xml"],
    "Downshiftology": ["https://downshiftology.com/recipes-sitemap.xml"],
    "The Real Food Dietitians": ["https://therealfooddietitians.com/post-sitemap.xml"],
    "Minimalist Baker": ["https://minimalistbaker.com/post-sitemap.xml", "https://minimalistbaker.com/post-sitemap2.xml"],
    "Detoxinista": ["https://detoxinista.com/post-sitemap.xml"],
    "Primal Gourmet": ["https://cookprimalgourmet.com/post-sitemap.xml"],
    "The Mediterranean Dish": ["https://www.themediterraneandish.com/post-sitemap.xml", "https://www.themediterraneandish.com/post-sitemap2.xml"],
    "Real Food with Jessica": ["https://www.realfoodwithjessica.com/post-sitemap.xml"],
}
KEYS = {
    "sweet3": r"smoothie|shake|energy-ball|energy-bite|date-ball|bliss-ball|protein-ball|stuffed-date|fruit-salad|nice-cream|popsicle|frozen-banana|chia-pudding|larabar|fruit-platter|baked-apple|poached",
    "eggs2": r"frittata|egg-muffin|egg-cups|baked-eggs|egg-bake|breakfast-casserole|omelet|scrambled|deviled|egg-salad|egg-roll-in|crustless|quiche|menemen|huevos|eggs-in",
    "dessert2": r"date|energy-ball|energy-bites|bliss|no-bake|baked-apple|apple-crisp|chia-pudding|nice-cream|sorbet|poached-pear|banana-bread|banana-muffin|fruit|stuffed-dates|coconut-macaroon|macaroon",
    "legumes2": r"lentil|chickpea|white-bean|black-bean|cannellini|dal|falafel|mujadara|split-pea|bean-stew|beans",
    "meat2": r"beef|lamb|meatball|brisket|short-rib|turkey|kofta|kebab|stuffed-cabbage|moussaka|pot-roast|stew",
    "vegetables": r"stuffed-(pepper|zucchini|eggplant|sweet-potato|squash|cabbage)|cauliflower-steak|ratatouille|roasted-(cauliflower|vegetables|eggplant|butternut|carrots)|eggplant|spaghetti-squash|zucchini-boat|vegetable-(curry|stew)|cabbage|mushroom",
    "salad": r"salad",
    "soup": r"soup|stew|chili",
    "legumes": r"lentil|chickpea|bean|dal|curry|hummus|falafel",
    "eggs": r"egg|frittata|shakshuka|omelet|quiche|hash",
    "chicken": r"chicken",
    "meat": r"beef|lamb|meatball|brisket|short-rib|turkey|steak|kofta|kebab|burger|pot-roast|ground-beef",
    "fish": r"salmon|cod|fish|tuna|halibut|trout|sea-bass|tilapia|sardine|mahi",
    "dessert": r"brownie|cookie|cake|pudding|truffle|bar|crumble|crisp|muffin|bites|tart|pie|fudge|mousse|ice-cream|nice-cream",
}
SKIP = r"roundup|best-|ideas|recipes$|-recipes|guide|how-to|what-to|meal-plan|gift|review|favorite|cookbook|\d+-"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def main():
    out, cat, limit = sys.argv[1], sys.argv[2], int(sys.argv[3])
    known = set()
    d = json.loads((Path(__file__).resolve().parent.parent / "data" / "recipes.json").read_text(encoding="utf-8"))
    known = {normalize(r["url"]) for r in d["recipes"]}
    seen_file = Path(out).with_suffix(".seen")
    seen = set(seen_file.read_text().split()) if seen_file.exists() else set()
    cands = []
    for site, maps in SITEMAPS.items():
        for m in maps:
            try:
                urls = re.findall(r"<loc>([^<]+)</loc>", get(m))
            except Exception as e:
                print("sitemap fail", m, e, file=sys.stderr); continue
            for u in urls:
                slug = u.rstrip("/").rsplit("/", 1)[-1]
                if re.search(KEYS[cat], slug) and not re.search(SKIP, slug) and normalize(u) not in known and u not in seen:
                    cands.append(u)
    random.seed(cat)
    random.shuffle(cands)
    n = 0
    with open(out, "a", encoding="utf-8") as f:
        for u in cands:
            if n >= limit:
                break
            seen.add(u)
            try:
                r = extract(u)
            except Exception as e:
                continue
            time.sleep(0.5)
            if "error" in r or not r["ingredients"] or not r["steps"] or not r.get("image"):
                continue
            flags = sorted({m.group(0).lower() for i in r["ingredients"] for m in [BANNED.search(ALLOWED.sub(" ", i))] if m})
            if flags:
                continue
            r["cat"] = cat
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    seen_file.write_text("\n".join(seen))
    print(cat, "clean candidates:", n, "of", len(cands), "urls")


if __name__ == "__main__":
    main()
