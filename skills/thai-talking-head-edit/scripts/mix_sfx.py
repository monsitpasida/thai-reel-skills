import json, subprocess, sys

# Mix the ready SFX from sound-plan.json over the voice stem. Each effect is peak-normalized to its
# target and delayed so its loudest moment lands on the cue time; a final limiter guards the peak.
plan_path, voice_path, out_path = sys.argv[1:4]
plan = json.load(open(plan_path))
sfx = [s for s in plan["sfx"] if s["status"] == "ready"]

def peak_db(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(out.split("max_volume:")[1].split("dB")[0])

args = ["ffmpeg", "-v", "error", "-y", "-i", voice_path]
chains, labels = [], ["[0:a]"]
for i, s in enumerate(sfx, 1):
    args += ["-i", s["asset_path"]]
    gain = s["target_peak_dbfs"] - peak_db(s["asset_path"])
    delay_ms = max(0, round((s["timeline_s"] - s["file_peak_offset_s"]) * 1000))
    chains.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gain:.2f}dB,"
                  f"adelay={delay_ms}|{delay_ms}[s{i}]")
    labels.append(f"[s{i}]")
    print(f"{s['type']:5} at {s['timeline_s']:6.2f}s  delay {delay_ms:6d} ms  gain {gain:+6.2f} dB  {s['asset_path'].split('Free SFX/')[-1]}")

graph = ";".join(chains + [f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,"
                           "alimiter=limit=0.79:attack=3:release=60:level=false:latency=1[out]"])
subprocess.run(args + ["-filter_complex", graph, "-map", "[out]", "-c:a", "pcm_s24le", "-ar", "48000", out_path],
               check=True)

# SFX-only stem (same gains and delays, no voice) so masking can be measured directly.
if len(sys.argv) > 4:
    stem = ";".join(chains + [f"{''.join(labels[1:])}amix=inputs={len(labels) - 1}:normalize=0,"
                              f"apad=whole_dur={plan.get('timeline_duration_s', 41.47)}[out]"])
    # args[4:] keeps the voice as input 0 (unused) so the SFX input indexes match the chains
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + args[4:] + ["-filter_complex", stem,
                    "-map", "[out]", "-c:a", "pcm_s24le", "-ar", "48000", sys.argv[4]], check=True)
