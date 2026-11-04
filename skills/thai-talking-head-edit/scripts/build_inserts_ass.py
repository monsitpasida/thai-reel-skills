import json, sys

# Render visual-insert-plan.json as an ASS overlay: a rounded card per insert, rows of
# vector icon + text that pop in on their spoken word. Placeholder items are skipped.
plan_path, out_ass, duration = sys.argv[1], sys.argv[2], float(sys.argv[3])
plan = json.load(open(plan_path))
st = plan["style"]
W, H = 1080, 1920

def bgr(hex_rgb, alpha=0.0):
    h = hex_rgb.lstrip("#")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper(), f"&H{int(round(alpha * 255)):02X}&"

def ts(t):
    cs = int(round(min(t, duration) * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"

def rounded_rect(w, h, r):
    return (f"m {r} 0 l {w - r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h - r} b {w} {h} {w} {h} {w - r} {h} "
            f"l {r} {h} b 0 {h} 0 {h} 0 {h - r} l 0 {r} b 0 0 0 0 {r} 0")

ICONS = {
    "check": "m 4 24 l 16 36 l 40 10 l 34 4 l 16 24 l 10 18",
    "cross": "m 6 0 l 22 16 l 38 0 l 44 6 l 28 22 l 44 38 l 38 44 l 22 28 l 6 44 l 0 38 l 16 22 l 0 6",
    "chat": "m 8 0 l 44 0 b 50 0 52 2 52 8 l 52 28 b 52 34 50 36 44 36 l 22 36 l 10 46 l 12 36 l 8 36 "
            "b 2 36 0 34 0 28 l 0 8 b 0 2 2 0 8 0",
}
ICON_COLOR = {"check": st["accent_color"], "cross": st["negative_color"], "chat": st["accent_color"]}
ICON_SCALE = st.get("icon_scale", 1.0)
ICONS = {k: " ".join(f"{float(t) * ICON_SCALE:g}" if t.lstrip("-").isdigit() else t for t in v.split())
         for k, v in ICONS.items()}

POP = "\\fscx90\\fscy90\\t(0,150,\\fscx100\\fscy100)"
bg_col, bg_alpha = bgr(st["background"], 1 - st["background_opacity"])
txt_col, _ = bgr(st["text_color"])
pad, row_h, radius = st["padding_px"], st["row_height_px"], st["corner_radius_px"]

def text_width(text, size):
    # measured with the real font so chips hug their text (needs Pillow: run with the venv python)
    from PIL import ImageFont
    font = ImageFont.truetype(st.get("font_file", "/System/Library/Fonts/SukhumvitSet.ttc"),
                              size, index=st.get("font_index", 0), layout_engine=ImageFont.Layout.BASIC)
    return font.getlength(text)

def chips(it):
    # one horizontal row of rounded chips (icon + text); each chip pops in on its own spoken word
    # and stays until the item ends. Used where there is no room for a tall card above the head.
    ch, gap, ipad, icon_w = st.get("chip_height_px", 104), st.get("chip_gap_px", 22), 30, 62
    fs = it.get("chip_font_px", st.get("chip_font_px", st["font_size_px"]))
    widths = [ipad * 2 + icon_w + text_width(r["text"], fs) for r in it["rows"]]
    # wrap onto extra lines (each centered, stacked downward) when a row would leave the safe width
    max_w, lines, cur = W - 80, [], []
    for i, wd in enumerate(widths):
        if cur and sum(widths[j] for j in cur) + gap * len(cur) + wd > max_w:
            lines.append(cur)
            cur = []
        cur.append(i)
    lines.append(cur)
    place = {}
    for li, line in enumerate(lines):
        total = sum(widths[j] for j in line) + gap * (len(line) - 1)
        assert total <= max_w, f"chip '{it['rows'][line[0]]['text']}' alone is {total:.0f}px - lower chip_font_px"
        x = it["position"]["x"] * W - total / 2
        for j in line:
            place[j] = (x, it["position"]["y"] * H + li * (ch + 14))
            x += widths[j] + gap
    end = it["timeline_end_s"]
    fade_out = 120 if it["animation_out"] == "fade" else 0
    out = []
    for j, (r, wd) in enumerate(zip(it["rows"], widths)):
        x, cy = place[j]
        a = r["appear_s"]
        icol, _ = bgr(ICON_COLOR[r["icon"]])
        dim = "\\alpha&H40&" if r["icon"] == "cross" else ""
        out.append(f"Dialogue: 1,{ts(a)},{ts(end)},Insert,,0,0,0,,{{\\an5\\pos({x + wd / 2:.0f},{cy:.0f})\\bord0\\shad0"
                   f"\\c{bg_col}\\1a{bg_alpha}{POP}\\fad(0,{fade_out})\\p1}}{rounded_rect(round(wd), ch, ch // 2)}{{\\p0}}")
        out.append(f"Dialogue: 2,{ts(a)},{ts(end)},Insert,,0,0,0,,{{\\an5\\pos({x + ipad + 26:.0f},{cy:.0f})\\bord0\\shad0"
                   f"\\c{icol}{POP}\\fad(0,{fade_out})\\p1}}{ICONS[r['icon']]}{{\\p0}}")
        out.append(f"Dialogue: 2,{ts(a)},{ts(end)},Insert,,0,0,0,,{{\\an4\\pos({x + ipad + icon_w:.0f},{cy:.0f})"
                   f"\\fs{fs}\\c{txt_col}{dim}{POP}\\fad(0,{fade_out})}}{r['text']}")
    return out

events = []
for it in plan["items"]:
    if it["status"] != "ready" or "rows" not in it:  # product cards are image overlays, not ASS
        continue
    if it.get("layout") == "chips":
        events += chips(it)
        continue
    w = it["size"]["width_px"]
    h = pad * 2 + row_h * len(it["rows"])
    cx, cy = it["position"]["x"] * W, it["position"]["y"] * H
    left, top = cx - w / 2, cy - h / 2
    start, end = it["timeline_start_s"], it["timeline_end_s"]
    fade_out = 120 if it["animation_out"] == "fade" else 0

    events.append(f"Dialogue: 1,{ts(start)},{ts(end)},Insert,,0,0,0,,"
                  f"{{\\an5\\pos({cx:.0f},{cy:.0f})\\bord0\\shad0\\c{bg_col}\\1a{bg_alpha}{POP}\\fad(0,{fade_out})\\p1}}"
                  f"{rounded_rect(w, h, radius)}{{\\p0}}")
    for i, row in enumerate(it["rows"]):
        ry = top + pad + row_h * i + row_h / 2
        icol, _ = bgr(ICON_COLOR[row["icon"]])
        fade_in = 0 if i == 0 else 100
        events.append(f"Dialogue: 2,{ts(row['appear_s'])},{ts(end)},Insert,,0,0,0,,"
                      f"{{\\an5\\pos({left + pad + 32:.0f},{ry:.0f})\\bord0\\shad0\\c{icol}{POP}\\fad({fade_in},{fade_out})\\p1}}"
                      f"{ICONS[row['icon']]}{{\\p0}}")
        dim = "\\alpha&H40&" if row["icon"] == "cross" else ""  # rejected option reads secondary
        events.append(f"Dialogue: 2,{ts(row['appear_s'])},{ts(end)},Insert,,0,0,0,,"
                      f"{{\\an4\\pos({left + pad + 92:.0f},{ry:.0f})\\c{txt_col}{dim}{POP}\\fad({fade_in},{fade_out})}}"
                      f"{row['text']}")

header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Insert,{st['font']},{st['font_size_px']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,{-1 if st['font_weight'] == 'bold' else 0},0,0,0,100,100,0,0,1,0,0,5,0,0,0,222

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(out_ass, "w").write(header + "\n".join(events) + "\n")
print(f"{len(events)} events from {sum(it['status'] == 'ready' for it in plan['items'])} inserts")
