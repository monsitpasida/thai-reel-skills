---
name: thai-talking-head-edit
description: End-to-end edit of a Thai talking-head clip into a 9:16 Reel/TikTok/Short in the user's approved house style - split-screen contextual inserts (Pexels B-roll, HyperFrames 2D + 3D explainers, real Amway product cards on the top 58%, speaker below), word-by-word yellow highlight captions, every ค่ะ/นะคะ cut, under 60 s, no music, -14 LUFS - plus a cover image for every finished video. Use when the user drops a Thai talking-head video and says "เริ่มทำงาน" or asks for a Reel in the usual style; it orders the reel-* skills, reuses the bundled scripts and assembles in the Remotion project split-broll/.
---

# Thai Talking-Head Edit

One pipeline for the user's Thai talking-head Reels (health / product clips, e.g. Amway BodyKey, Nutrilite, sleep & weight). It sequences the single-step skills and carries the decisions the user already approved, so a new clip starts from the finished look instead of from defaults.

**Talk to the user in Thai only** — every question, option, progress note and report. File names, commands and code may stay in English.

## Approved defaults (do not change unless the user asks)

Current default = **split-screen v2** (approved 2026-11-02 on the bone reel and the sleep reel `reel-84101381`). The older full-screen v11 look is kept at the end of this file for when the user asks for it.

| Area | Default |
|---|---|
| Length | **≤ 60 s** final (user rule) |
| Speech | every **ค่ะ / คะ / นะคะ removed** from audio and captions (`cut_ka.py`); male speaker → **ครับ / นะครับ** the same way; fillers, false starts, dead air > 0.6 s cut (also inside a kept segment — split it) |
| Canvas | 1080x1920, 30 fps, H.264 CRF 17 + AAC 192k 48 kHz, faststart |
| Layout | speaker full screen normally; on an insert the speaker slides down to the bottom 42 % and the visual reveals from the top 58 %; 250-400 ms in / 250-350 ms out, ease-out or damped spring, no bounce; soft 96 px feather + blur seam, never a hard divider; 1.5-4 s per insert (≤ ~5 s when it has an internal cut) |
| Inserts | only where they explain / visualize / prove / give context / demonstrate / reset attention — never every sentence; 6-9 per minute with ≥ ~1 s of face between them; a list of things in one sentence = one insert with `cuts` |
| Visuals | real video or photos from **Pexels** that match the words, plus **HyperFrames explainers: 2-3 2D scenes + 1 3D scene** for the abstract/process lines |
| Product cards | only when the speaker names a product. Find products with `find_products.py` (step 8b). If the product has a cartoon in the **product-cartoons catalog**, ask the user once per clip: cartoon or real photo. Otherwise use the real photo from **https://amway.co.th/** (whitespace trimmed) on a white rounded card. Either way it goes in a top corner of the split, on the spoken name, with the pop SFX |
| Captions | Sukhumvit Set Bold 74 px, 3-7 words; word-by-word highlight = dark text on a thick yellow pill, others white with black outline, pill off at `spoken_end_s + 0.1`; drawn as 3 stacked layers (outline → yellow → letters) so the pill never eats a neighbour glyph; full screen at y ≈ 1650, on the seam (y ≈ topRatio·1920) while split, dipping out/in instead of sliding across the face |
| Timing | CTC forced alignment (`airesearch/wav2vec2-large-xlsr-53-th`), per-word via PyThaiNLP `newmm`, merge words < 0.15 s; never trust Whisper word timestamps for Thai |
| Sound | **no music**; voice chain below; soft whoosh only on an insert that comes ≥ 4 s after the previous one (`sfx: auto`); pop on product cards; files only from the SFX folder printed by `bash ~/.claude/skills/sound-design/scripts/install-sfx.sh` (run it first; it pulls the pack from Google Drive if missing — on this Mac `/Volumes/JamesM.2/Claude/Video/Free SFX/`) |
| Loudness | -14 LUFS integrated, ≤ -1 dBTP (two-pass `loudnorm` on the Remotion render) |

