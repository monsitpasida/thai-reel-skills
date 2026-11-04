import argparse, subprocess, tempfile, os

# Build a 1080x1920 Reel cover: a chosen video frame + the hook as a big Thai title in the caption
# style (white, thick black outline, one keyword as dark text on a yellow pill) + an optional
# product card. Text goes through libass (harfbuzz) because Pillow here has no raqm, so Thai
# tone marks would stack wrongly. Writes cover.png and cover.jpg.
ap = argparse.ArgumentParser()
ap.add_argument("frame")                      # still from the edited video (no captions burned in)
ap.add_argument("out")                        # output path without extension
ap.add_argument("--title", required=True)     # lines separated by "|", words exactly as spoken
ap.add_argument("--hl", default="")           # keyword(s) to put on the yellow pill, "|"-separated
ap.add_argument("--title-y", type=int, default=300)  # top of the title block (keep >= 240: 3:4 grid crop)
ap.add_argument("--size", type=int, default=118)
ap.add_argument("--zoom", type=float, default=1.0)   # punch into the frame, centred on --focus-y
ap.add_argument("--focus-y", type=float, default=0.5)
ap.add_argument("--card", default="")         # RGBA product card PNG (build_product_card.py)
ap.add_argument("--card-x", type=int, default=600)
ap.add_argument("--card-y", type=int, default=1240)
ap.add_argument("--card-w", type=int, default=400)
ap.add_argument("--font", default="Sukhumvit Set")
a = ap.parse_args()

WHITE, BLACK, PILL_TXT, YELLOW = "&H00FFFFFF&", "&H00000000&", "&H00111111&", "&H004DE1FF&"  # BGR

def line_ass(text):
    out = text
    for k in [h for h in a.hl.split("|") if h]:
        out = out.replace(k, "{\\1c" + PILL_TXT + "\\3c" + YELLOW + "\\bord22}" + k + "{\\1c" + WHITE + "\\3c" + BLACK + "\\bord10}")
    return out

lines = a.title.split("|")
step = int(a.size * 1.32)
events = "\n".join(
    f"Dialogue: 0,0:00:00.00,0:00:05.00,T,,0,0,0,,{{\\an8\\pos(540,{a.title_y + i * step})}}{line_ass(t)}"
    for i, t in enumerate(lines))
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: T,{a.font},{a.size},{WHITE},{WHITE},{BLACK},&H80000000&,-1,0,0,0,100,100,0,0,1,10,4,8,60,60,0,222

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{events}
"""
tmp = tempfile.mkdtemp()
ass_path = os.path.join(tmp, "cover.ass")
open(ass_path, "w").write(ass)

z = a.zoom
base = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"scale={int(1080 * z)}:{int(1920 * z)},crop=1080:1920:(iw-1080)/2:(ih-1920)*{a.focus_y}")
inputs = ["-i", a.frame]
if a.card:
    inputs += ["-i", a.card]
    fc = f"[0:v]{base}[b];[1:v]scale={a.card_w}:-1[c];[b][c]overlay={a.card_x}:{a.card_y},ass={ass_path}"
else:
    fc = f"[0:v]{base},ass={ass_path}"
for ext, q in (("png", []), ("jpg", ["-q:v", "2"])):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-frames:v", "1", *q,
                    f"{a.out}.{ext}"], check=True)
print(f"{a.out}.png\n{a.out}.jpg")
