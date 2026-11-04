---
name: reel-motion
description: Apply motion design to a vertical Reel/TikTok/Short, including dynamic punch-in zooms, subtitle placement, title cards, B-roll layout, and optional CTA overlays. Use after rough cut and captions are ready.
---

# Reel Motion

Add controlled visual emphasis without making the edit feel over-animated.

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
- `.video-edit/rough-cut.mp4`
- `.video-edit/captions.json`
- `.video-edit/broll-plan.json`
- `.video-edit/visual-insert-plan.json` when it exists
- `.video-edit/sound-plan.json` and `.video-edit/audio/mix.wav` when they exist
- `.video-edit/edit-plan.json`

## Canvas

Default delivery canvas:
- 1080 x 1920
- 9:16
- portrait

Preserve source quality. Do not upscale aggressively when the source cannot support it.

## Dynamic zoom rules

Use these exact intent ranges:
- Normal: 100%
- Emphasis: 105-108%
- Strong emphasis / Hook: 108-112%

Rules:
1. Hook may use strong emphasis.
2. Important claims or transitions may use emphasis.
3. Do not zoom on every sentence.
4. Avoid sudden scale changes that feel like mistakes.
5. Reframe around the face/subject, not simply the geometric center.
6. Return to normal framing when emphasis ends.

### Smooth zoom (default)

Instant scale steps inside a continuous take read as stiff, and a frozen frame between zooms makes every change feel bigger. Default to this motion model:

- **Drift:** every zoom event moves linearly from `scale_from` to `scale_to` over its whole duration - a slow push-in of about 0.5-3% per event (roughly 0.3-0.5%/s). Normal events may drift up to ~102.5%; keep emphasis and hook inside their ranges at both ends.
- **Ease, inside a take:** when the scale changes where there is no picture cut (a punch-in on a key phrase, or a return to normal), blend from the previous event's end scale into the new drift line over `ease_s` 0.4-0.6 s with easeInOutCubic.
- **Hook entry:** start slightly wide (`enter_from` ~1.02) and ease-out into the hook scale over 0.6-0.8 s, so the video opens with motion.
- **At jump cuts:** change scale on the cut frame itself (the picture jumps anyway); the new event then drifts. Alternate scale at consecutive cuts so each cut reads as intentional.
- Peak speed inside an ease should stay under ~2% scale per frame at 30 fps; lengthen `ease_s` if it is higher.

Rendering without jitter:
- Static zoom can use a direct crop. Animated zoom with FFmpeg `zoompan` rounds the crop to whole input pixels, which shimmers on slow moves. Upscale first (lanczos, 3x, e.g. 720x1280 -> 2160x3840) and let `zoompan` (`d=1`, `s=1080x1920`, `fps=30`, zoom as a function of `it`) crop and downscale.
- Anchor x/y on the face center from `analysis.json` and clamp to the frame: `x = max(0, min(iw-iw/zoom, ax*iw - iw/zoom/2))`, same for y.
- Build the zoom expression from `motion-plan.json` with a script, and evaluate the same formula per frame before rendering: values within range, continuous except on cut frames, peak ease speed noted.

Verify after rendering:
- Measure frame-to-frame motion of a background patch (phase correlation): eased zooms should ramp smoothly with no single-frame jump; drift sections should move at the planned rate with no visible wobble (compare against a static-zoom render to separate measurement noise from jitter).
- Look at a strip of frames across one eased zoom.

## Subtitle layout

- Keep subtitles comfortably inside the vertical safe area.
- Maximum two lines.
- Avoid the bottom UI zone and right-side interaction controls.
- Keep subtitle styling consistent across the clip.
- Highlight selected keywords from `captions.json`, not arbitrary words.

## Word-by-word highlight

Use when the user asks for karaoke / word-by-word captions and `captions.json` items carry `words` (see `captions-th`). Record the choice in `motion-plan.json` `subtitle_style` (`mode: "word_highlight"` plus the colors below).

One accent on screen at a time:
- **Active** word: dark text (e.g. `#111111`) on a thick accent outline (12-16 px, accent = subtitle highlight color, shadow off) - a highlighter "pill".
- **Every other word** (upcoming and already spoken): plain white with the normal outline.
- Do not leave keywords accent-colored after they are spoken. Viewers read any leftover accent as "still being said"; in testing it was reported as yellow lingering after speech. Static keyword color is for non-word-highlight captions only.

Pill timing:
- The pill turns on at the word's start and **off 0.1 s after the word's last aligned sound** (`spoken_end_s` from `captions-th`), not when the next word starts.
- In a pause inside a caption, and during the caption's hold after the last word, no word is lit (all white).
- QC: total pill time beyond `spoken_end_s + 0.1` should be ~0 (only centisecond rounding), and no event may contain more than one pill.

