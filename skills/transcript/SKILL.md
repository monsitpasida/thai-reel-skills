---
name: transcript
description: Transcribe spoken video or audio with word-level timestamps for editing and subtitles. Use for Thai or multilingual speech, subtitle timing, filler detection, quote selection, and edit decisions that must match the actual spoken words.
---

# Transcript

Create a timestamp-accurate transcript that can drive non-destructive editing.

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

Produce a faithful transcript with segment and word timestamps. Preserve exactly what was said. This transcript is the source of truth for cuts and subtitles.

## Preferred engines

Use the best available local engine in this order:
1. `faster-whisper`
2. `whisper`
3. another installed ASR engine that returns timestamps

On this machine `faster-whisper` is installed in a dedicated venv: run it with `~/.venvs/whisper/bin/python` (not the system `python3`).

Do not install global packages without user approval. A local project environment is acceptable when the user has already asked Claude Code to set up the workflow.

## Hard rules

1. Word-level timestamps are required whenever the engine supports them.
2. Preserve spoken wording; do not rewrite grammar.
3. Preserve Thai particles, repeated words, and fillers in the raw transcript.
4. Mark uncertain recognition rather than inventing a word.
5. Detect language automatically, but prefer Thai decoding when the audio is predominantly Thai.
6. Do not translate unless the user explicitly requests translation.
7. Do not remove filler words in the transcript. Removal happens in `reel-rough-cut`.

## Workflow

1. Read `.video-edit/analysis.json` when available.
2. Extract clean temporary audio only if the ASR engine needs it.
3. Transcribe the entire relevant source.
4. Capture:
   - segment start/end
   - segment text
   - word start/end
   - word text
   - confidence/probability when available
5. Create a plain text transcript for human inspection.
6. Save machine-readable output to `.video-edit/transcript.json`.

## Output schema

```json
{
  "language": "th",
  "source_path": "/absolute/path/source.mov",
  "duration_s": 0.0,
  "segments": [
    {
      "start_s": 0.0,
      "end_s": 0.0,
      "text": "",
      "words": [
        {
          "start_s": 0.0,
          "end_s": 0.0,
          "text": "",
          "confidence": null
        }
      ]
    }
  ],
  "uncertain_ranges": []
}
```

Also write:
- `.video-edit/transcript.txt`

## Thai-specific guidance

- Keep spoken Thai natural and literal.
- Do not force spaces into words solely for display.
- Do not normalize the transcript into formal written Thai.
- Numbers may be stored as recognized speech; downstream caption rendering may choose a display form only if it does not change meaning.

## Validation

Before completion:
- timestamps must be monotonic
- each word must fall inside or very near its parent segment
- transcript duration must not exceed media duration materially
- no invented sentences may appear

## Failure handling

If confidence is poor because of noise or music:
- mark ranges in `uncertain_ranges`
- do not guess
- recommend audio cleanup or a second ASR pass only for those ranges

## Completion criteria

`.video-edit/transcript.json` and `.video-edit/transcript.txt` exist and reflect the complete spoken content needed for editing.
