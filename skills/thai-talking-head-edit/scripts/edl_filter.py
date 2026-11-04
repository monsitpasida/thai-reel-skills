import json, sys

# Build an ffmpeg filter_complex that trims each EDL segment from input 0 and concatenates them.
# Usage: edl_filter.py edit-plan.json [video chain after concat] [audio chain after concat]
plan = json.load(open(sys.argv[1]))
post = sys.argv[2] if len(sys.argv) > 2 else ""
apost = sys.argv[3] if len(sys.argv) > 3 else ""

parts, labels = [], []
for i, s in enumerate(plan["segments"]):
    a, b = s["source_start_s"], s["source_end_s"]
    parts.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,fps=30[v{i}]")
    # 15 ms fades at each audio edge avoid clicks at the jump cuts
    d = b - a
    parts.append(
        f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
        f"afade=t=in:d=0.015,afade=t=out:st={d - 0.015:.3f}:d=0.015[a{i}]"
    )
    labels.append(f"[v{i}][a{i}]")

n = len(plan["segments"])
parts.append(f"{''.join(labels)}concat=n={n}:v=1:a=1[vc][acat]")
parts.append(f"[vc]{post}[vout]" if post else "[vc]null[vout]")
if apost == "drop":  # audio comes from a separate mix (sound-design)
    parts.append("[acat]anullsink")
else:
    parts.append(f"[acat]{apost}[ac]" if apost else "[acat]anull[ac]")
print(";".join(parts))
