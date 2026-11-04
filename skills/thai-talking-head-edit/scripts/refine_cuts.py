import json, sys, wave
import numpy as np

# Snap each segment edge in edit-plan.json to the quietest 10 ms frame within +/-RADIUS of the
# planned time (dense speech has few real pauses), then pad slightly outward so no consonant clips.
plan_path, wav_path = sys.argv[1], sys.argv[2]
RADIUS, PAD = 0.12, 0.03

w = wave.open(wav_path)
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = sr // 100
n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)

QUIET, REACH_END, REACH_START = -42.0, 0.6, 0.4

def dip(t):
    a, b = max(0, int((t - RADIUS) * 100)), min(n - 1, int((t + RADIUS) * 100))
    i = a + int(np.argmin(db[a:b + 1]))
    return i / 100, db[i]

def edge(t, forward):
    # nearest dip; if it is not actually quiet, walk outward until speech has really stopped
    tt, d = dip(t)
    if d <= QUIET:
        return tt, d
    i, step = int(tt * 100), (1 if forward else -1)
    limit = int((t + (REACH_END if forward else -REACH_START)) * 100)
    while 0 < i < n - 1 and (i <= limit if forward else i >= limit):
        if db[i] <= QUIET:
            return i / 100, db[i]
        i += step
    return tt, d  # no quiet point in reach: keep the dip and flag it

plan = json.load(open(plan_path))
for s in plan["segments"]:
    t0, d0 = edge(s["planned_start_s"], forward=False)
    t1, d1 = edge(s["planned_end_s"], forward=True)
    s["source_start_s"] = round(max(0.0, t0 - PAD), 3)
    s["source_end_s"] = round(t1 + 0.01 + PAD, 3)
    s["edge_levels_db"] = [round(float(d0), 1), round(float(d1), 1)]
    print(f"{s['role']:5} {s['planned_start_s']:7.2f}->{s['source_start_s']:7.2f} ({d0:5.1f} dB)   "
          f"{s['planned_end_s']:7.2f}->{s['source_end_s']:7.2f} ({d1:5.1f} dB)  {s['text'][:30]}")
plan["target_duration_s"] = round(sum(s["source_end_s"] - s["source_start_s"] for s in plan["segments"]), 2)
json.dump(plan, open(plan_path, "w"), ensure_ascii=False, indent=2)
print("total", plan["target_duration_s"], "s")
