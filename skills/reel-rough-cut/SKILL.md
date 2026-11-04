---
name: reel-rough-cut
description: Build and execute a tight 45-60 second talking-head rough cut for Instagram Reels, TikTok, or Shorts. Use for removing greetings, filler, repeated ideas, dead air over 0.6s, false starts, and low-value sections while preserving the speaker's actual meaning.
---

# Reel Rough Cut

Create a high-retention 45-60 second edit using only authentic spoken material.

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
- `.video-edit/analysis.json`
- `.video-edit/transcript.json`
- `.video-edit/hook.json`

## Target

- Format intent: vertical short-form
- Final content duration: 45-60 seconds when the source supports it
- Pace: concise conversational
- Primary technique: jump cuts
- Hook: first 0-3 seconds

## Hard rules

1. Analyze the full transcript before cutting.
2. Remove unnecessary:
   - greetings
   - setup that does not add value
   - filler words
   - false starts
   - repeated sentences
   - repeated ideas
   - dead air longer than 0.6 seconds
3. Preserve meaningful dramatic pauses.
4. Never create words the speaker did not say.
5. Preserve the original meaning and factual context.
6. Do not duplicate the relocated hook in the body unless repetition is clearly intentional.
7. Do not stretch, duplicate, or fabricate content just to reach 45 seconds.
8. Prefer semantic cuts at phrase boundaries over cuts that damage speech rhythm.
9. Keep enough pre/post roll around speech to avoid clipped consonants and unnatural breaths.

## Edit decision priority

Keep material that does at least one of these:
- answers the central question
- provides evidence
- gives a useful example
- creates curiosity/payoff
- supports the CTA
- is necessary for truthful context

Cut material that does none of them.

## Dead-air rule

- Candidate dead air: silence > 0.6 s
- Preserve a pause when it contributes to emphasis, emotion, comprehension, or transition.
- Do not automatically remove every detected silence.

## Workflow

1. Place the selected hook first.
2. Build the body in a coherent order.
3. Remove duplicated hook content from its original position.
4. Generate an edit decision list (EDL).
5. Validate expected duration.
6. Execute the rough cut with FFmpeg or another deterministic editor.
7. Prefer one high-quality re-encode over repeated generation loss.
8. Save:
   - `.video-edit/edit-plan.json`
   - `.video-edit/rough-cut.mp4`

## Edit-plan schema

```json
{
  "target_duration_s": 0.0,
  "segments": [
    {
      "source_path": "/absolute/path/source.mov",
      "source_start_s": 0.0,
      "source_end_s": 0.0,
      "role": "hook|body|cta",
      "reason": ""
    }
  ],
  "removed_ranges": [
    {
      "start_s": 0.0,
      "end_s": 0.0,
      "reason": "filler|repeat|dead_air|intro|false_start|low_value"
    }
  ],
  "warnings": []
}
```

## FFmpeg guidance

For accurate cuts:
- use `trim`/`atrim` with `setpts`/`asetpts` and concat when frame-accurate editing is required
- avoid depending on stream-copy cuts for exact speech boundaries
- preserve A/V sync
- do not normalize loudness here unless needed to prevent clipping; final loudness belongs in export/QC

## Failure handling

- If usable source content is under 45 seconds, create the strongest truthful edit and add a warning instead of padding.
- If the source cannot be reduced below 60 seconds without losing essential meaning, produce the shortest coherent version and flag the conflicting segments.
- If an edit point clips a word or breath unnaturally, widen the boundary and re-render.

## Completion criteria

The rough cut is coherent, authentic, fast-paced, and `.video-edit/edit-plan.json` exactly describes the exported rough cut.
