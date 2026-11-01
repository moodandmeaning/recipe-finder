"""Merge a batch spec (hand-written Hebrew and English text for each candidate) with the extracted candidate
data in cand_*.jsonl (current folder) into recipes ready for tools/add_recipes.py:
    python <repo>/tools/build_batch.py spec.json new.json
Spec item: key ("soup#3" = line 3 of cand_soup.jsonl), id, cat, shabbat, optional times/servings/nut/added/
en_ing/drop, en{title, description, steps, whyFits}, he{title, description, ingredients, steps, whyFits}.
"""
import glob, html, json, re, sys
from datetime import date
from urllib.parse import quote

TODAY = date.today().isoformat()  # the user's computer is on Israel time

SOURCE_NAMES = {"Nom Nom Paleo®": "Nom Nom Paleo", "PrimalGourmet": "Primal Gourmet",
                "kikar.co.il": "כיכר השבת · אוכל", "10dakot.co.il": "10 דקות"}
data = {}
for f in glob.glob("cand_*.jsonl"):
    c = f[5:-6]
    for i, l in enumerate(open(f, encoding="utf-8")):
        data[f"{c}#{i}"] = json.loads(l)


def clean(s):
    s = s.replace("((", "(").replace("))", ")").replace(" (, ", " (").replace("(, ", "(").replace(" ,", ",")
    s = re.sub(r"\s*,\s*\(", " (", s)
    s = re.sub(r"\(\s*\)", "", s)
    return re.sub(r"\s+", " ", s).strip()


spec = json.load(open(sys.argv[1], encoding="utf-8"))
out = []
for s in spec:
    r = data[s["key"]]
    ing = s.get("en_ing") or [clean(x) for i, x in enumerate(r["ingredients"]) if i not in s.get("drop", [])]
    t = s.get("times", {})
    rec = {
        "id": s["id"],
        "url": r["url"].split("?")[0] if "kikar" not in r["url"] else r["url"],
        "source": html.unescape(SOURCE_NAMES.get(r["site"], r["site"])),
        "sourceLang": "he" if re.search(r"kikar|10dakot|\.co\.il", r["url"]) else "en",
        "image": quote(re.sub(r"https://i\d\.wp\.com/(www\.)?", "https://", r["image"]).split("?")[0] if "wp.com" in r["image"] else r["image"], safe=":/?&=%#+,;@!~*'()"),
        "added": s.get("added", TODAY),
        "category": s["cat"],
        "shabbat": s.get("shabbat", False),
        "prepMinutes": t.get("prep", r["prepMinutes"]),
        "cookMinutes": t.get("cook", r["cookMinutes"]),
        "waitMinutes": t.get("wait", 0),
        "totalMinutes": t.get("total", r["totalMinutes"]),
        "servings": s.get("servings", r["servings"]),
        "nutrition": s.get("nut", {"calories": r["calories"], "protein": r["protein"]}),
        "en": dict(s["en"], ingredients=ing) if "ingredients" not in s["en"] else s["en"],
        "he": s["he"],
    }
    # Times must add up: prep + cook + wait (chilling, soaking, marinating) = total.
    pr, ck = rec["prepMinutes"] or 0, rec["cookMinutes"] or 0
    wt = rec["waitMinutes"] or max(0, (rec["totalMinutes"] or 0) - pr - ck)
    wt = wt if wt >= 10 else 0
    rec.update(prepMinutes=pr, cookMinutes=ck, waitMinutes=wt, totalMinutes=pr + ck + wt)
    if not wt:
        del rec["waitMinutes"]
    assert len(rec["he"]["ingredients"]) >= len(ing) - 1, (s["id"], len(rec["he"]["ingredients"]), len(ing))
    out.append(rec)
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "recipes built")
