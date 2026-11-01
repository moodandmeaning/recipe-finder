"""Adds new recipes to data/recipes.json, skipping any already there (same id or same URL).

Usage: python tools/add_recipes.py NEW_RECIPES.json
NEW_RECIPES.json holds a JSON array of recipes in the format from ROUTINE.md.
New recipes go to the start of the list, and "updated" is set to the newest "added" date.
Safe to run after `git reset --hard origin/main`, so several runs can push without conflicts.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from latest_posts import normalize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "recipes.json"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    new = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if isinstance(new, dict):
        new = new.get("recipes", [])
    data = json.loads(DATA.read_text(encoding="utf-8"))
    ids = {r["id"] for r in data["recipes"]}
    urls = {normalize(r["url"]) for r in data["recipes"]}
    added = []
    for r in new:
        if r["id"] in ids or normalize(r["url"]) in urls:
            print("skip (already in the app):", r["id"])
            continue
        ids.add(r["id"])
        urls.add(normalize(r["url"]))
        added.append(r)
    data["recipes"] = added + data["recipes"]
    dates = [r.get("added", "") for r in data["recipes"]] + [data.get("updated", "")]
    data["updated"] = max(d for d in dates if d)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added {len(added)}, total {len(data['recipes'])}")


if __name__ == "__main__":
    main()