Rendering rules:
1. Do not scale or bold the active word - it changes glyph advance and the centered line jumps. Outline width does not change advance, so the pill is jitter-free.
2. One subtitle event per word state: the caption's first event starts at the caption start (with the normal pop), each later event at its word's start, the last ends at the caption end. No gaps, no overlaps.
3. Split color runs only at grapheme boundaries: a Thai combining mark (above/below vowels, tone marks, ์) must stay in its base character's run, or shaping breaks.
4. Spaces take the state of the word before them.
5. Check frames at several word steps for: no line shift, tone marks inside the pill, pill not touching neighboring words.
6. When previewing an ASS overlay on a frame grabbed with input `-ss`, add `-copyts` (or seek after `-i`); otherwise the overlay sees time 0. Do not preview new captions on a render that already has captions burned in.

## B-roll

Follow `.video-edit/broll-plan.json`.
- Use clean cut, mask, or simple motion only when appropriate.
- Do not overuse transitions.
- Preserve spoken-audio continuity unless a deliberate sound edit is requested.

## Visual inserts

Render items from `.video-edit/visual-insert-plan.json` exactly as planned (timing, position, text, animation).
- Skip items with `status: placeholder`; list them as warnings instead of drawing a stand-in.
- Keep inserts above the subtitle layer only where they do not overlap it; never let an insert hide a subtitle.
- Use the plan's style block; do not restyle per insert.

## Explainer animations (HyperFrames cutaways)

Build the scenes planned in `visual-insert-plan.json` `animations` as one HyperFrames project next to the edit (e.g. `<clip>/anim/`), scenes back to back on the root timeline:
- Load `/hyperframes:hyperframes` first. With the plugin install, run the CLI through the plugin launcher (`node <PLUGIN_ROOT>/skills/hyperframes/scripts/plugin-cli.mjs <command>`), from the project folder: `init <dir> --example blank --non-interactive --resolution portrait`, then `check --json` (0 errors), then `snapshot --at <QA times>` and look at the contact sheet before rendering.
- Never tween a `.clip` element itself (except opacity): wrap the scene in a child (`#x-inner`) and animate that (iris clip-path, fade). Use `fromTo`; SVG parts rotate with `svgOrigin`.
- Root background transparent; render `render --format webm --fps 30 -o renders/<name>.webm` (VP9 with alpha, ~1-2 MB) - not ProRes MOV when disk space is tight.
- Composite in FFmpeg after the zoom and image cards, before the ASS captions/inserts: decode with `-c:v libvpx-vp9 -i anim.webm` (the native VP9 decoder drops alpha), `format=yuva420p,split`, per scene `trim=IN:OUT,setpts=PTS-STARTPTS+START/TB`, then `overlay=eof_action=pass:format=auto`. Captions stay on top and must remain readable over the scene.
- Verify alpha before compositing (alphaextract mean: 0 before the iris, 255 mid-scene), and check frames just before, inside and just after each cutaway.
- Shell (zsh): write `${VAR}[label]`, never `$VAR[label]` - zsh treats `[...]` after a variable as a subscript and silently drops the filter string.

## Audio

If `.video-edit/audio/mix.wav` exists, use it as the audio track instead of the rough-cut voice. It is already on the edited timeline; do not re-trim or re-time it. Keep zoom events and SFX from `sound-plan.json` aligned (a `hit` linked to a zoom must land on that zoom's frame).

## Editorial overlays

Allowed when explicitly requested:
- hook title
- concise topic label
- CTA such as a follow prompt

These overlays are not subtitles and must not imply the speaker said words they did not say.

## Remotion guidance

Prefer Remotion when:
- word highlighting is needed
- reusable subtitle components are needed
- punch-in animation must be parameterized
- CTA/title treatments need consistent layout

Keep timing in data files rather than scattering magic numbers across components.

## Output

Write `.video-edit/motion-plan.json`:

```json
{
  "canvas": {"width": 1080, "height": 1920, "fps": 30},
  "zoom_anchor": {"x": 0.5, "y": 0.5},
  "supersample": 3,
  "zoom_events": [
    {
      "start_s": 0.0,
      "end_s": 0.0,
      "scale_from": 1.08,
      "scale_to": 1.11,
      "transition": "cut|ease",
      "ease_s": 0.5,
      "ease_curve": "in_out|out",
      "enter_from": 1.02,
      "reason": "hook|normal|emphasis|strong_emphasis"
    }
  ],
  "broll": [],
  "subtitle_style": {},
  "overlays": []
}
```

`scale_from`/`scale_to` are the drift endpoints of that event. `ease_s`, `ease_curve` apply only to `transition: "ease"`; `enter_from` is only for the first event (default: the previous event's `scale_to`). Zoom events cover the whole timeline with no gaps.

Then render:
- `.video-edit/final/pre-qc.mp4`

## Failure handling

If face tracking/reframing is unreliable:
- prefer a stable manual crop over jittery auto-tracking

If a motion effect reduces legibility:
- remove the effect

## Completion criteria

The video is visually intentional, subtitles remain readable, emphasis is selective, and motion never changes the spoken meaning.