Reference projects: Remotion `/Volumes/JamesM.2/Claude/Video/split-broll/` (README = plan schema; compositions `SplitReel` = bone reel, others removed from the shared copy), edit `/Volumes/JamesM.2/Claude/Video/reel-84101381/.video-edit/`, explainers `sleep-anim/` and `bone-anim/`.

## Environment

- ffmpeg with libass/harfbuzz/libvpx: `~/.local/bin/ffmpeg` if present, otherwise `ffmpeg` on PATH
- Python venv: `~/.venvs/whisper/bin/python` (faster-whisper, torch, transformers, pythainlp); run scripts with `-I`. System `python3` has no numpy/PIL — keep it for JSON glue only.
- Models live in `HF_HOME=/Volumes/JamesM.2/Claude/tools-cache/huggingface` (≈ 4 GB, downloaded on first use). Export HF_HOME before running the venv so they are not fetched twice.
- ASR model: `mobiuslabsgmbh/faster-whisper-large-v3-turbo` (≈ 20 min for a 6.6 min retake session — run it in the background and analyse frames meanwhile).
- HyperFrames: `node ~/.claude/plugins/cache/hyperframes/hyperframes/<ver>/skills/hyperframes/scripts/plugin-cli.mjs <check --json|snapshot --at|render --format webm --output ...>`
- Remotion: `cd split-broll && npx remotion still|render <Composition> ...`; Studio is in `.claude/launch.json` (`split-broll-studio`, port 3007).
- zsh: write `${VAR}[label]`, never `$VAR[label]`; zsh does not word-split `$ids` — loop over id lists inside `bash -c`.

## Pipeline

Work in `<project>/.video-edit/`; never touch the source. Copy `scripts/` from this skill into `.video-edit/scripts/` first.

1. **video-analyze** → resolution, audio, a frame grid. Note where the face sits (fraction of frame height → `speakerFocusY`; bone reel 0.45, sleep reel 0.57). If the audio is unusable, stop and ask for clean audio — do not guess words.
2. **transcript** → `transcribe.py audio16k.wav src out.json out.txt <model>`; correct product names by hand.
3. **Takes** → for retake sessions run `ctc_peek.py audio16k.wav a-b c-d ...` on every candidate take (wav2vec2 greedy decode with word times; shows restarts Whisper hides) and pick the most complete fluent one per line.
4. **reel-hook + reel-rough-cut** → `edit-plan.json` (segments in source seconds, `text`, `reason`), then `refine_cuts.py edit-plan.json audio16k.wav`. Re-check any edge it moved onto a false start (it can snap back into a dropped word). Aim ≈ 55-58 s before particle removal.
5. Render the rough cut with the voice chain (`edl_filter.py edit-plan.json "" "<voice chain>,aresample=48000"`), extract `rough16k.wav`.
6. **captions-th** → `caption-chunks.json` (list of segments → `[text, []]` chunks) and `force_align.py caption-chunks.json rough16k.wav captions.json captions.srt` (writes `captions-chars.json` too). Edit `SPOKEN`/`SEG_FIX` first. `verify_captions.py rough16k.wav captions.json > verify.txt` (slow, background); "off" on 1-2 word chunks is usually Whisper mishearing — confirm with the CTC score before changing text.
7. **Remove ค่ะ/นะคะ** → `cut_ka.py captions-chars.json edit-plan.json edit-plan.json` (keep the v1 copies), re-render the rough cut, `ctc_peek.py` the whole thing: no stray "ค", the word before keeps its vowel (สี่ once decoded as สิ → nudge that segment end +0.03 s, not more or the ค comes back), last segment ends cleanly. Then rewrite the chunks without the particles (join a lone list number to its sentence: "สอง ยิ่งง่วง") and run `force_align.py` again.
8. **Plan the inserts** (word times from the new `captions.json`): which lines get Pexels footage, which get a 2D explainer, which one gets the 3D shot, which products are named. Keep ≥ ~1 s of face between inserts; drop or merge a visual rather than pumping the split twice in a row.
8b. **Products named** → `python3 scripts/find_products.py captions.json > products-found.json`. It reads `/Volumes/JamesM.2/Claude/Video/product-cartoons/catalog.json` (278 Amway TH products, main categories) and matches each catalog alias, including spoken forms such as บอดี้คีย์, แคลแมกดี and EAA, against the spoken words. For each hit it gives `start_s`/`end_s`, the cartoon `webm`/`png` if made, and the real `photo` URL. Check every hit by ear. A generic alias (โปรตีน, บอดี้คีย์) maps to the flagship product; when `ambiguous` lists several codes, pick by context or ask. Product card in the plan:
   - cartoon: copy the webm to `split-broll/public/cartoons/<file_base>.webm` and set `"image": "cartoons/<file_base>.webm"`. `ProductCard` plays a `.webm` as a transparent animated clip with no white card. Each clip is 3 s and its first frame is empty, so set `start` ≈ the word's `start_s` and `end` ≤ `start` + 3.
   - real photo: download `photo` into `public/products/` (trim the white edges) as before.
   - New products or a refreshed catalog: see `product-cartoons/README.md`.
