---
name: reel-export-qc
description: Render and quality-check the final Instagram Reel, TikTok, or Short. Use for final H.264/AAC export, duration and aspect checks, audio loudness, black-frame/silence detection, subtitle-safe-area review, sync verification, and final pass/fail reporting.
---

# Reel Export & QC

Render once, inspect systematically, and deliver only after critical checks pass.

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
- `.video-edit/final/pre-qc.mp4`
- `.video-edit/edit-plan.json`
- `.video-edit/captions.json`
- `.video-edit/broll-plan.json`
- `.video-edit/visual-insert-plan.json` when it exists
- `.video-edit/sound-plan.json` when it exists
- `.video-edit/motion-plan.json`

## Delivery target

Default social master:
- 9:16
- 1080 x 1920
- H.264 video
- `yuv420p`
- AAC audio
- 48 kHz audio
- web optimized / fast start

Frame rate:
- preserve a sensible source rate when possible
- do not invent high frame-rate motion by upconverting 30 fps to 60 fps without a reason

Quality:
- use visually high-quality H.264 settings suitable for social upload
- avoid unnecessary multiple re-encodes

Audio target:
- target approximately -14 LUFS integrated for social playback unless the user's mastering standard differs
- true peak should stay safely below clipping, typically around -1 dBTP

## Hard QC checks

1. File opens and decodes.
2. Final frame size is 1080x1920 unless an explicit alternate target exists.
3. Aspect ratio is 9:16.
4. Duration is 45-60 seconds when the source supports the requested target.
5. No accidental black frames.
6. No accidental long silence caused by editing.
7. Speech is in sync with image.
8. Captions match spoken audio.
9. Captions stay readable and inside safe areas.
10. B-roll references are valid and intentional.
11. No clipped first/last syllables at jump cuts.
12. No audio clipping or obviously broken loudness transitions.
13. Hook begins immediately and is not preceded by dead air.
14. CTA/ending is not cut off.
15. No temporary/debug overlays remain.
16. Visual inserts appear on the planned frames, never cover the face or a subtitle, and carry only spoken information; no placeholder graphic was rendered.
17. Music and SFX never mask speech: voice stays dominant in every caption range, and no SFX lands on a word.
18. Every music/SFX file in `sound-plan.json` has a recorded source and license note.

## Useful tools

Use:
- `ffprobe` for dimensions, duration, streams
- FFmpeg `blackdetect` for suspicious black sections
- FFmpeg `silencedetect` for suspicious silence
- FFmpeg loudness measurement (`ebur128` or `loudnorm`) for audio checks

Automated detection is advisory; visually/audibly inspect flagged ranges before declaring a failure.

## Export

Write final file to:
- `.video-edit/final/reel-final.mp4`

Write:
- `.video-edit/qc-report.json`

## QC report schema

```json
{
  "status": "pass|pass_with_warnings|fail",
  "output_path": ".video-edit/final/reel-final.mp4",
  "duration_s": 0.0,
  "width": 1080,
  "height": 1920,
  "fps": 0.0,
  "video_codec": "h264",
  "audio_codec": "aac",
  "integrated_lufs": null,
  "true_peak_db": null,
  "checks": [
    {
      "name": "",
      "status": "pass|warn|fail",
      "details": ""
    }
  ],
  "warnings": []
}
```

## Failure handling

- Do not label the render complete if a critical QC item fails.
- Fix only the failing stage when possible; do not rebuild unrelated work.
- If the source itself prevents the 45-60 second target, allow `pass_with_warnings` when the edit is otherwise correct.
- Never hide a technical limitation.

## Completion criteria

The final file exists, passes critical checks, and `qc-report.json` records the exact output properties and any warnings.
