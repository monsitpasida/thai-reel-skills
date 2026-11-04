---
name: video-analyze
description: Analyze raw video footage before editing. Use for inspecting source video, technical metadata, visual quality, scene structure, pacing risks, framing, orientation, audio presence, and editability for Reels/TikTok/Shorts.
---

# Video Analyze

You are the pre-edit analyst for short-form social video.

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


## Goal

Inspect the source footage once and produce a reliable machine-readable analysis that downstream skills can reuse.

## Inputs

Required:
- One or more source video files.

Optional:
- User's target platform.
- Desired final duration.
- Reference style or editing rules.

## Hard rules

1. Do not edit or overwrite source media.
2. Prefer `ffprobe` for technical metadata.
3. Inspect representative frames; do not extract every frame unless specifically necessary.
4. If the video is long, sample intelligently around scene changes and regular intervals.
5. Separate observed facts from editorial recommendations.
6. Do not infer spoken wording here; transcription belongs to `transcript`.
7. Report uncertainty explicitly.

## Workflow

1. Validate that each media path exists and is readable.
2. Use `ffprobe` or an equivalent media inspector to capture:
   - duration
   - width / height
   - aspect ratio
   - frame rate
   - codec
   - pixel format
   - variable vs constant frame-rate indicators
   - audio stream presence
   - audio sample rate / channels
3. Inspect frames for:
   - talking-head vs B-roll
   - camera angle and headroom
   - face position
   - lighting consistency
   - obvious blur / shake
   - exposure problems
   - cuts / retakes
   - overlays or burned-in text
   - black frames or corrupted sections
4. Identify major visual sections and approximate time ranges.
5. Flag likely editing constraints for a 9:16 short-form output.
6. Save `.video-edit/analysis.json`.

## Output schema

```json
{
  "source_files": [
    {
      "path": "/absolute/path/source.mov",
      "duration_s": 0.0,
      "width": 0,
      "height": 0,
      "fps": 0.0,
      "video_codec": "",
      "audio_codec": "",
      "sample_rate_hz": 0,
      "channels": 0,
      "orientation": "portrait|landscape|square|unknown",
      "notes": []
    }
  ],
  "visual_sections": [
    {
      "start_s": 0.0,
      "end_s": 0.0,
      "type": "talking_head|broll|screen|other",
      "description": ""
    }
  ],
  "quality_flags": [],
  "reel_constraints": [],
  "recommended_next_skill": "transcript"
}
```

## Failure handling

- If the file is corrupt, identify the failing stream and report the exact file.
- If `ffprobe` is unavailable, use another installed media inspector.
- Do not install global dependencies silently.
- If the source has no usable audio, record that clearly so transcript-dependent skills do not fabricate dialogue.

## Completion criteria

The skill is complete only when `.video-edit/analysis.json` exists, is valid JSON, and references the exact source files inspected.
