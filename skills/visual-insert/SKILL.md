---
name: visual-insert
description: Plan on-screen graphic inserts for a short-form talking-head video - text callouts, numbers, icons, lists, product cards, screenshots and simple diagrams that explain or emphasize what is being said. Use after captions and B-roll planning, especially when no B-roll footage exists, and before reel-motion renders.
---

# Visual Insert

Add graphics that make a spoken point easier to understand or remember. A visual insert is not decoration and not a second subtitle track.

## Shared project contract

Use a working directory named `.video-edit/` at the project root. Never modify the original source file in place.

Expected shared artifacts:
- `.video-edit/analysis.json`
- `.video-edit/transcript.json`
- `.video-edit/hook.json`
- `.video-edit/edit-plan.json`
- `.video-edit/captions.json`
- `.video-edit/broll-plan.json`
- `.video-edit/visual-insert-plan.json`
- `.video-edit/sound-plan.json`
- `.video-edit/motion-plan.json`
- `.video-edit/qc-report.json`
- `.video-edit/final/`

When an upstream artifact exists, read and reuse it instead of recomputing it unless it is stale or invalid.
Use absolute source timestamps in seconds and preserve at least millisecond precision in JSON.


## Inputs

Read:
- `.video-edit/edit-plan.json`
- `.video-edit/captions.json`
- `.video-edit/broll-plan.json`
- `.video-edit/analysis.json` (face position, safe areas)

Also inspect user-provided brand assets (logo, product images, fonts, colors) when available.

## Insert types

- `callout`: 1-4 word key phrase pulled from what was just said
- `number`: a figure, price, percentage or count that was spoken
- `list`: 2-4 short items the speaker enumerates
- `icon`: a simple pictogram that matches a spoken noun or action
- `product_card`: the user's own product image with its name
- `screenshot`: a real screen or document the speaker refers to
- `diagram`: a simple comparison or before/after that mirrors the spoken argument
- `animation`: a short explainer cutaway (3-8 s) built in HyperFrames when the speaker explains a mechanism, an ingredient, a before/after or a benefit that a still graphic cannot show (see "Explainer animations")

## Layout by framing

- Talking head with room above the head: tall rounded cards (rows of icon + text) centered above the head.
- Close framing (head fills ~20-70% of the height): no tall cards - use one horizontal row of rounded chips in the top band (y ~10-16%), each chip popping in on its word; when a row would exceed the safe width it wraps to a second centered line, lifted so the second line stays on the hair, not the face. Measure chip text widths with the real font (Pillow) - never guess.
- Product image cards go beside the face (e.g. right of it) when there is no room above; a thin product (mascara, pen) gets a portrait card.
- Product photos: prefer the brand's own site (ask the user which site is allowed), trim the white margins before placing them on a card, and never use a promo poster whose badges carry claims the speaker did not make.

## Explainer animations

Use when the user asks for animation that shows what is being explained, or a beat is abstract (how an ingredient works, before/after, something happening over a day).
1. Pick 1-3 beats from the edited transcript; each becomes one scene of 3-8 s. Record word times from `captions.json` (`words[].start_s`) - every element in the scene lands on its word.
2. Write `SPEC.md` (HyperFrames `/hyperframes` workflow): goal, look, objects, motion, safe area (text in y 200-1300 px so the reel's captions stay clear), shots with local times (= reel time - scene start), banned defaults, QA times, and FACTS - every word on screen must be a spoken phrase; no numbers or claims the speaker did not say.
3. Default look (approved by this user): Gen-Z cartoon sticker - flat pastel ground with dots, ink #1B1B3A 6 px outlines, hard 10px 10px sticker shadow, one accent #FF4F6D per shot, Kanit 500/700/800 (woff2 with @font-face), real product photo on a sticker card when the product appears.
4. Scenes enter with an iris (circle clip-path 0 -> 120% in 0.3 s) and leave with a 0.22 s fade, so they cut in and out of the talking head cleanly.
5. Record each scene in `visual-insert-plan.json` under `animations` (`source`, `source_in_s`, `source_out_s`, `timeline_start_s`, `mode: fullscreen_cutaway`) and mark any chips/cards it replaces as `status: replaced`.
6. Keep the SFX on the animation's beats (pop/tick per sticker) and add a whoosh on each transition (`sound-design`).

## Hard rules

1. Every insert must have a semantic reason: `explain`, `emphasize`, `structure` or `attention_reset`.
2. Text in an insert must come from the spoken words (exact or a tight excerpt). Never add claims, numbers, prices or promises the speaker did not say.
3. Do not duplicate the subtitle on screen at the same moment; an insert carries a keyword or structure, not the full sentence.
4. Never cover the speaker's face or mouth. Place inserts beside or above the subject using the face position in `analysis.json`.
5. Stay inside the safe area: away from the bottom UI zone, the right-side action rail and the top status area.
6. Do not overlap a planned B-roll insert unless the graphic is designed to sit on that footage.
7. Use only assets that exist (user files, the project asset library, a component registry already installed) or plain text and shapes. If a needed image is missing, mark the insert `placeholder` - never invent a file path or a product shot.
8. Health, finance and product-performance claims stay exactly as spoken; do not visualize them as stronger than said (no fake charts, no invented before/after).

## Density and timing

- Typical on-screen time: 0.8-2.5 s.
- No more than one insert on screen at a time.
- Leave at least 2 s between inserts; aim for one every 4-8 s at most across a 45-60 s reel.
- Enter on or just after the spoken word it supports (never before it is said), leave before the next idea starts.
- Prefer inserts where the talking head has run uninterrupted for 5 s or more and no B-roll is planned.

## Visual consistency

- One type family, one accent color (reuse the subtitle highlight color unless the brand says otherwise), one corner radius.
- Simple entrances only: pop/scale 90-100%, fade or short slide; 100-200 ms.
- Match the subtitle language and script; check Thai shaping (tone marks and vowels) renders correctly in the chosen font.

## Workflow

1. Read the edited timeline and captions; mark beats that are abstract, list-like, numeric or name a product.
2. Cross out beats already covered by B-roll.
3. Pick the strongest 3-8 beats; choose the insert type for each.
4. Draft the exact text from the spoken words and choose a position that avoids the face and the subtitle block.
5. Resolve assets; mark missing ones `placeholder`.
6. Save `.video-edit/visual-insert-plan.json`. Rendering happens in `reel-motion`.

## Output schema

```json
{
  "style": {
    "font": "",
    "accent_color": "",
    "text_color": "",
    "background": "",
    "corner_radius_px": 0
  },
  "items": [
    {
      "timeline_start_s": 0.0,
      "timeline_end_s": 0.0,
      "type": "callout|number|list|icon|product_card|screenshot|diagram",
      "reason": "explain|emphasize|structure|attention_reset",
      "spoken_context": "",
      "text": "",
      "asset_path": null,
      "position": {"x": 0.5, "y": 0.2, "anchor": "center"},
      "size": {"width_px": 0, "height_px": 0},
      "animation_in": "pop|fade|slide_up",
      "animation_out": "fade|none",
      "status": "ready|placeholder",
      "notes": ""
    }
  ]
}
```

Positions are normalized to the 1080x1920 canvas.

## Failure handling

If no beat clearly benefits from a graphic:
- write an empty `items` list and say so - zero inserts is a valid result
- do not add inserts just to fill time

If brand fonts or colors are unknown:
- reuse the subtitle style from `motion-plan.json` and note the assumption

## Completion criteria

Every insert is tied to a spoken moment, carries only spoken information, avoids the face, subtitles and platform UI, and has a valid asset or explicit placeholder status.
