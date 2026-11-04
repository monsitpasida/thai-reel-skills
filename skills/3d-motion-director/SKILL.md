---
name: 3d-motion-director
description: Direct and build 3D motion cutaways (three.js inside HyperFrames) for the user's vertical Thai Reels - a hero object, a camera move and labels timed to spoken words, rendered as a 1080x1920 WebM that the Reel pipeline overlays. Use when the user asks for 3D, a 3D scene, a 3D product or body-part shot, "3d-motion-director", or when an explainer beat (bone, cell, capsule, product bottle, molecule) would read better as a turning object than as a flat sticker.
---

# 3D Motion Director

Turns one spoken explainer beat into a short 3D shot: one hero object, one camera move, one or two labels, each landing on its word. Output plugs into the `thai-talking-head-edit` pipeline exactly like the flat HyperFrames cutaways (same webm overlay chain, same SFX rules).

**Talk to the user in Thai only.** File names, code and commands stay in English.

## When 3D earns its place

- A physical thing the viewer should *see from several sides or inside*: bone structure, a capsule dissolving, a cell, a joint, a product bottle turning to its label.
- A process in space: nutrients flowing into a bone, a shield forming around a cell, layers peeling apart (exploded view).
- Not for: plain lists, numbers, ✓/✕ lines (keep those as 2D inserts), or anything the speaker did not say.

Max 1-2 3D shots per 60 s Reel; they cost render time (~4-8 s per second of 3D on this 8 GB Mac).

## Director's workflow

1. **Beat sheet** - from `captions.json`, pick the spoken span (reel time) and list the key words with their `start_s`. Scene time = reel time − scene start.
2. **Shot card** in the project's `SPEC.md`, one block per shot:
   - hero object (what it is, built from primitives or a real product photo on a plane/cylinder)
   - camera move: one of `dive` (push in through/into the object), `reveal` (slow arc 20-35° + dolly), `exploded` (parts separate along an axis), `orbit-stop` (half turn that settles on the label/front)
   - beats: `word @ t → what changes` (scale pop, part lights up, label pops, particles flow)
   - labels: only spoken words, Thai, Kanit 800 sticker labels in HTML over the canvas
3. **Build** from `templates/scene3d.html` (copy into `compositions/<id>.html`) and mount it in `index.html` like the other scenes.
4. **Check** - `check --json`, then `snapshot --at` the first frame, every beat and the last frame; look at them.
5. **Render** with the rest of the cutaways (`render --format webm`), composite per the pipeline, run the reel QC.

## Camera grammar (keep it calm, phone-sized)

- One move per shot, eased (`easeInOutCubic`), lasting most of the shot; hold the last 0.3 s still before the cut.
- FOV 30-40°; hero fills 45-60 % of frame width; keep it centred in y 450-1200 so captions (y ≥ 1400) stay clear.
- Max rotation speed ≈ 60°/s; no spinning loops, no shaky cam, no Dutch angles.
- Labels and stickers sit at y 200-1300, never over the hero's key detail.

## Look (matches the approved flat sticker style)

- Background: the scene's pastel dotted HTML background (same as 2D scenes); canvas transparent on top.
- Materials: `MeshToonMaterial` with a 3-step gradient map, flat pastel colours from the palette (ink #1B1B3A, accent #FF4F6D, green #3BB273, yellow #FFD34D, lavender, sky). Ink outline via the inverted-hull pass (back-face copy scaled 1.03-1.05, ink colour).
- Light: one warm key from upper-left, one soft fill; a blurred ink contact shadow (a transparent plane with a radial-gradient texture) under the hero.
- Banned: realistic PBR chrome, bloom/glow, dark or navy backgrounds, gradients on text, invented numbers/claims.

## Technical rules (HyperFrames + three.js)

- three.js r149 classic build (global `THREE`): `<script src="https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js"></script>` inside **each 3D scene file** (lint `missing_three_script` fails if it only sits in index.html). No OrbitControls, no `requestAnimationFrame` loop.
- Draw every frame from time only, driven by the scene's own GSAP timeline: a `clock` proxy tweened 0→DUR with `ease: "none"` and `onUpdate: () => renderAt(clock.t)`, plus `renderAt(0)` once (see template). This keeps the canvas in sync with the scene's place in the root; frames render out of order.
- Framing reference (tested): FOV 34, a 3.5-unit-wide hero at camera distance 14-17 fills ≈ 55-65 % of the 1080 width.
- Renderer: `antialias: true, alpha: true, preserveDrawingBuffer: true`, `setPixelRatio(1)`, size 1080x1920, `setClearColor(0x000000, 0)`.
- Randomness: seeded mulberry32 only. Particles: precompute positions per index; position = f(t).
- Heavy setup (texture loads) → `window.__hf.buildReady["<id>"] = promise`.
- Labels are HTML stickers animated by the scene's GSAP timeline (registered in `window.__timelines["<id>"]`), so they follow the same lint rules as the 2D scenes (svgOrigin baselines, no repeated fromTo, finite repeats).
- Product images: use the real cropped product PNG as a texture on a rounded plane or cylinder wrap - never model a fake label.

## Known pitfalls

- A blank/black frame usually means a NaN (divide by zero in an ease or normalise) or the module script failing to load - check `check --json` runtime errors first.
- Toon materials need `gradientMap.minFilter = magFilter = NearestFilter` or the bands blur.
- Inverted-hull outlines need `side: BackSide` and the hull must share the hero's transform (add it as a child).
- Decode the rendered webm with `-c:v libvpx-vp9` before `-i` or the alpha is lost.

## Completion

The shot matches its card in `SPEC.md`, every beat lands on its spoken word in snapshots, nothing covers the caption zone, the webm renders, and the report to the user (in Thai) lists the shots, their reel times and file paths.
