import { Easing, interpolate, spring } from "remotion";

export type Size = { width: number; height: number };
export type Focus = { x: number; y: number };

export type Rect = { left: number; top: number; width: number; height: number };

/**
 * object-fit: cover, computed by hand so the crop can be aimed at a subject.
 * `focus` is the point of the source (0..1) that should sit at the box center,
 * clamped so no edge of the source is ever exposed. Aspect ratio is preserved
 * exactly — width and height are always scaled by the same factor.
 */
export const coverRect = (
  src: Size,
  box: Size,
  focus: Focus,
  extraScale = 1,
): Rect => {
  const scale = Math.max(box.width / src.width, box.height / src.height) * extraScale;
  const width = src.width * scale;
  const height = src.height * scale;
  const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));
  const left = clamp(box.width / 2 - focus.x * width, box.width - width, 0);
  const top = clamp(box.height / 2 - focus.y * height, box.height - height, 0);
  return { left, top, width, height };
};

export type SplitEasing = "ease-out" | "spring";

export type SplitTiming = {
  startFrame: number;
  durationInFrames: number;
  enterFrames: number;
  exitFrames: number;
  easing: SplitEasing;
};

// Expo-style ease-out: fast departure, long soft landing, no overshoot.
const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);
// Symmetric ease for the retract so the speaker glides back instead of snapping.
const EASE_EXIT = Easing.bezier(0.45, 0, 0.25, 1);

/**
 * 0 = speaker full screen, 1 = fully split. Shared by the insert and the
 * captions so both always agree on where the seam is.
 */
export const splitProgress = (frame: number, fps: number, t: SplitTiming): number => {
  const local = frame - t.startFrame;
  if (local < 0 || local >= t.durationInFrames) return 0;

  const exitStart = t.durationInFrames - t.exitFrames;
  if (local >= exitStart) {
    return interpolate(local, [exitStart, t.durationInFrames], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: EASE_EXIT,
    });
  }

  if (t.easing === "spring") {
    // damping 200 = critically damped: settles without any bounce.
    return spring({
      frame: local,
      fps,
      config: { damping: 200 },
      durationInFrames: t.enterFrames,
    });
  }
  return interpolate(local, [0, t.enterFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
};
