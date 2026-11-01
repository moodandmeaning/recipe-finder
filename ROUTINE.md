# Daily recipe run

These are the instructions for the scheduled daily task (and for anyone running it by hand).
Goal: add about **10 new recipes** to `data/recipes.json` that pass **every** rule in `config/rules.md`, then push.

## 1. Get ready
- `git pull` to start from the latest version.
- Read `config/rules.md` carefully. It is the only judge of what gets in.
- Look at the existing recipes in `data/recipes.json`: their URLs (to skip) and their categories (to keep variety).

## 2. Find candidates (aim for 25–40)
- `python tools/latest_posts.py --days 14` lists new posts from the sites in `config/sources.json`.
- Search the open web for more. Mix English and Hebrew searches (`config/sources.json` → `hebrewSearches` has ideas), and rotate the categories so each day is varied, e.g. "whole30 beef stew", "paleo salmon recipe", "dairy-free grain-free chicken soup", "מתכון סלט קינואה" ✗ (no grains!), "מתכון סלט עדשים", "מתכון עוף בתנור עם ירקות".
- Prefer recipe pages from real recipe sites and creators (including the websites of Instagram recipe creators). Skip roundups ("25 best…"), videos with no written recipe, and paywalled pages.
- At least 2 of the day's recipes should come from Hebrew sources when possible.

## 3. Read each candidate
- `python tools/extract_recipe.py URL [URL ...]` returns the recipe's exact data (title, photo, ingredients, steps, times, servings, nutrition).
- If a site blocks it or the page has no recipe data, read the page with web fetch instead. Never guess ingredients. If you can't read the full ingredient list, skip the recipe.
- Don't try to get around sites that block automated access. Just skip them.

## 4. Check against the rules (strict)
For each candidate, go through **every ingredient** and **every step** against `config/rules.md`:
- Any dairy, grain, refined sugar (over the limit), non-kosher item, deep frying, processed food, or meat+fish together → **reject**.
- Optional garnishes that break a rule (e.g. "feta for serving"): reject the recipe. Only grain *side dishes* ("serve over rice") may be dropped, as the rules describe.
- When unsure, reject. 10 great recipes are better than 12 doubtful ones.
- Keep a short list of what you rejected and why. Put it in the commit message body.

## 5. Write the recipe in both languages
Add each passing recipe to the start of the `recipes` array in `data/recipes.json`, in exactly this shape:

```json
{
  "id": "short-english-slug",
  "url": "https://original recipe page",
  "source": "Site or creator name",
  "sourceLang": "en",
  "image": "https://direct photo URL from the recipe data",
  "added": "YYYY-MM-DD (today, Israel time)",
  "category": "salad | soup | chicken | meat | fish | vegetables | legumes | eggs | dessert",
  "shabbat": true,
  "prepMinutes": 10,
  "cookMinutes": 30,
  "totalMinutes": 40,
  "servings": 4,
  "nutrition": { "calories": 300, "protein": 25 },
  "en": {
    "title": "...", "description": "one or two sentences",
    "ingredients": ["one ingredient per line, with amounts"],
    "steps": ["one step per line"],
    "whyFits": "one or two sentences: why this passes the rules (mention anything that was dropped)"
  },
  "he": { "title": "...", "description": "...", "ingredients": ["..."], "steps": ["..."], "whyFits": "..." }
}
```
- **Rewrite the steps in your own words** (clear and concise). Don't copy the site's text. Ingredient lists can be kept as they are, with amounts.
- Hebrew must be natural, everyday Israeli kitchen Hebrew (כף, כפית, כוס, גרם, מעלות צלזיוס). English uses cups/tbsp with grams where helpful. Temperatures: °C first in English too, with °F in parentheses.
- Translate ingredient amounts accurately. Don't round in a way that changes the recipe.
- `nutrition`: use the site's values per serving. If missing, estimate and say "estimate" in `whyFits`. Use `null` for unknown times.
- `shabbat: true` when the dish keeps well and can be made ahead or kept warm.
- Use the direct image URL (not `i0/i1/i2.wp.com` proxies).
- Set the top-level `"updated"` to today's date.

## 6. Check and push
- `python tools/check_data.py` must finish with **0 errors**. Look at every warning. If one is a real rule break, remove the recipe.
- Commit with a message like `Add 10 recipes (2026-11-02)`, with the rejected list in the body, and `git push`.
- If fewer than 10 good recipes were found, push what you have. Never pad the batch with recipes that break the rules.
