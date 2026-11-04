import json, sys

# Product-card overlays from visual-insert-plan.json. Prints the image paths (one per line) to
# argv[2] and the filter-graph fragment that takes [base] and ends unlabelled, so the caller can
# append more filters. Input index of the first card = argv[3].
plan_path, inputs_out, first_index = sys.argv[1], sys.argv[2], int(sys.argv[3])
plan = json.load(open(plan_path))
FADE_IN, FADE_OUT, RISE, RISE_S = 0.18, 0.15, 36, 0.22

paths, parts, cur, n = [], [], "base", 0
for it in plan["items"]:
    if it["type"] != "product_card" or it["status"] != "ready":
        continue
    end = it["timeline_end_s"]
    for img in it["images"]:
        idx = first_index + len(paths)
        paths.append(img["asset_path"])
        s = img["appear_s"]
        parts.append(f"[{idx}:v]format=rgba,fade=t=in:st={s}:d={FADE_IN}:alpha=1,"
                     f"fade=t=out:st={end - FADE_OUT:.3f}:d={FADE_OUT}:alpha=1[c{n}]")
        # ease-out slide up; commas are safe inside the single quotes, as in the zoompan expression
        y = f"{img['y']}+{RISE}*pow(max(0,1-(t-{s})/{RISE_S}),2)"
        parts.append(f"[{cur}][c{n}]overlay=x={img['x']}:y='{y}':enable='between(t,{s},{end})':format=auto[o{n}]")
        cur, n = f"o{n}", n + 1

open(inputs_out, "w").write("\n".join(paths) + ("\n" if paths else ""))
print(";".join(parts) + f";[{cur}]" if parts else "[base]")
