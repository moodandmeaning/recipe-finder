# Recipe Finder: project notes

A mobile web app (it installs to the phone's home screen) that shows ~10 new healthy recipes every day, in Hebrew and English with a toggle. Built for the user, who isn't a developer.

- Live: https://moodandmeaning.github.io/recipe-finder/ (GitHub Pages, `main` branch, repo root, public repo)
- Static site with no build step and no dependencies: `index.html`, `css/style.css`, `js/app.js` (UI), `js/i18n.js` (all interface text + categories), `sw.js` (offline), `manifest.webmanifest`, `icons/`.
- Data: `data/recipes.json`. Each recipe has both `he` and `en` text. Format and process are in `ROUTINE.md`.
- Rules: `config/rules.md`. Sites to check: `config/sources.json`.
- Tools (Python standard library only): `tools/latest_posts.py` (new posts from feeds), `tools/extract_recipe.py` (reads schema.org Recipe data from a page), `tools/check_data.py` (must pass before pushing), `tools/make_icons.py`.

## Requirements decided with the user (keep these)
- Rules: no dairy; **no grains at all** (user confirmed); kosher only (no pork/shellfish, fish with fins and scales); no refined sugar (dates/fruit OK); no deep frying, no white flour, no processed foods. Allowed: vegetables, fruit, legumes, kosher meat, chicken, fish, eggs, nuts and seeds. No time limit. Strict "very healthy".
- ~10 new recipes per day, varied categories, from open web search plus the creator sites in sources.json. Instagram can't be read directly, so we follow creators' websites instead.
- Must cost nothing beyond the user's Claude Pro plan: no paid APIs. The daily run is a scheduled Claude cloud task that follows `ROUTINE.md`.
- Every recipe in both Hebrew and English (toggle עב/EN in the header, remembered). Steps are rewritten in our own words. Photos are linked, not copied. Each recipe links to the original.
- App: feed (newest first, "new today" badge, search, category chips, time filter, Shabbat filter), recipe page (photo, servings, times, nutrition, ingredient checklist, steps, why-it-fits, original link), favorites (♥, stored on the phone).
- Don't get around sites that block automated readers. Tools identify themselves honestly (`RecipeFinderBot`).

## Working on it
- Run locally: `python -m http.server 8000 --bind 127.0.0.1`, then open http://127.0.0.1:8000/
- After changing app files, bump the cache names in `sw.js` (`shell-vN`) so phones get the update.
- Workflow the user asked for: commit with a clear English message and **push to GitHub after every change**. Pages redeploys automatically in about a minute.
