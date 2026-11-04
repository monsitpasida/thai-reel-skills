import sys
from PIL import Image, ImageDraw, ImageFilter

# Render one product image onto a rounded white card with a soft shadow, as an RGBA PNG.
# Usage: build_product_card.py in.jpg out.png size_px|WxH [crop x0,y0,x1,y1 as fractions]
src, out = sys.argv[1], sys.argv[2]
cw, ch = (int(v) for v in sys.argv[3].split("x")) if "x" in sys.argv[3] else (int(sys.argv[3]),) * 2  # "WxH" or one size
crop = [float(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else None

RADIUS, PAD, SHADOW = 32, 28, 24  # corner radius matches the text insert cards
img = Image.open(src).convert("RGBA")
# flatten transparency (e.g. macOS screenshots) onto white so empty edges trim instead of turning black
flat = Image.new("RGBA", img.size, (255, 255, 255, 255))
flat.alpha_composite(img)
img = flat
if crop:
    w, h = img.size
    img = img.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))

# trim near-white margins so the product fills the card
gray = img.convert("L")
box = gray.point(lambda p: 255 if p < 245 else 0).getbbox()
if box:
    img = img.crop(box)

img.thumbnail((cw - 2 * PAD, ch - 2 * PAD), Image.LANCZOS)

canvas = Image.new("RGBA", (cw + 2 * SHADOW, ch + 2 * SHADOW), (0, 0, 0, 0))
shadow = Image.new("L", canvas.size, 0)
ImageDraw.Draw(shadow).rounded_rectangle((SHADOW, SHADOW + 8, SHADOW + cw, SHADOW + ch + 8), RADIUS, fill=110)
shadow = shadow.filter(ImageFilter.GaussianBlur(14))
canvas.paste((0, 0, 0, 255), (0, 0), shadow)

card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
ImageDraw.Draw(card).rounded_rectangle((0, 0, cw - 1, ch - 1), RADIUS, fill=(255, 255, 255, 255))
card.alpha_composite(img, ((cw - img.width) // 2, (ch - img.height) // 2))
canvas.alpha_composite(card, (SHADOW, SHADOW))
canvas.save(out)
print(f"{out}: {canvas.size[0]}x{canvas.size[1]} (product {img.width}x{img.height})")