9. **Explainers** (HyperFrames, section below) → `<clip>-anim/renders/explainers.webm`.
10. **Pexels B-roll** (section below) → `split-broll/public/pexels-<topic>/`.
11. **Assemble** in `split-broll/`: copy `rough-cut.mp4` → `public/<reel-id>/speaker.mp4`, the webm → `public/anim/`, `captions.json` + a new `edit-plan.json` → `src/data/<reel-id>/`, add a `<Composition id="...Reel">` to `src/Root.tsx` with `speakerFocusY`. `npx tsc --noEmit`, then `npx remotion still <Comp> --frame=N --scale=0.2` at every insert (mid + seam) and look: subject visible, explainer labels clear of the seam caption, face never covered.
12. **Render + QC** → `npx remotion render <Comp> .video-edit/final/pre-qc.mp4 --codec=h264 --crf=17` (background, ~5 min), two-pass `loudnorm I=-14:TP=-1.5` with `-c:v copy` → `final/reel-final.mp4`, ebur128 / blackdetect / silencedetect, frame strip at each insert, 720p preview (`crf 25`), `qc-report.json`. Keep the previous file as `reel-final-vN.mp4`; on approval copy to `reel-final-vN-approved.mp4`.
13. **Cover (always)** → section below.

## Split inserts (split-broll edit plan)

```json
{ "whoosh": "demo/whoosh.wav", "pop": "sfx/pop.mp3",
  "inserts": [{ "type": "contextual-split-insert", "start": 17.08, "end": 21.45,
                "visual": "pexels-sleep/dumbbell-6388424.mp4", "visualStart": 3.0,
                "layout": "top-broll-bottom-speaker", "topRatio": 0.58, "bottomRatio": 0.42,
                "seamStyle": "soft-blur-feather", "focus": { "x": 0.5, "y": 0.45 },
                "cuts": [{ "at": 18.58, "visual": "anim/sleep-explainers-2d-3d.webm", "visualStart": 3.7, "focus": { "x": 0.5, "y": 0.38 } }],
                "reason": "explain", "spokenContext": "...", "sfx": "auto" }],
  "products": [{ "start": 16.5, "end": 17.9, "image": "products/nutrilite-vitamin-d3-k2.png", "side": "right", "source": "https://amway.co.th/..." }] }
```

- Times are seconds on the rough-cut timeline; `start` = split begins entering, `end` = fully back. Start an insert ~0.05-0.1 s before its key word.
- `focus.y` aims the cover crop: the top area shows ~60 % of a 9:16 source's height. Explainers designed for it (content in y 160-1150) use 0.38; footage usually 0.3-0.6 — check a still.
- `visual` may be a still image (Ken Burns is automatic). Transitions, easing and Ken Burns vary per insert by themselves.
- After any re-cut, remap every time with the char-level map (old chars minus removed particles ↔ new chars) and re-check explainer beats; retime a scene in HyperFrames when a beat drifts ≥ ~0.15 s.

