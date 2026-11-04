import json, subprocess, sys
import numpy as np

# For each SFX cue: how far it sits under the voice peak (masking rule) and how well it pokes out
# of the voice above 4 kHz while it is actually sounding (audibility), using the separate stems.
W = sys.argv[1]
SR, HOP = 48000, 480  # 10 ms frames

def load(path, hp=None):
    af = ["-af", f"highpass=f={hp}"] if hp else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, *af, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def env(x):
    n = len(x) // HOP
    return 20 * np.log10(np.sqrt((x[:n * HOP].reshape(n, HOP) ** 2).mean(1)) + 1e-9)

v, s = load(f"{W}/audio/voice.wav"), load(f"{W}/audio/sfx-stem.wav")
ve, se = env(load(f"{W}/audio/voice.wav", 4000)), env(load(f"{W}/audio/sfx-stem.wav", 4000))
pk = lambda x: 20 * np.log10(np.abs(x).max() + 1e-9)

print(f"{'cue':>6} {'type':5} {'under voice pk':>14} {'HF SNR while sounding':>22}")
worst = []
for c in json.load(open(f"{W}/sound-plan.json"))["sfx"]:
    a, b = int((c["timeline_s"] - 0.1) * SR), int((c["timeline_s"] + 0.3) * SR)
    under = pk(v[a:b]) - pk(s[a:b])
    fa, fb = a // HOP, b // HOP
    seg = se[fa:fb]
    on = np.where(seg > seg.max() - 12)[0] + fa  # frames where the effect is really sounding
    p_s = 10 * np.log10(np.mean(10 ** (se[on] / 10)))
    p_v = 10 * np.log10(np.mean(10 ** (ve[on] / 10)))
    snr = p_s - p_v
    flags = ("" if under >= 8 else "  too loud") + ("" if c["type"] == "hit" or snr >= 0 else "  may be masked")
    worst.append(flags)
    print(f"{c['timeline_s']:6.2f} {c['type']:5} {under:12.1f}dB {snr:+20.1f}dB{flags}")
print("all within rules" if not any(worst) else "needs adjustment")
