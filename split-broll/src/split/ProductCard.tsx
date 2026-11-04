import { Audio } from "@remotion/media";
import React from "react";
import {
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { resolveSrc } from "./src";

export type ProductCardProps = {
  image: string;
  startFrame: number;
  durationInFrames: number;
  /** Card edge length in px. */
  size?: number;
  left?: number;
  top?: number;
  sfx?: string | null;
  sfxVolume?: number;
};

/**
 * Real product photo on a white card, popping in on the word that names it
 * (approved house style). Meant to sit in the B-roll half of a split.
 */
export const ProductCard: React.FC<ProductCardProps> = ({
  startFrame,
  durationInFrames,
  sfx = null,
  sfxVolume = 0.5,
  ...rest
}) => (
  <Sequence name="Product card" from={startFrame} durationInFrames={durationInFrames}>
    <Card durationInFrames={durationInFrames} {...rest} />
    {sfx ? <Audio name="Pop" src={resolveSrc(sfx)} volume={sfxVolume} /> : null}
  </Sequence>
);

const Card: React.FC<Omit<ProductCardProps, "startFrame" | "sfx" | "sfxVolume">> = ({
  image,
  durationInFrames,
  size = 330,
  left = 1080 - 56 - 330,
  top = 150,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (image.endsWith(".webm")) {
    return <CartoonClip image={image} durationInFrames={durationInFrames} size={size} left={left} top={top} />;
  }
  // A small, quick settle — reads as a pop without a rubbery bounce.
  const pop = spring({ frame, fps, config: { damping: 14, stiffness: 180, mass: 0.6 } });
  const out = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.quad),
  });

  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width: size,
        height: size,
        borderRadius: 36,
        backgroundColor: "#fff",
        boxShadow: "0 18px 40px rgba(0,0,0,0.28)",
        overflow: "hidden",
        opacity: Math.min(1, pop * 1.6) * out,
        scale: interpolate(pop, [0, 1], [0.82, 1]),
        translate: `0px ${interpolate(pop, [0, 1], [26, 0])}px`,
      }}
    >
      <Img
        src={resolveSrc(image)}
        style={{ width: "100%", height: "100%", objectFit: "contain" }}
      />
    </div>
  );
};

/**
 * Animated cartoon of the product (transparent WebM from product-cartoons/catalog.json).
 * The clip animates its own entrance, so no white card; a little larger than the photo card.
 */
const CartoonClip: React.FC<{ image: string; durationInFrames: number; size: number; left: number; top: number }> = ({
  image,
  durationInFrames,
  size,
  left,
  top,
}) => {
  const frame = useCurrentFrame();
  const out = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.quad),
  });
  const big = Math.round(size * 1.35);
  return (
    <OffthreadVideo
      src={resolveSrc(image)}
      transparent
      muted
      style={{
        position: "absolute",
        left: left - (big - size) / 2,
        top: top - (big - size) / 2,
        width: big,
        height: big,
        opacity: out,
      }}
    />
  );
};
