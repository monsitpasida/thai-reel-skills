import difflib, json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

# Transcribe the audio under each caption on its own and compare it with the caption text.
# A caption whose window holds the wrong words (too early / too late) scores low.
wav_path, captions_path = sys.argv[1], sys.argv[2]
caps = json.load(open(captions_path))["items"]

w = wave.open(wav_path)
sr = w.getframerate()
audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

# ASR spells some words differently from the captions; fold them together before comparing.
FOLD = [("ความรับ", "ความลับ"), ("มือ", "มื้อ"), ("เมือ", "มื้อ"), ("รถ", "ลด"), ("รด", "ลด"),
        ("ควบคุณ", "ควบคุม"), ("กลุม", "ควบคุม"), ("เป้าใหม่", "เป้าหมาย"), ("ละค่ะ", "แหละค่ะ")]

def norm(s):
    s = "".join(s.split()).lower()
    for a, b in FOLD:
        s = s.replace(a, b)
    for brand in ("bodykey", "บอดีคีย์", "บอดิคี", "บอดี้คีย์", "บริคี", "bodiki", "บอดีคี"):
        s = s.replace(brand, "B")
    return s

model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
scores = []
for c in caps:
    clip = audio[int(c["start_s"] * sr):int(c["end_s"] * sr)]
    segs, _ = model.transcribe(clip, language="th", beam_size=5, condition_on_previous_text=False,
                               without_timestamps=True)
    heard = "".join(s.text for s in segs)
    r = difflib.SequenceMatcher(None, norm(c["text"]), norm(heard)).ratio()
    scores.append(r)
    flag = "  <-- off" if r < 0.75 else ""
    print(f"{c['start_s']:6.2f}-{c['end_s']:6.2f}  {r:.2f}  cap: {c['text']}  | heard: {heard.strip()}{flag}", flush=True)

print(f"\nmean {np.mean(scores):.3f}  min {min(scores):.2f}  below 0.75: {sum(s < 0.75 for s in scores)}/{len(scores)}")
