import json, sys

# Keep pass-1 segments that end before the cutover, replace the rest with the VAD re-pass.
main_path, repass_path, cutover = sys.argv[1], sys.argv[2], float(sys.argv[3])
main = json.load(open(main_path))
repass = json.load(open(repass_path))

kept = [s for s in main["segments"] if s["end_s"] <= cutover]
main["segments"] = kept + repass
main["engine"] += f"; {cutover}s-end re-transcribed with VAD"
main["uncertain_ranges"] = [
    {"start_s": 97.7, "end_s": 100.0, "reason": "pass-1 garbled, re-pass starts mid-sentence at 100 s"},
    {"start_s": 129.34, "end_s": 140.34, "reason": "VAD re-pass skipped; pass-1 garbled (retake of 125.6 line)"},
]
main["notes"] = [
    "ASR homophone misspellings present (literal recognizer output kept): มือ=มื้อ, รถ=ลด, ความรับ=ความลับ, ควบคุณ=ควบคุม, บริคี/บอดีคีย์/Body Key=BodyKey.",
    "Speaker records multiple retakes of the BodyKey benefit lines (25-100 s) and the CTA (151-170 s).",
]
json.dump(main, open(main_path, "w"), ensure_ascii=False, indent=2)
open(main_path.replace(".json", ".txt"), "w").write(
    "\n".join(f"[{s['start_s']:7.2f} - {s['end_s']:7.2f}] {s['text']}" for s in main["segments"]) + "\n"
)
print(len(main["segments"]), "segments")