## Pexels B-roll

- Search in the built-in browser: open `https://www.pexels.com/search/videos/<query>/?orientation=portrait` with `preview_start`, then in-page `fetch()` other search pages and read `article a[href^="/video/"]` slugs (id = trailing number). curl to pexels.com returns 403. A Google sign-in popup can appear and pauses page JS — Claude cannot close it; ask the user to close it if it blocks.
- Posters for a contact sheet: `https://images.pexels.com/videos/<id>/pexels-photo-<id>.jpeg?auto=compress&w=200` (some ids 404 — skip them). Pick by looking, not by title.
- Get the real file URLs from the clip page with an in-page `fetch('/video/<slug>/')` and the regex `https://videos\.pexels\.com/video-files/[^"'\s\\]+?\.mp4` — many clips are `hd_1080_2048`, `uhd_1440_2732` or `<n>_1080_1920_25fps.mp4`, so guessing `<id>-hd_1080_1920_<fps>fps.mp4` misses them. Download the 1080-wide file with curl (the CDN allows curl; pexels.com pages do not).
- Photos: `https://images.pexels.com/photos/<id>/pexels-photo-<id>.jpeg?auto=compress&w=1600`.
- Contact-sheet each downloaded clip at 1 fps to choose `visualStart` and `focus`. Record ids/URLs in the split-broll README credits table.

## Explainer animations (HyperFrames)

- New project next to the clip (copy `sleep-anim/`: fonts, hyperframes.json, index.html pattern), 1080x1920, one sub-composition per scene, scenes back to back in one webm; the plan slices them by `visualStart`.
- **Design for the split top area**: all objects and labels inside y 160-1150 (the bottom of the canvas is never seen; the seam + captions sit just below 1150).
- 2-3 2D scenes + 1 3D scene (three.js r149 toon + inked hull, see `sleep-anim/compositions/clock3d.html`, `bone-anim/compositions/inside3d.html`, and the `3d-motion-director` skill).
- Write `SPEC.md` first: scene time = reel time − scene start, from the final (post-particle-cut) `captions.json`; each beat lands on its word. Every on-screen word must be spoken (digits for spoken numbers are fine: "7–9 ชั่วโมง").
- Look: flat Gen Z sticker — ink #1B1B3A 6-9 px outlines, 10 px hard shadow, red #FF4F6D, green #3BB273, yellow #FFD34D, pastel dotted backgrounds. Banned: dark/navy, glow, gradients, glass cards, invented numbers or terms (e.g. hormone names nobody said).
- Draw unambiguous objects: a hand-drawn flexed arm read as a thumb / something worse twice — use a dumbbell for "muscle / exercise".
- Rules: never tween a `.clip`; `fromTo` baselines; `svgOrigin` consistent between reset and `.to()`; no duplicate fromTo on one target. `check --json`, `snapshot --at` the beats and look, then `render --format webm --output renders/explainers.webm`.

## Cover (always)

- Pull 8 candidate stills from `rough-cut.mp4` (no captions), crop to face + torso, drop any with eyes closed, number them on one sheet, send it and let the user pick (they like an expressive mid-sentence face, mouth open, eyes to camera).
- Title = the hook as spoken (particles dropped), 2 lines ≤ ~20 Thai characters, one keyword on the yellow pill: `build_cover.py frame.png final/cover --title "line1|line2" --hl "keyword" --size 94 --title-y 400 [--zoom 1.1 --focus-y 0.6] [--card cards/x.png ...]`.
- Put spaces around the highlighted word in the title ("ลองไปเช็ค เวลานอน ก่อน") — the pill outline otherwise covers the neighbour glyph. Keep lines away from the screen edges (default size 118 is too big for 20-character lines).
- Title in the empty area above the head, never over the face; everything inside y 240-1680. Product card beside the torso only if a product is named. Look at it before sending.

## Known pitfalls

