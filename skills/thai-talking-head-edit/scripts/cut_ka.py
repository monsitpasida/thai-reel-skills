import json, re, sys

# Remove every ค่ะ / คะ / นะคะ (and ครับ / นะครับ for male speakers) from the rough cut (user, 2026-11-02).
# Reads the CTC character timings that force_align.py wrote for the CURRENT rough cut, finds the
# particles, and rewrites edit-plan.json with those spans cut out of the source segments. A ~0.18 s
# pause is kept before the next word so the speech does not sound rushed.
# Usage: cut_ka.py captions-chars.json edit-plan.json out-edit-plan.json
# Afterwards: re-render the rough cut, check it with ctc_peek.py (no stray "ค", the word before
# keeps its vowel - e.g. สี่ must not decode as สิ), then rewrite caption-chunks without the particles
# and run force_align.py again.
chars_path, plan_path, out_path = sys.argv[1:4]
PREV_PAD, LEAD, TAIL, KEEP_PAUSE, MIN_SEG = 0.06, 0.04, 0.08, 0.18, 0.12

chars = json.load(open(chars_path))
plan = json.load(open(plan_path))
seq = "".join(c["char"] for c in chars)

cuts = []
for m in re.finditer("นะครับ|ครับ|นะคะ|ค่ะ|คะ", seq):
    a, b = m.start(), m.end()
    nxt = chars[b] if b < len(chars) else None
    start, end = chars[a]["start_s"], chars[b - 1]["end_s"]
    prev_end = chars[a - 1]["end_s"] if a else 0.0
    ca = max(prev_end + PREV_PAD, start - LEAD)
    cb = end + TAIL if nxt is None else min(max(end + TAIL, nxt["start_s"] - KEEP_PAUSE), nxt["start_s"] - 0.06)
    cuts.append((ca, cb))

segs, t = [], 0.0
for s in plan["segments"]:
    d = s["source_end_s"] - s["source_start_s"]
    ra, rb = t, t + d
    t += d
    keep = [(ra, rb)]
    for ca, cb in cuts:
        nk = []
        for x, y in keep:
            if cb <= x or ca >= y:
                nk.append((x, y))
                continue
            if ca > x:
                nk.append((x, ca))
            if cb < y:
                nk.append((cb, y))
        keep = nk
    for x, y in keep:
        if y - x < MIN_SEG:
            continue
        n = dict(s)
        n["source_start_s"] = n["planned_start_s"] = round(s["source_start_s"] + (x - ra), 3)
        n["source_end_s"] = n["planned_end_s"] = round(s["source_start_s"] + (y - ra), 3)
        segs.append(n)

plan["segments"] = segs
plan["target_duration_s"] = round(sum(s["source_end_s"] - s["source_start_s"] for s in segs), 2)
plan["notes"] = (plan.get("notes", "") + " ค่ะ/นะคะ removed by cut_ka.py.").strip()
json.dump(plan, open(out_path, "w"), ensure_ascii=False, indent=2)
print(f"{len(cuts)} particles cut, {len(segs)} segments, {plan['target_duration_s']} s")
