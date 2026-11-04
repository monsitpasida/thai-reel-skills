---
name: reel-hook
description: Find the strongest authentic 0-3 second spoken hook from a transcript for an Instagram Reel, TikTok, or Short. Use when choosing a cold open, strongest quote, curiosity gap, or high-retention opening without inventing dialogue.
---

# Reel Hook

Select the strongest real quote from the source material for the first 0-3 seconds.

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
- `.video-edit/transcript.json`
- `.video-edit/analysis.json` when available

## Hard rules

1. The hook must use words actually spoken in the source.
2. Never synthesize a new spoken sentence.
3. Target duration: 0-3.0 seconds.
4. The hook may come from anywhere in the source.
5. If the hook is moved from later in the video, remove its duplicate occurrence from the body edit unless repetition is editorially justified.
6. Do not select misleading context merely because it sounds dramatic.
7. Prioritize immediate comprehension over clickbait.

## Scoring

Score candidate quotes from 1-10 on:
- curiosity
- clarity without setup
- specificity
- emotional or practical payoff
- relevance to the main message
- natural spoken rhythm
- ability to stand alone in <= 3 seconds

Avoid greetings such as:
- สวัสดีค่ะ
- วันนี้เราจะมา...
- คลิปนี้จะพูดถึง...

unless the greeting itself contains the main value proposition, which is rare.

## Workflow

1. Read the whole transcript before choosing.
2. Generate 3-5 candidate spans using exact source timestamps.
3. Reject candidates that depend heavily on previous context.
4. Choose one primary hook.
5. Record 1-2 backups.
6. Save `.video-edit/hook.json`.

## Output schema

```json
{
  "primary": {
    "start_s": 0.0,
    "end_s": 0.0,
    "duration_s": 0.0,
    "exact_text": "",
    "score": 0,
    "reason": ""
  },
  "alternates": [],
  "context_risk": "low|medium|high"
}
```

## Failure handling

If no useful quote fits inside 3 seconds:
- choose the strongest shorter fragment that remains truthful
- never paraphrase the spoken line
- flag `context_risk`
- allow visual title text only if the user has requested editorial text overlays; it must not masquerade as spoken subtitles

## Completion criteria

The primary hook is authentic, <= 3 seconds, and traceable to exact transcript timestamps.