- Thai Whisper (turbo) hallucinates on silence → VAD re-pass on those ranges (`transcribe_range.py`, `merge_transcript.py`).
- `torchaudio.load` has no backend here; decode 24-bit WAVE_FORMAT_EXTENSIBLE with ffmpeg.
- Approved voice chain: `highpass=f=70,acompressor=threshold=-26dB:ratio=3:attack=5:release=150:makeup=2.512,volume=7.6dB,alimiter=limit=0.79:level=0:latency=1` (`makeup` is linear, not dB).
- When a word's spelling is doubtful, score candidate wordings with CTC `forced_align` and keep the best.
- Fast speakers run ครับ into the next word; CTC char spikes lag the real onset by ~0.1 s. If ctc_peek still hears นะ/คร or loses a neighbour word, rerun with a local copy of cut_ka.py using `PREV_PAD, LEAD, TAIL = 0.0, 0.16, 0.02` and end at `next_start - 0.08` (reel-VID1322).
- `refine_cuts.py` can widen an edge into a word you meant to drop (or make two segments overlap and repeat audio) — compare its output with your plan and keep hand-set edges where it does.
- Long caption chunks auto-wrap into 2 balanced lines (> 20 spacing characters); Latin words get padding. Still prefer 3-7 short words per chunk.
- When the speaker says "I want pictures of <product>", show the real product photos (amway.co.th) as the split visual itself (still + Ken Burns), not just a corner card.
- Never put a stand-in picture of a named person (e.g. a mentor) — keep the speaker on screen unless the user sends a photo.
- Remotion `--scale` must give integer dimensions (0.6667 fails; use 0.5 / 0.25 / 0.2).
- The first `remotion still` calls can time out while the bundle warms up on the external drive — pass `--timeout=90000`.
- A `color=` source in an ffmpeg filter is infinite — give it `d=` or `shortest=1`.
- The safety check blocks `rm -rf` inside `bash -c`; create fresh scratch dirs instead of wiping them.
- Files over 30 MB do not reach the user's phone; always send the 720p preview.
- The ElevenLabs / Grok skills are disabled; clean-audio rescue is not available.

## Completion

`final/reel-final.mp4` ≤ 60 s passes QC, `final/cover.png` + `cover.jpg` exist, the previous version is kept, no ค่ะ/นะคะ left (ctc_peek), every on-screen word was spoken, every SFX file is from the user's folder, Pexels sources are credited in the README, and the Thai report lists what changed, the insert table, QC numbers, file paths, and that nobody has watched the full clip yet unless they have.

## Classic full-screen style (v11/v12) — only on request

Speaker full screen with smooth zoom (`zoom_expr.py`), ✓/✕ text inserts above the head with an SFX on every line (`build_inserts_ass.py`), product cards above the head (`build_overlays.py`, `build_product_card.py`), full-screen HyperFrames cutaways, captions burned with libass (`build_ass.py`), SFX mixed with `mix_sfx.py` + `sfx_audibility.py`, all rendered in one ffmpeg pass:

```zsh
W=.video-edit
ZP=$(python3 -I $W/scripts/zoom_expr.py $W/motion-plan.json)
OV=$(python3 -I $W/scripts/build_overlays.py $W/visual-insert-plan.json $W/cards/inputs.txt 2)
FC=$(python3 -I $W/scripts/edl_filter.py $W/edit-plan.json "${ZP}[base];${OV}ass=$W/captions.ass,ass=$W/inserts.ass,format=yuv420p" drop)
ffmpeg -i source.mov -i $W/audio/mix.wav <card inputs> [-c:v libvpx-vp9 -i explainers.webm] \
  -filter_complex "$FC" -map "[vout]" -map 1:a -c:v libx264 -preset slow -crf 17 -profile:v high -r 30 \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart $W/final/pre-qc.mp4
```

Reference: `/Volumes/JamesM.2/Claude/Video/.video-edit/` (BodyKey v11) and `reel-881f4d72/` (bone reel v4 with cutaways).
