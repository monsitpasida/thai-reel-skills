import { Audio, Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { coverRect, Focus, Size, SplitEasing, splitProgress } from "./geometry";
import { resolveSrc } from "./src";

export type KenBurns = "push-in" | "pull-out" | "drift-left" | "drift-right" | "none";

/** A hard cut to another visual inside the top area, without leaving the split. */
export type BrollCut = {
  /** Frame (relative to the insert start) where this visual takes over. */
  atFrame: number;
  src: string;
  startTime?: number;
  focus?: Focus;
  size?: Size;
};

const isImage = (src: string) => /\.(jpe?g|png|webp|avif)(\?|$)/i.test(src);

export type ContextualSplitInsertProps = {
  mainVideo: string;
  /** Video or still image (.jpg/.png/.webp) for the top area. */
  brollVideo: string;
  /** Further visuals cut to inside the same split. */
  brollCuts?: BrollCut[];
  /** Composition frame where the split starts entering. */
  startFrame: number;
  /** Whole insert, including enter and exit transitions. */
  durationInFrames: number;
  topRatio?: number;
  /** Enter transition length (250–400 ms). */
  transitionFrames?: number;
  /** Exit transition length (250–350 ms). Defaults to min(transitionFrames, 350 ms). */
  exitFrames?: number;
  /** Max blur (px) of the soft band over the seam. */
  blurAmount?: number;
  /** Height (px) of the overlap zone where B-roll fades into the speaker. */
  featherSize?: number;
  /** Seconds into the B-roll source to start playing from. */
  brollStartTime?: number;

  /** Composition frame where frame 0 of mainVideo sits. */
  mainVideoStartFrame?: number;
  mainSize?: Size;
  brollSize?: Size;
  /** Point of the B-roll (0..1) kept at the center of the top area. */
  brollFocus?: Focus;
  /** Vertical position (0..1) of the speaker's face in the source frame. */
  speakerFocusY?: number;
  /** 0 = muted (default). Only raise when the B-roll's own sound matters. */
  brollVolume?: number;
  whoosh?: string | null;
  whooshVolume?: number;
  easing?: SplitEasing;
  kenBurns?: KenBurns;
};

const PORTRAIT: Size = { width: 1080, height: 1920 };

export const ContextualSplitInsert: React.FC<ContextualSplitInsertProps> = ({
  startFrame,
  durationInFrames,
  whoosh = null,
  whooshVolume = 0.22,
  ...rest
}) => {
  const { fps } = useVideoConfig();
  return (
    <Sequence
      name="Contextual split insert"
      from={startFrame}
      durationInFrames={durationInFrames}
    >
      <SplitLayers startFrame={startFrame} durationInFrames={durationInFrames} {...rest} />
      {whoosh ? (
        <Audio
          name="Whoosh"
          src={resolveSrc(whoosh)}
          // Skip the lead-in so the swell lands while the split is still opening.
          trimBefore={Math.round(0.12 * fps)}
          durationInFrames={Math.round(0.9 * fps)}
          volume={(f) =>
            interpolate(f, [0, 0.55 * fps, 0.9 * fps], [whooshVolume, whooshVolume, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          }
        />
      ) : null}
    </Sequence>
  );
};

const SplitLayers: React.FC<
  Omit<ContextualSplitInsertProps, "whoosh" | "whooshVolume">
> = ({
  mainVideo,
  brollVideo,
  brollCuts = [],
  startFrame,
  durationInFrames,
  topRatio = 0.58,
  transitionFrames,
  exitFrames,
  blurAmount = 14,
  featherSize = 96,
  brollStartTime = 0,
  mainVideoStartFrame = 0,
  mainSize = PORTRAIT,
  brollSize = PORTRAIT,
  brollFocus = { x: 0.5, y: 0.5 },
  speakerFocusY = 0.45,
  brollVolume = 0,
  easing = "ease-out",
  kenBurns = "push-in",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const enter = transitionFrames ?? Math.round(0.33 * fps);
  const exit = exitFrames ?? Math.min(enter, Math.round(0.35 * fps));
  const timing = { startFrame: 0, durationInFrames, enterFrames: enter, exitFrames: exit, easing };
  const p = splitProgress(frame, fps, timing);

  const seamY = topRatio * height;
  const brollBoxH = seamY + featherSize / 2;
  const revealedH = brollBoxH * p;

  // Speaker: same framing as the full-screen base at p = 0, then slides down
  // until the face sits in the middle of the bottom area. The top edge never
  // drops below the feather, so the B-roll always covers it — no gap, no bar.
  const speaker = coverRect(mainSize, { width, height }, { x: 0.5, y: 0.5 });
  const faceY = speaker.top + speakerFocusY * speaker.height;
  const targetFaceY = seamY + (height - seamY) * 0.5;
  const maxShift = seamY - featherSize - speaker.top;
  const shift = Math.max(0, Math.min(targetFaceY - faceY, maxShift));

  // B-roll: slow Ken Burns across the whole insert so it never feels frozen.
  const kb = frame / Math.max(1, durationInFrames - 1);
  const kbScale =
    kenBurns === "push-in"
      ? interpolate(kb, [0, 1], [1.0, 1.06])
      : kenBurns === "pull-out"
        ? interpolate(kb, [0, 1], [1.07, 1.01])
        : kenBurns === "none"
          ? 1
          : 1.06;
  const kbDriftX =
    kenBurns === "drift-left"
      ? interpolate(kb, [0, 1], [0.025, -0.025])
      : kenBurns === "drift-right"
        ? interpolate(kb, [0, 1], [-0.025, 0.025])
        : 0;
  const clips: Required<BrollCut>[] = [
    { atFrame: 0, src: brollVideo, startTime: brollStartTime, focus: brollFocus, size: brollSize },
    ...brollCuts.map((c) => ({
      atFrame: c.atFrame,
      src: c.src,
      startTime: c.startTime ?? 0,
      focus: c.focus ?? brollFocus,
      size: c.size ?? PORTRAIT,
    })),
  ].sort((a, b) => a.atFrame - b.atFrame);

  // Fade happens in the first third of the reveal: on the way in it is
  // already opaque while the edge is still travelling; on the way out it
  // dissolves as it retracts.
  const brollOpacity = interpolate(p, [0, 0.35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const feather = Math.min(featherSize, revealedH);

  return (
    <AbsoluteFill>
      <AbsoluteFill name="Speaker (split)" style={{ overflow: "hidden", backgroundColor: "black" }}>
        <Video
          name="Speaker copy"
          src={resolveSrc(mainVideo)}
          trimBefore={startFrame - mainVideoStartFrame}
          muted
          objectFit="fill"
          style={{
            position: "absolute",
            left: speaker.left,
            top: speaker.top,
            width: speaker.width,
            height: speaker.height,
            translate: `0px ${p * shift}px`,
          }}
        />
      </AbsoluteFill>

      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width,
          height: revealedH,
          overflow: "hidden",
          opacity: brollOpacity,
          maskImage: `linear-gradient(to bottom, #000 0px, #000 ${revealedH - feather}px, transparent ${revealedH}px)`,
          WebkitMaskImage: `linear-gradient(to bottom, #000 0px, #000 ${revealedH - feather}px, transparent ${revealedH}px)`,
        }}
      >
        {/* Content descends a little as the curtain opens: reveal from the top. */}
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            width,
            height: brollBoxH,
            translate: `0px ${-(1 - p) * brollBoxH * 0.16}px`,
          }}
        >
          {clips.map((clip, i) => {
            const until = clips[i + 1]?.atFrame ?? durationInFrames;
            // Ken Burns runs on the insert clock, so it carries straight across cuts.
            const rect = coverRect(
              clip.size,
              { width, height: brollBoxH },
              { x: clip.focus.x + kbDriftX, y: clip.focus.y },
              kbScale,
            );
            const style: React.CSSProperties = {
              position: "absolute",
              left: rect.left,
              top: rect.top,
              width: rect.width,
              height: rect.height,
            };
            return (
              <Sequence
                key={i}
                name={`B-roll ${i + 1}`}
                from={clip.atFrame}
                durationInFrames={until - clip.atFrame}
              >
                {isImage(clip.src) ? (
                  <Img src={resolveSrc(clip.src)} style={style} />
                ) : (
                  <Video
                    src={resolveSrc(clip.src)}
                    trimBefore={Math.round(clip.startTime * fps)}
                    muted={brollVolume <= 0}
                    volume={(f) => brollVolume * splitProgress(f + clip.atFrame, fps, timing)}
                    objectFit="fill"
                    style={style}
                  />
                )}
              </Sequence>
            );
          })}
        </div>
      </div>

      {/* Soft blur band riding on the seam: blends both images into each other. */}
      <div
        style={{
          position: "absolute",
          left: 0,
          width,
          top: revealedH - featherSize * 1.15,
          height: featherSize * 1.5,
          opacity: brollOpacity,
          backdropFilter: `blur(${blurAmount * p}px)`,
          WebkitBackdropFilter: `blur(${blurAmount * p}px)`,
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.10) 50%, rgba(0,0,0,0) 100%)",
          maskImage:
            "linear-gradient(to bottom, transparent 0%, #000 40%, #000 60%, transparent 100%)",
          WebkitMaskImage:
            "linear-gradient(to bottom, transparent 0%, #000 40%, #000 60%, transparent 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
