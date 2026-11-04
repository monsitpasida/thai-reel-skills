import json, sys, time
from faster_whisper import WhisperModel

audio, src, out_json, out_txt, model_name = sys.argv[1:6]

t0 = time.time()
model = WhisperModel(model_name, device="cpu", compute_type="int8")
print(f"model loaded in {time.time()-t0:.1f}s", flush=True)

segments, info = model.transcribe(
    audio,
    language="th",
    word_timestamps=True,
    vad_filter=False,
    beam_size=5,
    condition_on_previous_text=False,
)

out = {
    "language": info.language,
    "source_path": src,
    "duration_s": round(info.duration, 3),
    "engine": f"faster-whisper {model_name} int8 cpu",
    "segments": [],
    "uncertain_ranges": [],
}
lines = []
for s in segments:
    words = [
        {"start_s": round(w.start, 3), "end_s": round(w.end, 3), "text": w.word, "confidence": round(w.probability, 3)}
        for w in (s.words or [])
    ]
    out["segments"].append({"start_s": round(s.start, 3), "end_s": round(s.end, 3), "text": s.text.strip(), "words": words})
    low = [w for w in words if w["confidence"] < 0.4]
    if words and len(low) / len(words) > 0.3:
        out["uncertain_ranges"].append({"start_s": round(s.start, 3), "end_s": round(s.end, 3), "reason": "low word confidence"})
    lines.append(f"[{s.start:7.2f} - {s.end:7.2f}] {s.text.strip()}")
    print(lines[-1], flush=True)

json.dump(out, open(out_json, "w"), ensure_ascii=False, indent=2)
open(out_txt, "w").write("\n".join(lines) + "\n")
print(f"done in {time.time()-t0:.1f}s", flush=True)
