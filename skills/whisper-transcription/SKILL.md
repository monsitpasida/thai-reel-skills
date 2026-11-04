---
name: whisper-transcription
description: Transcribe speech in video or audio to text, SRT/VTT subtitles, or word-level timestamps locally with OpenAI Whisper (Thai and 90+ languages). Use for subtitles, transcripts, finding where something was said, or transcript-based cutting.
---

# Whisper transcription

## Pick an engine (check what is installed first)
1. `whisper-cli` (whisper.cpp) – fastest on Apple Silicon. `brew install whisper-cpp`; model: download a ggml file, e.g. `curl -L -o ~/models/ggml-large-v3-turbo.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin`
2. `mlx_whisper` – fast on Apple Silicon. `pip install mlx-whisper`
3. `whisper` (openai-whisper, Python) – simplest. `pip install -U openai-whisper` (needs ffmpeg)
4. `faster-whisper` (Python lib) – best for word timestamps from code.
If none is installed, ask before installing; suggest whisper.cpp on a Mac.

## Model choice
- Thai or mixed Thai/English: `large-v3` or `large-v3-turbo` (small models are poor at Thai).
- English only and speed matters: `small.en` / `medium.en`.
Always pass the language when known (`--language th`) – auto-detect wastes time and can pick the wrong one.

## Prepare audio
`ffmpeg -i input.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le audio.wav`

## Commands
whisper.cpp: `whisper-cli -m ~/models/ggml-large-v3-turbo.bin -f audio.wav -l th -osrt -ovtt -otxt -of out`
  word-level: add `-ml 1 -sow` (one word per segment) or `-oj` for full JSON.
openai-whisper: `whisper audio.wav --model large-v3 --language th --output_format all --word_timestamps True --output_dir out`
mlx: `mlx_whisper audio.wav --model mlx-community/whisper-large-v3-turbo --language th --output-format srt`
Translate speech to English: openai-whisper `--task translate`; whisper.cpp `-tr`.

## After transcribing
- Read the transcript and fix obvious mishearings of names/brands before burning subtitles.
- Subtitle lines: max ~42 Latin chars or ~30 Thai chars per line, 2 lines, 1–6 s each. Re-split long segments.
- Thai has no spaces between words; when re-wrapping, break at existing spaces or use `pythainlp` word_tokenize.
- Burn subtitles with FFmpeg (see ffmpeg-video-editing skill) using a Thai-capable font.

## Transcript-based editing
1. Get word/segment timestamps (JSON).
2. Show the user the numbered transcript; let them say what to keep/remove (fillers, retakes, dead air).
3. Turn kept ranges into an FFmpeg trim/concat filter, pad each cut by ~0.05–0.1 s so words are not clipped.
4. Render, then re-transcribe or spot-check the joins.

## Troubleshooting
- Repeated/hallucinated lines in silence: use VAD (`--vad` in whisper.cpp with a VAD model, or faster-whisper `vad_filter=True`), or cut silence first.
- Timing drifts: make sure the audio was extracted from the same file being edited.
- Cloud alternative: ElevenLabs speech-to-text (Scribe) when local speed is too slow.
