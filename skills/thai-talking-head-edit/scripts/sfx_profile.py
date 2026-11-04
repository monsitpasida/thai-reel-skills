import subprocess, sys
import numpy as np

# Describe short SFX files without listening: audible length, attack time, brightness, level.
SR = 48000
print(f"{'file':42} {'audible':>7} {'t_peak':>6} {'lead':>5} {'centroid':>8} {'peak':>6} {'lufs~':>6}")
for path in sys.argv[1:]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    if not len(x):
        continue
    hop = SR // 100
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(env)
    pk = db.max()
    above = np.where(db > pk - 30)[0]
    lead = above[0] / 100  # silence before the sound starts
    audible = (above[-1] - above[0] + 1) / 100
    t_peak = db.argmax() / 100
    seg = x[above[0] * hop:(above[-1] + 1) * hop]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1 / SR)
    centroid = (spec * freqs).sum() / spec.sum()
    rms_db = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
    name = path.split("Free SFX/")[-1]
    print(f"{name[:42]:42} {audible:6.2f}s {t_peak:5.2f}s {lead:4.2f}s {centroid:7.0f}Hz {20*np.log10(np.abs(x).max()+1e-9):5.1f} {rms_db:6.1f}")
