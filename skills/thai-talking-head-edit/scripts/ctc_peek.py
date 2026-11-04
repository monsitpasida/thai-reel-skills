import sys, wave
import numpy as np, torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

# Greedy wav2vec2 decode of source spans, printed as words with start times. Whisper smooths over
# restarts and repeated words; this shows what is really said inside a chosen take.
# Usage: ctc_peek.py audio16k.wav start-end [start-end ...]
M = "airesearch/wav2vec2-large-xlsr-53-th"
proc, model = Wav2Vec2Processor.from_pretrained(M), Wav2Vec2ForCTC.from_pretrained(M).eval()
w = wave.open(sys.argv[1]); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
for span in sys.argv[2:]:
    a, b = (float(v) for v in span.split("-"))
    seg = x[int(a * sr):int(b * sr)]
    with torch.inference_mode():
        ids = model(proc(seg, sampling_rate=sr, return_tensors="pt").input_values).logits.argmax(-1)[0].tolist()
    step = len(seg) / sr / len(ids)
    words, cur, t0, prev = [], "", None, None
    for i, t in enumerate(ids):
        if t != prev and t != proc.tokenizer.pad_token_id:
            ch = proc.tokenizer.convert_ids_to_tokens(t)
            if ch == "|":
                if cur: words.append(f"{cur}@{t0:.2f}"); cur = ""
            else:
                if not cur: t0 = a + i * step
                cur += ch
        prev = t
    if cur: words.append(f"{cur}@{t0:.2f}")
    print(f"[{a:.2f}-{b:.2f}] " + " ".join(words), flush=True)
