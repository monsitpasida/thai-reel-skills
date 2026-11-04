---
name: sound-design
description: Design and mix the audio for a short-form talking-head video - voice cleanup, background music bed with ducking, and sparing sound effects on cuts, punch-ins and graphic inserts. Use after the edit, captions, B-roll and visual inserts are planned and before reel-motion renders; produces a mixed audio stem on the edited timeline.
---

# Sound Design

Make the voice clear and the edit feel finished. The voice is always the priority; music and effects support it and never compete with it.

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
- `.video-edit/rough-cut.mp4` (voice on the edited timeline)
- `.video-edit/edit-plan.json` (cut points)
- `.video-edit/captions.json` (where speech is)
- `.video-edit/broll-plan.json`
- `.video-edit/visual-insert-plan.json`
- `.video-edit/motion-plan.json` when zoom events already exist

Also inspect user-provided music and SFX folders when available.

## Step 0: install the SFX library

Before choosing any SFX, run:

```bash
bash ~/.claude/skills/sound-design/scripts/install-sfx.sh
```

It downloads the user's SFX pack from Google Drive (zip, shared by link) only when this machine does not have it yet, and prints the SFX folder path on its last line. Use that path as the SFX library. To publish a new pack, the user uploads a new zip; replace `SFX_FILE_ID` in the script. If the download fails, report it and continue with a voice-only mix.

## Asset rules

Priority order:
1. Music/SFX the user supplied
2. The project's own licensed library
3. Royalty-free or generated audio, only when the user has approved that source

Hard rules:
1. Never download or use commercial music without a license the user confirms.
2. Never fabricate a file path; if no suitable track exists, mark music as `placeholder` and deliver a voice-only mix.
3. Record the source and license note for every external file in `sound-plan.json`.
4. Do not add music to platform-native audio plans (e.g. the user will pick a trending sound in-app) - ask or leave it out.

## Voice

- Light cleanup only: high-pass around 60-80 Hz, gentle compression, optional de-ess. No heavy noise reduction that makes speech watery.
- Short fades (10-20 ms) at every edit point to avoid clicks.
- Never time-stretch, pitch-shift or rearrange words; never synthesize voice.

## Music bed

- Choose energy and tempo that fit the message; a calm explainer gets a low, steady bed.
- Duck under speech: music sits roughly 18-24 dB below the voice while talking, may rise in clear pauses and at the end.
- Use sidechain ducking or keyframed volume driven by speech ranges from `captions.json`.
- Start with the hook (or a fraction of a second before) and resolve or fade out by the end; do not let it cut off abruptly.
- Avoid vocals in the bed under speech.

## Sound effects

Allowed, sparingly:
- `whoosh` on B-roll entries or large transitions
- `pop`/`tick` on visual-insert entrances
- `hit` on the hook's strong punch-in

Rules:
1. At most one SFX every ~3 s on average; skip SFX on most plain jump cuts.
2. SFX must never mask a word - place them in gaps or under non-critical syllables, at least 8-12 dB below the voice peak.
3. Keep a consistent SFX palette across the clip.
4. No novelty sounds (laugh tracks, airhorns) unless the user asks for that style.
5. If the user asks for a sound on every line that appears in a visual insert (list/diagram rows), that request overrides rule 1. Generate the cues from `visual-insert-plan.json` row `appear_s` times so sound and graphic can never drift apart. Use one sound for the card entrance (and a negative/cross row) and a lighter, brighter sound for each following positive row, so a new line reads differently from a new card.

### Choosing and checking SFX without listening

- Profile candidates first: audible length, attack time, spectral centroid, and the 5 ms RMS envelope. A file that is one 2-5 ms click followed by a quiet tail (high peak, very low RMS) disappears under speech even at a "correct" peak level - pick sounds with 50-150 ms of body.
- Prefer energy above ~5 kHz (bright pops/ticks) or below ~600 Hz (soft hits/whooshes); avoid SFX centered in 1-4 kHz, where they mask consonants.
- Peak-normalize each SFX to a target and delay it so its peak lands on the cue (`adelay = cue - time_of_peak_in_file`).
- Keep the voice and an SFX-only stem as separate files. If the final mix has a limiter, enable its latency compensation (`alimiter ... latency=1`), otherwise mix - voice comparisons are skewed by the lookahead delay.
- Per cue, measure from the stems: (a) SFX peak vs the local voice peak - must be at least 8 dB under; (b) SFX vs voice above 4 kHz averaged over the frames where the SFX is actually sounding - aim for >= 0 dB so it is audible. Adjust single cues (e.g. +4 dB on a cue that lands on a loud syllable, -1 dB on one that is too close) instead of changing all of them.
- Wide-window peak comparisons and mean-volume checks are misleading for short clicks; use the sounding-frames measurement.
- Confirm no word is lost: transcribe +/-1 s around each cue from the voice-only and the mixed audio and compare.
- When only the audio changes, re-mux it onto the existing video stream (`-c:v copy`) instead of re-rendering the picture.

## Mix targets

- Final loudness belongs to `reel-export-qc` (about -14 LUFS integrated, about -1 dBTP), but mix so that only a small final gain is needed.
- Check that the voice remains intelligible on a phone speaker: no music energy masking 1-4 kHz under speech.

## Workflow

1. Measure the voice: loudness, noise floor, clipping.
2. Plan music (track, in/out, ducking curve) and SFX events from the timeline artifacts.
3. Build the mix with FFmpeg (`sidechaincompress`, `volume` with `enable`/expressions, `adelay`, `amix`) or another deterministic tool.
4. Render `.video-edit/audio/mix.wav` - 48 kHz, stereo, exactly the length of the rough cut.
5. Listen-check or measure: speech ranges stay dominant, no SFX lands on a word.
6. Save `.video-edit/sound-plan.json`. `reel-motion` muxes `mix.wav` instead of the raw voice.

## Output schema

```json
{
  "voice": {
    "chain": "",
    "measured_lufs": null
  },
  "music": {
    "status": "ready|placeholder|none",
    "asset_path": null,
    "source": "",
    "license_note": "",
    "timeline_start_s": 0.0,
    "timeline_end_s": 0.0,
    "bed_level_db_under_voice": 20,
    "ducking": "sidechain|keyframed",
    "fade_in_s": 0.0,
    "fade_out_s": 0.0
  },
  "sfx": [
    {
      "timeline_s": 0.0,
      "type": "whoosh|pop|tick|hit",
      "asset_path": null,
      "gain_db": 0.0,
      "linked_to": "broll|visual_insert|zoom|cut",
      "status": "ready|placeholder"
    }
  ],
  "mix_path": ".video-edit/audio/mix.wav",
  "warnings": []
}
```

## Failure handling

- No approved music or SFX available: deliver the cleaned voice as `mix.wav`, set `music.status` to `placeholder` or `none`, and say so.
- If ducking still masks speech, lower the bed rather than raising the voice into the limiter.
- If the voice itself is noisy or clipped, report it; do not hide it under music.

## Completion criteria

`mix.wav` exists on the edited timeline, the voice is clearly dominant everywhere it speaks, every music/SFX file has a known source, and `sound-plan.json` describes exactly what was mixed.
