import json, sys

# Map hand-chunked caption text (spoken words, corrected ASR spelling) onto the
# rough cut's ASR segments, timing each chunk by its character offset in the segment.
words_path, out_json, out_srt = sys.argv[1:4]
asr = json.load(open(words_path))

# One entry per ASR segment of the rough cut, in order: list of (chunk text, [highlight words]).
CHUNKS = [
    [("ความลับของคนที่กิน", ["ความลับ"]), ("BodyKey คู่กับโปรตีน", ["BodyKey", "โปรตีน"])],
    [("เป้าหมายไม่ใช่แค่", []), ("อยากผอมเร็วนะคะ", ["ผอมเร็ว"])],
    [("แต่เพราะเขารู้ว่า", []), ("เวลาควบคุมอาหาร", ["ควบคุมอาหาร"]), ("สิ่งสำคัญที่สุด", ["สิ่งสำคัญที่สุด"])],
    [("ไม่ใช่กินให้น้อยลง", ["น้อยลง"])],
    [("แต่ต้องกินให้พอ", ["กินให้พอ"]), ("และเลือกให้ถูก", ["เลือกให้ถูก"])],
    [("BodyKey ช่วยจัดการ", ["BodyKey"]), ("มื้ออาหารของเรา", []), ("ได้ง่ายขึ้น สะดวกขึ้น", ["ง่ายขึ้น", "สะดวกขึ้น"])],
    [("โดยเฉพาะช่วงที่เรารีบ", ["รีบ"]), ("ไม่มีเวลาเตรียมอาหาร", ["ไม่มีเวลา"])],
    [("ทำให้เราควบคุม", []), ("พลังงานอาหาร", ["พลังงานอาหาร"]), ("ในแต่ละมื้อได้ง่ายขึ้นค่ะ", ["ง่ายขึ้น"])],
    [("ส่วนโปรตีนนะคะ", ["โปรตีน"]), ("ก็เป็นสารอาหาร", []), ("สำคัญมากๆ", ["สำคัญมากๆ"]), ("ที่เราก็ต้องใช้นะคะ", [])],
    [("โดยเฉพาะช่วงที่เรา", []), ("ควบคุมน้ำหนัก", ["ควบคุมน้ำหนัก"]), ("แล้วก็ออกกำลังกาย", ["ออกกำลังกาย"])],
    [("เพราะฉะนั้นเวลากิน", []), ("BodyKey คู่กับโปรตีน", ["BodyKey", "โปรตีน"]), ("เป้าหมายไม่ใช่การอดอาหาร", ["อดอาหาร"])],
    [("แต่เป็นการเลือกกินให้เป็น", ["กินให้เป็น"]), ("แล้วก็กินให้ครบ", ["กินให้ครบ"])],
    [("นี่แหละค่ะ", []), ("ความลับของคนที่", ["ความลับ"]), ("ลดน้ำหนักได้ต่อเนื่อง", ["ต่อเนื่อง"])],
    [("ไม่ได้เก่งเรื่องอดนะคะ", ["อด"])],
    [("แต่เก่งเรื่องกินให้เป็น", ["กินให้เป็น"])],
    [("ใครนะคะที่กำลัง", []), ("ควบคุมน้ำหนักอยู่", ["ควบคุมน้ำหนัก"])],
    [("แต่ไม่รู้จะเริ่มยังไง", ["เริ่มยังไง"])],
    [("ลองทักมาคุยกันได้นะคะ", ["ทักมาคุยกัน"])],
]
assert len(CHUNKS) == len(asr), (len(CHUNKS), len(asr))

MAX_HOLD = 0.3  # how long a caption may linger into a pause
items = []
for seg, chunks in zip(asr, CHUNKS):
    toks = [w for w in seg["words"] if w["text"].strip()]
    cum, total = [], 0
    for w in toks:
        cum.append(total)
        total += len(w["text"].strip())
    text_total = sum(len(c.replace(" ", "")) for c, _ in chunks)

    def time_at(frac):
        target = frac * total
        for w, c in zip(toks, cum):
            if c >= target - 1e-6:
                return w["start_s"]
        return seg["end_s"]

    offset = 0
    starts = []
    for c, _ in chunks:
        starts.append(seg["start_s"] if offset == 0 else time_at(offset / text_total))
        offset += len(c.replace(" ", ""))
    for i, (c, hl) in enumerate(chunks):
        end = starts[i + 1] if i + 1 < len(chunks) else seg["end_s"]
        items.append({"start_s": round(starts[i], 3), "end_s": round(end, 3), "text": c, "lines": [c],
                      "highlights": [{"text": h, "type": "keyword"} for h in hl]})

# Let each caption hold briefly through a following pause, but never overlap the next one.
for a, b in zip(items, items[1:]):
    a["end_s"] = round(min(b["start_s"], a["end_s"] + MAX_HOLD), 3)
items[-1]["end_s"] = round(items[-1]["end_s"] + MAX_HOLD, 3)

# Merge flashes shorter than 0.45 s into the previous caption when both fit on two lines.
merged = []
for it in items:
    if merged and it["end_s"] - it["start_s"] < 0.45 and len(merged[-1]["lines"]) == 1:
        p = merged[-1]
        p["end_s"] = it["end_s"]
        p["text"] += " " + it["text"]
        p["lines"].append(it["text"])
        p["highlights"] += it["highlights"]
    else:
        merged.append(it)

for a, b in zip(merged, merged[1:]):
    assert a["start_s"] < a["end_s"] <= b["start_s"], (a, b)

json.dump({"language": "th", "timeline": "rough-cut", "items": merged}, open(out_json, "w"), ensure_ascii=False, indent=2)

def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"

with open(out_srt, "w") as f:
    for i, it in enumerate(merged, 1):
        f.write(f"{i}\n{ts(it['start_s'])} --> {ts(it['end_s'])}\n" + "\n".join(it["lines"]) + "\n\n")

short = min(it["end_s"] - it["start_s"] for it in merged)
print(f"{len(merged)} captions, shortest {short:.2f}s")
for it in merged:
    print(f"{it['start_s']:6.2f}-{it['end_s']:6.2f}  {' / '.join(it['lines'])}")
