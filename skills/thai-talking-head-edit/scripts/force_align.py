import json, re, sys, wave
import numpy as np
import torch
from torchaudio.functional import forced_align, merge_tokens
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

from pythainlp.tokenize import word_tokenize

# v3 caption timing: CTC forced alignment of the known caption text against the edited audio
# with a Thai wav2vec2 model. Each caption starts where its first character is spoken.
# v4 adds per-word times (PyThaiNLP segmentation) for word-by-word highlighting.
chunks_path, wav_path, out_json, out_srt = sys.argv[1:5]
MODEL = "airesearch/wav2vec2-large-xlsr-53-th"
LEAD, HOLD = 0.04, 0.3
MIN_WORD_S = 0.15  # shorter highlight steps flicker; merge them into the next word

# newmm mis-segments a few phrases in this script; fix them before alignment.
SEG_FIX = {("เรื่อ", "งอด"): ["เรื่อง", "อด"]}

def words_of(text):
    toks = word_tokenize(text, engine="newmm", keep_whitespace=False)
    out = []
    for t in toks:
        if t == "ๆ" and out:
            out[-1] += t
        else:
            out.append(t)
    i, fixed = 0, []
    while i < len(out):
        pair = tuple(out[i:i + 2])
        if pair in SEG_FIX:
            fixed += SEG_FIX[pair]
            i += 2
        else:
            fixed.append(out[i])
            i += 1
    assert "".join(fixed) == text.replace(" ", ""), (text, fixed)
    return fixed

proc = Wav2Vec2Processor.from_pretrained(MODEL)
model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
vocab = proc.tokenizer.get_vocab()
blank = vocab["[PAD]"]

# Spoken form for the aligner only - what is displayed stays as written.
SPOKEN = [("BodyKey", "บอดี้คีย์"), ("Go", "โก"), ("Vibrant", "ไวแบรนท์"), ("Waterproof", "วอเตอร์พรูฟ"), ("Length", "เลงธ์"),
          ("Serum", "เซรั่ม"), ("Mascara", "มาสคาร่า"), ("Carbon", "คาร์บอน"), ("Black", "แบล็ค"), ("10", "สิบ")]

def spoken(text):
    for a, b in SPOKEN:
        text = text.replace(a, b)
    if text.endswith("ๆ"):  # applied per word: มากๆ -> มากมาก
        text = text[:-1] * 2
    return "".join(ch for ch in text if ch in vocab and ch != "|")

w = wave.open(wav_path)
sr = w.getframerate()
assert sr == 16000 and w.getnchannels() == 1
audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
inputs = proc(audio, sampling_rate=sr, return_tensors="pt")
with torch.inference_mode():
    emissions = torch.log_softmax(model(inputs.input_values).logits, dim=-1)
stride = len(audio) / sr / emissions.shape[1]

caps = [(c[0], c[1]) for seg in json.load(open(chunks_path)) for c in seg]
cap_words = [words_of(text) for text, _ in caps]
targets, owner, word_owner = [], [], []
for k, words in enumerate(cap_words):
    for wi, word in enumerate(words):
        for ch in spoken(word):
            targets.append(vocab[ch])
            owner.append(k)
            word_owner.append((k, wi))

ali, scores = forced_align(emissions, torch.tensor([targets], dtype=torch.int32), blank=blank)
spans = merge_tokens(ali[0], scores[0].exp(), blank=blank)
assert len(spans) == len(targets), (len(spans), len(targets))

chars = [{"caption": k, "char": proc.tokenizer.convert_ids_to_tokens(t),
           "start_s": round(s.start * stride, 3), "end_s": round(s.end * stride, 3)}
          for s, k, t in zip(spans, owner, targets)]
json.dump(chars, open(out_json.replace(".json", "-chars.json"), "w"), ensure_ascii=False)

first, last, conf = {}, {}, {}
for span, k in zip(spans, owner):
    first.setdefault(k, span.start * stride)
    last[k] = span.end * stride
    conf.setdefault(k, []).append(span.score)

wstart, wend = {}, {}
for span, kw in zip(spans, word_owner):
    wstart.setdefault(kw, span.start * stride)
    wend[kw] = span.end * stride

def timed_words(k):
    # end_s = next word's start (slot length, used for the merge rule); spoken_end_s = last aligned
    # character, so the renderer can switch the highlight off when the word is finished.
    ws, carry = [], ""
    for i, w in enumerate(cap_words[k]):
        if (k, i) not in wstart:  # no alignable characters (e.g. punctuation): join the next word
            carry += w
            continue
        ws.append({"text": carry + w, "start_s": wstart[(k, i)], "end_s": wend[(k, i)], "spoken_end_s": wend[(k, i)]})
        carry = ""
    if carry and ws:
        ws[-1]["text"] += carry
    for a, b in zip(ws, ws[1:]):
        a["end_s"] = b["start_s"]

    def join(a, b):
        return {"text": a["text"] + b["text"], "start_s": a["start_s"], "end_s": b["end_s"], "spoken_end_s": b["spoken_end_s"]}

    merged = []
    for w in ws:
        if merged and merged[-1]["end_s"] - merged[-1]["start_s"] < MIN_WORD_S:
            merged[-1] = join(merged[-1], w)
        else:
            merged.append(w)
    if len(merged) > 1 and merged[-1]["end_s"] - merged[-1]["start_s"] < MIN_WORD_S:
        last_w = merged.pop()
        merged[-1] = join(merged[-1], last_w)
    return [{k2: (round(v, 3) if k2 != "text" else v) for k2, v in w.items()} for w in merged]

items = []
for k, (text, hl) in enumerate(caps):
    items.append({"start_s": round(max(0.0, first[k] - LEAD), 3), "speech_end_s": round(last[k], 3),
                  "text": text, "lines": [text], "align_score": round(float(np.mean(conf[k])), 3),
                  "words": timed_words(k),
                  "highlights": [{"text": h, "type": "keyword"} for h in hl]})
items[0]["start_s"] = 0.0  # hook text is on screen from the first frame
for a, b in zip(items, items[1:]):
    a["end_s"] = round(min(b["start_s"], a["speech_end_s"] + HOLD), 3)
items[-1]["end_s"] = round(items[-1]["speech_end_s"] + HOLD, 3)
for a, b in zip(items, items[1:]):
    assert a["start_s"] < a["end_s"] <= b["start_s"] + 1e-6, (a, b)

json.dump({"language": "th", "timeline": "rough-cut", "timing": f"v3 CTC forced alignment ({MODEL})", "items": items},
          open(out_json, "w"), ensure_ascii=False, indent=2)

def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"

with open(out_srt, "w") as f:
    for i, it in enumerate(items, 1):
        f.write(f"{i}\n{ts(it['start_s'])} --> {ts(it['end_s'])}\n" + "\n".join(it["lines"]) + "\n\n")

print(f"frame stride {stride * 1000:.1f} ms, {len(items)} captions")
for it in items:
    print(f"{it['start_s']:6.2f}-{it['end_s']:6.2f} (speech ends {it['speech_end_s']:6.2f}, conf {it['align_score']:.2f})  {it['text']}")
