import difflib, json, sys, wave
import numpy as np

# v2 caption timing: map each caption's characters onto the ASR token stream with a
# character-level diff (instead of proportional spreading), then snap every boundary
# to the quietest 10 ms frame nearby and every phrase start to the real speech onset.
words_path, chunks_path, wav_path, out_json, out_srt = sys.argv[1:6]
asr = json.load(open(words_path))
CHUNKS = json.load(open(chunks_path))
assert len(CHUNKS) == len(asr)

w = wave.open(wav_path)
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
HOP = 0.01
n = len(x) // int(sr * HOP)
env = np.array([np.sqrt(np.mean(x[i * int(sr * HOP):(i + 1) * int(sr * HOP)] ** 2)) + 1e-9 for i in range(n)])
db = 20 * np.log10(env)
SPEECH_DB = np.percentile(db, 30) + 12  # loud enough to be voice, not room tone

def frame(t):
    return int(min(max(t / HOP, 0), n - 1))

def snap_dip(t, radius=0.15):
    a, b = frame(t - radius), frame(t + radius)
    i = a + int(np.argmin(db[a:b + 1]))
    # only move if the dip is real, i.e. clearly quieter than the boundary we had
    return i * HOP if db[i] < db[frame(t)] - 3 else t

def onset(t, back=0.25, fwd=0.25):
    a, b = frame(t - back), frame(t + fwd)
    for i in range(a, b + 1):
        if db[i] > SPEECH_DB:
            return max(0.0, i * HOP - 0.04)  # tiny lead so text is up as the word starts
    return t

def offset(t, back=0.3, fwd=0.3):
    a, b = frame(t - back), frame(t + fwd)
    for i in range(b, a - 1, -1):
        if db[i] > SPEECH_DB:
            return (i + 1) * HOP
    return t

items = []
for seg, chunks in zip(asr, CHUNKS):
    toks = [t for t in seg["words"] if t["text"].strip()]
    asr_chars, owner = "", []
    for k, t in enumerate(toks):
        s = "".join(t["text"].split())
        asr_chars += s
        owner += [k] * len(s)
    texts = ["".join(c[0].split()) for c in chunks]
    cap_chars = "".join(texts)

    # corr index -> asr index via the diff opcodes
    m = [0] * (len(cap_chars) + 1)
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, cap_chars, asr_chars, autojunk=False).get_opcodes():
        for i in range(i1, i2 + 1):
            frac = (i - i1) / max(i2 - i1, 1)
            m[i] = min(int(round(j1 + frac * (j2 - j1))), len(asr_chars) - 1)

    def t_at(ci):
        return toks[owner[m[ci]]]["start_s"]

    seg_start = onset(seg["start_s"])
    seg_end = offset(seg["end_s"])
    bounds, ci = [seg_start], 0
    for txt in texts[:-1]:
        ci += len(txt)
        bounds.append(snap_dip(t_at(ci)))
    bounds.append(seg_end)
    for i in range(1, len(bounds) - 1):  # keep order and a minimum 0.35 s per caption
        bounds[i] = min(max(bounds[i], bounds[i - 1] + 0.35), bounds[-1] - 0.35 * (len(bounds) - 1 - i))

    for i, (txt, hl) in enumerate(chunks):
        items.append({"start_s": round(bounds[i], 3), "end_s": round(bounds[i + 1], 3), "text": txt,
                      "lines": [txt], "highlights": [{"text": h, "type": "keyword"} for h in hl]})

# Hold through short pauses (max 0.3 s) but never overlap the next caption.
for a, b in zip(items, items[1:]):
    a["end_s"] = round(min(b["start_s"], a["end_s"] + 0.3), 3)
items[-1]["end_s"] = round(items[-1]["end_s"] + 0.3, 3)
for a, b in zip(items, items[1:]):
    assert a["start_s"] < a["end_s"] <= b["start_s"] + 1e-6, (a, b)

json.dump({"language": "th", "timeline": "rough-cut", "timing": "v2 diff-aligned + pause-snapped", "items": items},
          open(out_json, "w"), ensure_ascii=False, indent=2)

def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"

with open(out_srt, "w") as f:
    for i, it in enumerate(items, 1):
        f.write(f"{i}\n{ts(it['start_s'])} --> {ts(it['end_s'])}\n" + "\n".join(it["lines"]) + "\n\n")
print(f"{len(items)} captions, shortest {min(i['end_s'] - i['start_s'] for i in items):.2f}s")
