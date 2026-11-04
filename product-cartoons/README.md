# product-cartoons

Animated cartoon versions of the Amway Thailand products, for the Reel product cards.

## Files
- `catalog.json`: the lookup table used by `thai-talking-head-edit`. For each product: code, Thai name, brand, spoken aliases, category, real photo URL, and `files.webm` / `files.png` (relative to this folder; `null` until made).
- `photos/<code>.jpg|png`: the real product photos for the 278 catalog products (58 MB), linked from `photo_local` in `catalog.json`; the source images for the AI drawings. Download again with `tools/download_photos.sh`.
- `products-raw.json`: everything scraped from amway.co.th (433 products from the sitemap: name, price, image, description, categories).
- `webm/<code>_<brand>.webm`: 1080×1080, VP9 with alpha, 3 s, first frame empty.
- `png/<code>_<brand>.png`: a transparent still of the same character.
- `samples/`: the style trials (2D filter, 3D toon mascot) shown to the user.

## Tools (`tools/`)
- `scrape_catalog.py`: scrapes by sitemap. Plain curl gets blocked after a burst of requests. The data in this folder came from the built-in browser at ~1 request every 2.5 s. Never solve the site's CAPTCHA.
- `scope-main.json`: the main-category scope (no spare parts, filters, tickets, kits or sets).
- `build_catalog.py`: rebuilds `catalog.json` (aliases come from the names plus the hand-written `EXTRA` spoken forms) and picks up any webm/png files present. Run it after adding files.
- AI illustrations (the style the user chose): `ai_generate.sh <photo> <id> ...` calls Codex (`/Applications/ChatGPT.app/.../codex`, using the user's ChatGPT login and quota) with `ai_prompt.txt`. Output goes to `ai-work/ai-<id>.png`.
- Full production run: `python3 tools/produce.py [--tier 1] [--limit N]` works through `tools/production-queue.json` in priority order. The order is tier 1 Nutrilite/BodyKey/XS (65), then tier 2 Artistry/G&H/Glister/Amway Home/Satinique (117), then tier 3 the other brands (33), then tier 4 makeup shades (63). It skips products that are done, sleeps until the ChatGPT quota resets whenever it runs out, and logs to `production.log`.
- 3D toon mascot (fallback, renders locally): `prep3d.py` → `build_batch.py batch.json` → `npx hyperframes render --format webm` in `render3d/` → `split_batch.py`.
- 2D sticker filter + animation: `cartoonize.py`, `animate.py`.

Python with numpy/opencv/PIL: `~/.venvs/cartoon/bin/python -I`.

## Running production
Started 2026-11-03 06:55 with `nohup caffeinate -i python3 tools/produce.py > production.out 2>&1 &`; the PID is in `production.pid`. It keeps running after the Claude app closes, and caffeinate keeps the Mac awake.
Progress: `tail production.log`. Stop: `kill $(cat production.pid)`. Run the same command again to resume; finished products are skipped.
