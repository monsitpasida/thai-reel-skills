---
name: captions-th
description: Create readable Thai short-form captions synchronized to the edited audio. Use for Thai subtitles, word highlighting, 3-7 word caption chunks, maximum two lines, and timing derived from real speech rather than paraphrased text.
---

# Thai Captions

Generate subtitles that match the final spoken edit.

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
- `.video-edit/edit-plan.json`
- `.video-edit/rough-cut.mp4`

## Hard rules

1. Captions must match the actual edited speech.
2. Do not paraphrase.
3. Aim for 3-7 words or short Thai semantic units per caption.
4. Maximum 2 lines on screen.
5. Break captions at natural phrase boundaries.
6. Never display a later phrase before it is spoken.
7. Highlight only meaningful keywords; do not highlight every word.
8. Subtitles are not a place to add new factual claims.
9. Editorial CTA/title overlays must be stored separately from subtitles.

## Timing

- Re-map source transcript timestamps through the EDL.
- Prefer word-level timing.
- Keep captions readable without lagging behind speech.
- Avoid extremely short flashes; merge fragments when semantically safe.
- Avoid a caption lingering into the next sentence.

### Do not trust Whisper word timestamps for Thai

Whisper tokenizes Thai into sub-character pieces; its word timestamps drift +/-0.2-0.5 s and single tokens can absorb whole pauses or retakes. Use them only to find text and rough segment bounds, never as final caption or word timing.

### Forced alignment (preferred)

Align the known caption text to the edited audio (`rough-cut.mp4` downmixed to 16 kHz mono) with CTC forced alignment:
- Model: `airesearch/wav2vec2-large-xlsr-53-th` (Thai characters only, 20 ms frames) via `transformers` + `torchaudio.functional.forced_align` / `merge_tokens`. Install into a local venv only with the user's OK (~2.4 GB model plus PyTorch); check free disk first.
- Align the whole edit in one pass so captions cannot drift relative to each other.
- Convert text to its spoken form for the aligner only (display text stays as written): Latin brand names to Thai spelling (e.g. BodyKey -> บอดี้คีย์), `ๆ` repeats the word it follows (apply per word, not per phrase), drop characters missing from the model vocab.
- Caption start = first aligned character - 0.04 s; first caption of the video starts at 0.0. Caption end = last character + up to 0.3 s hold, never past the next caption's start.
- Read audio with `wave`/ffmpeg, not `torchaudio.load` (no audio backend in a plain pip install).

### Word-level timing (for word-by-word highlight)

When the motion style needs per-word highlight:
- Segment each caption into words with PyThaiNLP (`word_tokenize(engine="newmm", keep_whitespace=False)`), merge a standalone `ๆ` into the previous word, and fix known mis-splits with an explicit table (e.g. `เรื่อ|งอด` -> `เรื่อง|อด`). Assert the joined words equal the caption text.
- Run the forced alignment with one target sequence per word so every word gets its own start.
- Store two ends per word: `end_s` = next word's start (the word's slot, used for merging) and `spoken_end_s` = its last aligned character (where the renderer switches the highlight off). Never overwrite the real end with the next start.
- Merge words active for under 0.15 s into the next word (e.g. `ไม่|ใช่|แค่` -> `ไม่ใช่แค่`); fold a too-short last word into the one before it.
- Store the result as `words` on each caption item; caption start/end must not change when words are added.

### Verifying sync

- Spot-check caption starts against the loudness envelope (speech onset at 10-50 ms resolution) and against source-level word times mapped through the EDL.
- Re-transcribing each caption window on its own is only a rough signal: short clips transcribe poorly and windows that start early score too well. Do not tune timing to that score alone.

## Thai line breaking

Prefer breaks at:
- clause boundaries
- conjunctions
- natural pauses
- semantic groups

Avoid:
- splitting a person's name
- splitting a number from its unit
- splitting a short phrase so aggressively that meaning becomes harder to read

## Keyword highlighting

Good candidates:
- numbers
- product/category names when spoken
- key benefit nouns
- contrast words
- central action words

Store highlights as character or token ranges in JSON. Do not hard-code styling here.

## Outputs

Write:
- `.video-edit/captions.json`
- `.video-edit/captions.srt`

## JSON schema

```json
{
  "language": "th",
  "items": [
    {
      "start_s": 0.0,
      "end_s": 0.0,
      "text": "",
      "lines": [""],
      "highlights": [
        {"text": "", "type": "keyword"}
      ],
      "words": [
        {"text": "", "start_s": 0.0, "end_s": 0.0, "spoken_end_s": 0.0}
      ]
    }
  ]
}
```

`words` is optional; include it when word-level timing was produced. Word texts joined (ignoring spaces) must equal `text`. Times are on the edited (rough-cut) timeline.

## Validation

Check:
- all caption times are monotonic
- no caption crosses an edit boundary incorrectly
- max two rendered lines
- spoken meaning is unchanged
- no caption refers to audio that was cut
- when `words` exist: word times are monotonic, lie inside their caption, no word step is shorter than 0.15 s, and the words reassemble the caption text exactly

## Failure handling

If transcription around a cut is uncertain, inspect/listen to the relevant range rather than guessing.

## Completion criteria

Captions are synchronized, concise, readable in Thai, and can be consumed directly by Remotion or converted to another subtitle format.
