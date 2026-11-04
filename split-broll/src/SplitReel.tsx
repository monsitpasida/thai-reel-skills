import { Video } from "@remotion/media";
import { ALL_FORMATS, Input, UrlSource } from "mediabunny";
import React from "react";
import { AbsoluteFill, CalculateMetadataFunction, useVideoConfig } from "remotion";
import { ContextualSplitInsert } from "./split/ContextualSplitInsert";
import { ProductCard } from "./split/ProductCard";
import { coverRect, Size } from "./split/geometry";
import { EditPlan, planToInserts } from "./split/plan";
import { CaptionsFile, SplitCaptions } from "./split/SplitCaptions";
import { resolveSrc } from "./split/src";

export type SplitReelProps = {
  mainVideo: string;
  editPlan: EditPlan;
  captions: CaptionsFile;
  /** Vertical position (0..1) of the speaker's face in the source frame. */
  speakerFocusY: number;
  /** Filled in by calculateMetadata. */
  sizes?: Record<string, Size>;
};

const probeImage = (src: string) =>
  new Promise<{ size: Size; duration: number }>((resolve, reject) => {
    const img = new Image();
    img.onload = () =>
      resolve({ size: { width: img.naturalWidth, height: img.naturalHeight }, duration: 0 });
    img.onerror = () => reject(new Error(`Could not load image ${src}`));
    img.src = resolveSrc(src);
  });

const probe = async (src: string) => {
  if (/\.(jpe?g|png|webp|avif)(\?|$)/i.test(src)) return probeImage(src);
  const input = new Input({ formats: ALL_FORMATS, source: new UrlSource(resolveSrc(src)) });
  try {
    const track = await input.getPrimaryVideoTrack();
    if (!track) throw new Error(`No video track in ${src}`);
    return {
      size: { width: track.displayWidth, height: track.displayHeight },
      duration: await input.computeDuration(),
    };
  } finally {
    input.dispose();
  }
};

export const calculateSplitReelMetadata: CalculateMetadataFunction<SplitReelProps> = async ({
  props,
}) => {
  const fps = 30;
  const visuals = [
    props.mainVideo,
    ...new Set(
      props.editPlan.inserts.flatMap((i) => [i.visual, ...(i.cuts ?? []).map((c) => c.visual)]),
    ),
  ];
  const probed = await Promise.all(visuals.map(probe));
  const sizes: Record<string, Size> = {};
  visuals.forEach((v, i) => {
    sizes[v] = probed[i].size;
  });
  return {
    fps,
    durationInFrames: Math.floor(probed[0].duration * fps),
    props: { ...props, sizes },
  };
};

export const SplitReel: React.FC<SplitReelProps> = ({
  mainVideo,
  editPlan,
  captions,
  speakerFocusY,
  sizes = {},
}) => {
  const { fps, width, height } = useVideoConfig();
  const inserts = planToInserts(editPlan, fps, sizes);
  const mainSize = sizes[mainVideo] ?? { width: 1080, height: 1920 };
  const base = coverRect(mainSize, { width, height }, { x: 0.5, y: 0.5 });

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* The only audible copy of the speaker: voice runs unbroken under every insert. */}
      <Video
        name="Speaker"
        src={resolveSrc(mainVideo)}
        objectFit="fill"
        style={{
          position: "absolute",
          left: base.left,
          top: base.top,
          width: base.width,
          height: base.height,
        }}
      />

      {inserts.map((ins) => (
        <ContextualSplitInsert
          key={ins.id}
          mainVideo={mainVideo}
          mainSize={mainSize}
          speakerFocusY={speakerFocusY}
          brollVideo={ins.brollVideo}
          brollCuts={ins.brollCuts}
          brollSize={ins.brollSize}
          startFrame={ins.startFrame}
          durationInFrames={ins.durationInFrames}
          topRatio={ins.topRatio}
          transitionFrames={ins.transitionFrames}
          exitFrames={ins.exitFrames}
          blurAmount={ins.blurAmount}
          featherSize={ins.featherSize}
          brollStartTime={ins.brollStartTime}
          brollFocus={ins.brollFocus}
          brollVolume={ins.brollVolume}
          whoosh={ins.whoosh}
          easing={ins.easing}
          kenBurns={ins.kenBurns}
        />
      ))}

      {(editPlan.products ?? []).map((prod, i) => (
        <ProductCard
          key={`product-${i}`}
          image={prod.image}
          left={prod.side === "left" ? 56 : width - 56 - 330}
          startFrame={Math.round(prod.start * fps)}
          durationInFrames={Math.round((prod.end - prod.start) * fps)}
          sfx={editPlan.pop ?? null}
        />
      ))}

      <SplitCaptions captions={captions} inserts={inserts} />
    </AbsoluteFill>
  );
};
