import json, sys

# Turn captions.json + motion-plan subtitle_style into an ASS file for libass.
captions_path, motion_path, out_ass, duration = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
caps = json.load(open(captions_path))["items"]
st = json.load(open(motion_path))["subtitle_style"]

def bgr(hex_rgb):
    h = hex_rgb.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()

WHITE, HL = bgr(st["color"]), bgr(st["highlight_color"])

def ts(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"

def styled(line, highlights):
    # Highlight the longest keywords first so shorter ones inside them are not double-wrapped.
    spans = []
    for h in sorted({h["text"] for h in highlights}, key=len, reverse=True):
        i = line.find(h)
        while i != -1:
            if not any(a < i + len(h) and i < b for a, b in spans):
                spans.append((i, i + len(h)))
            i = line.find(h, i + 1)
    out, pos = "", 0
    for a, b in sorted(spans):
        out += line[pos:a] + "{\\c" + HL + "&}" + line[a:b] + "{\\c" + WHITE + "&}"
        pos = b
    return out + line[pos:]

header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st['font']},{st['size_px']},{WHITE},{WHITE},&H00000000,&H80000000,{-1 if st['weight'] == 'bold' else 0},0,0,0,100,100,0,0,1,{st['outline_px']},{st['shadow_px']},2,{st['side_margin_px']},{st['side_margin_px']},{st['bottom_margin_px']},222

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

POP = "{\\fscx92\\fscy92\\t(0,100,\\fscx100\\fscy100)}"
# Thai marks that combine with the previous base character - never start a colour run on one.
COMBINING = set("ัิีึืฺุู็่้๊๋์ํ๎")

def keyword_mask(text, highlights):
    mask = [False] * len(text)
    for h in {h["text"] for h in highlights}:
        i = text.find(h)
        while i != -1:
            mask[i:i + len(h)] = [True] * len(h)
            i = text.find(h, i + 1)
    return mask

def word_index(text, words):
    # display-char -> word number (spaces join the word before them)
    idx, wi, used = [], 0, 0
    for ch in text:
        if ch != " " and used == len(words[wi]["text"]) and wi + 1 < len(words):
            wi, used = wi + 1, 0
        idx.append(wi)
        if ch != " ":
            used += 1
    return idx

def word_state_text(text, words, active, kw):
    # Active word: dark text on a thick accent outline (a highlighter "pill"); outline width does
    # not change glyph advance, so the centred line never shifts as the highlight moves.
    widx = word_index(text, words)
    tags = []
    for i in range(len(text)):
        w = widx[i]
        if active is not None and w == active and text[i] != " ":
            tags.append("\\c" + PILL_TEXT + "&\\3c" + ACTIVE + "&\\bord" + str(st["pill_border_px"]) + "\\shad0")
        else:
            spoken_ = active is None or w < active
            col = UPCOMING if not spoken_ and (active is None or w > active) else (SPOKEN_KW if kw[i] else WHITE)
            tags.append("\\c" + col + "&\\3c&H00000000&\\bord" + str(st["outline_px"]) + "\\shad" + str(st["shadow_px"]))
    for i in range(1, len(text)):  # keep combining marks in their base character's run
        if text[i] in COMBINING:
            tags[i] = tags[i - 1]
    out, cur = "", None
    for ch, tag in zip(text, tags):
        if tag != cur:
            out += "{" + tag + "}"
            cur = tag
        out += ch
    return out

mode = st.get("mode", "keyword")
if mode == "word_highlight":
    ACTIVE, UPCOMING, PILL_TEXT = bgr(st["active_color"]), bgr(st["upcoming_color"]), bgr(st["pill_text_color"])
    # null spoken_keyword_color = keywords go back to plain text once spoken (one accent on screen)
    SPOKEN_KW = bgr(st["spoken_keyword_color"]) if st.get("spoken_keyword_color") else WHITE
    TAIL = st.get("pill_tail_s", 0.1)  # pill stays this long after the word's last sound

lines = []
for c in caps:
    end = min(c["end_s"], duration)
    if mode == "word_highlight" and c.get("words"):
        text, words = c["lines"][0], c["words"]
        kw = keyword_mask(text, c["highlights"])
        steps = []  # (start, end, active word index or None)
        for k, w in enumerate(words):
            a = c["start_s"] if k == 0 else w["start_s"]
            nxt = end if k == len(words) - 1 else min(words[k + 1]["start_s"], end)
            off = min(nxt, w.get("spoken_end_s", nxt) + TAIL)
            steps.append((a, off, k))
            if nxt - off > 0.02:
                steps.append((off, nxt, None))  # pause or hold: no word lit
        for i, (a, b, k) in enumerate(steps):
            if b - a <= 0.005:
                continue
            lines.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{POP if i == 0 else ''}"
                         f"{word_state_text(text, words, k, kw)}")
        continue
    text = "\\N".join(styled(l, c["highlights"]) for l in c["lines"])
    lines.append(f"Dialogue: 0,{ts(c['start_s'])},{ts(end)},Cap,,0,0,0,,{POP}{text}")

open(out_ass, "w").write(header + "\n".join(lines) + "\n")
print(f"{len(lines)} events")
