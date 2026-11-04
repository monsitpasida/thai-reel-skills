---
name: broll-selector
description: Select semantically relevant B-roll for a short-form video. Use when matching local user footage or available assets to transcript segments, choosing insert timing, and avoiding decorative or misleading stock footage.
---

# B-roll Selector

Use B-roll to explain, prove, visualize, or reset attention. Do not add footage merely because it looks attractive.

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
- `.video-edit/edit-plan.json`
- `.video-edit/captions.json`
- `.video-edit/analysis.json`

Also inspect user-provided local media folders when available.

## Priority order

1. User's own footage
2. Existing project asset library
3. Licensed/approved external footage
4. Generated visual, only when the workflow explicitly permits generation

Never fabricate a local file path.

## Hard rules

1. Every B-roll insert must have a semantic reason.
2. Typical insert duration: 1-4 seconds.
3. Do not cover an important facial reaction or emotionally important talking-head moment without a strong reason.
4. Avoid repeating the same generic footage.
5. Avoid misleading product demonstrations or visuals that imply facts not stated.
6. Do not download or license third-party footage without permission or an approved workflow.
7. If no suitable asset exists, create a placeholder request instead of pretending one exists.

## Valid reasons for B-roll

- `explain`: makes an abstract statement concrete
- `prove`: shows evidence/example
- `visualize`: shows the object/action being discussed
- `attention_reset`: supports pacing after an extended talking-head stretch

## Workflow

1. Divide the rough cut into semantic beats.
2. Score each beat for B-roll usefulness.
3. Search available assets by:
   - filename
   - metadata
   - visual inspection
   - transcript relevance
4. Select only the strongest inserts.
5. Record exact target timing in final-edit time.
6. Save `.video-edit/broll-plan.json`.

## Output schema

```json
{
  "items": [
    {
      "timeline_start_s": 0.0,
      "timeline_end_s": 0.0,
      "reason": "explain|prove|visualize|attention_reset",
      "spoken_context": "",
      "asset_path": null,
      "asset_in_s": null,
      "asset_out_s": null,
      "fit": "cover|contain|portrait_crop",
      "notes": "",
      "status": "ready|placeholder"
    }
  ]
}
```

## Selection standard

Reject an asset if it is:
- only loosely related by keyword
- visually distracting
- contextually inaccurate
- poor quality relative to the main footage
- likely to create a false implication

## Failure handling

If no suitable B-roll exists:
- keep the talking head
- optionally suggest a text/motion treatment
- mark the requested concept as `placeholder`
- never hallucinate an asset

## Completion criteria

Every planned insert has a clear semantic purpose and valid source path or explicit placeholder status.
