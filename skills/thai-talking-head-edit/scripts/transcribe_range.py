import json, sys, time
from faster_whisper import WhisperModel

# Transcribe a pre-cut audio clip and shift timestamps back to source time.
audio, offset, out_json, model_name = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]

t0 = time.time()
model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, info = model.transcribe(
    audio,
    language="th",
    word_timestamps=True,
    vad_filter=True,
    vad_parameters={"min_silence_duration_ms": 400},
    beam_size=5,
    temperature=0.0,
    condition_on_previous_text=False,
    no_repeat_ngram_size=0,
)

out = []
for s in segments:
    words = [
        {"start_s": round(w.start + offset, 3), "end_s": round(w.end + offset, 3), "text": w.word, "confidence": round(w.probability, 3)}
        for w in (s.words or [])
    ]
    out.append({"start_s": round(s.start + offset, 3), "end_s": round(s.end + offset, 3), "text": s.text.strip(), "words": words})
    conf = sum(w["confidence"] for w in words) / max(len(words), 1)
    print(f"[{s.start + offset:7.2f} - {s.end + offset:7.2f}] ({conf:.2f}) {s.text.strip()}", flush=True)

json.dump(out, open(out_json, "w"), ensure_ascii=False, indent=2)
print(f"done in {time.time()-t0:.1f}s", flush=True)
