import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { splitProgress } from "./geometry";
import { SplitInsertSpec } from "./plan";

export type CaptionWord = {
  text: string;
  start_s: number;
  end_s: number;
  spoken_end_s?: number;
};

export type CaptionItem = {
  start_s: number;
  speech_end_s: number;
  text: string;
  lines: string[];
  words: CaptionWord[];
};

export type CaptionsFile = { items: CaptionItem[] };

type Props = {
  captions: CaptionsFile;
  inserts: SplitInsertSpec[];
  /** Caption center line (px) when the speaker is full screen. */
  fullY?: number;
};

// House style (approved BodyKey v11): yellow bar on the spoken word, off 0.1 s after it ends.
const ACCENT = "#FFE14D";
const HOLD_S = 0.1;
const LINGER_S = 0.6;

// Thai combining vowels / tone marks take no width; count only spacing characters.
const visibleLength = (s: string) => s.replace(/[\sัิ-ฺ็-๎]/g, "").length;
// About this many spacing characters fit on one 74 px line inside the 960 px caption box.
const MAX_LINE = 20;

// Too-long single-line chunk: break at the word boundary that balances the two lines best.
const balance = (words: CaptionWord[]): CaptionWord[][] => {
  const lens = words.map((w) => visibleLength(w.text));
  const total = lens.reduce((a, b) => a + b, 0);
  if (total <= MAX_LINE || words.length < 2) return [words];
  let best = 1;
  let bestDiff = Infinity;
  let acc = 0;
  for (let i = 1; i < words.length; i++) {
    acc += lens[i - 1];
    const diff = Math.abs(total - 2 * acc);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = i;
    }
  }
  return [words.slice(0, best), words.slice(best)];
};

const splitLines = (item: CaptionItem): CaptionWord[][] => {
  if (item.lines.length <= 1) return balance(item.words);
  const out: CaptionWord[][] = [[]];
  let budget = item.lines[0].replace(/\s/g, "").length;
  let used = 0;
  for (const w of item.words) {
    if (used >= budget && out.length < item.lines.length) {
      out.push([]);
      budget = item.lines[out.length - 1].replace(/\s/g, "").length;
      used = 0;
    }
    out[out.length - 1].push(w);
    used += w.text.replace(/\s/g, "").length;
  }
  return out;
};

export const SplitCaptions: React.FC<Props> = ({ captions, inserts, fullY = 1650 }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const items = captions.items;
  const idx = items.findIndex((it, i) => {
    const next = items[i + 1]?.start_s ?? Infinity;
    return t >= it.start_s && t < Math.min(next, it.speech_end_s + LINGER_S);
  });
  if (idx === -1) return null;
  const item = items[idx];
  // Same 92% → 100% pop over 100 ms as the approved ASS captions.
  const pop = Math.min(1, (t - item.start_s) / 0.1);

  // Jump to the seam of whichever insert is on screen. Sliding would drag the
  // text across the speaker's face, so it dips out at the old spot and back in
  // at the new one, on the same easing as the split.
  let y = fullY;
  let opacity = 1;
  for (const ins of inserts) {
    const p = splitProgress(frame, fps, {
      startFrame: ins.startFrame,
      durationInFrames: ins.durationInFrames,
      enterFrames: ins.transitionFrames,
      exitFrames: ins.exitFrames,
      easing: ins.easing,
    });
    if (p > 0) {
      // Sits on the feathered seam: below the B-roll subject, above the face.
      const splitY = ins.captionY ?? ins.topRatio * height + 4;
      y = p < 0.5 ? fullY : splitY;
      opacity = Math.abs(2 * p - 1);
      break;
    }
  }

  const lines = splitLines(item);
  const isActive = (w: CaptionWord) =>
    t >= w.start_s && t < (w.spoken_end_s ?? w.end_s) + HOLD_S;

  // Three identical text layers stacked exactly on top of each other:
  // black outlines, then the yellow bar, then the letters. Drawing them in one
  // pass let the 28 px yellow stroke of the spoken word paint over the edge
  // glyphs of its neighbours (e.g. ล in "อนุมูล", ฟ in "เซฟ").
  const layer = (kind: "outline" | "bar" | "fill") =>
    lines.map((line, li) => (
      <div key={li} style={{ display: "flex", flexWrap: "nowrap", justifyContent: "center" }}>
        {line.map((w, wi) => {
          const active = isActive(w);
          const style: React.CSSProperties =
            kind === "outline"
              ? {
                  color: "transparent",
                  WebkitTextStroke: active ? "0px transparent" : "12px #000",
                  textShadow: active ? "none" : "2px 2px 0 rgba(0,0,0,0.5)",
                }
              : kind === "bar"
                ? {
                    color: active ? ACCENT : "transparent",
                    WebkitTextStroke: active ? `28px ${ACCENT}` : "0px transparent",
                  }
                : { color: active ? "#111" : "#fff" };
          // Latin words (AI, EAA, BodyKey) get a little air from the Thai around them.
          const latin = /[A-Za-z]/.test(w.text);
          return (
            <span key={wi} style={{ ...style, padding: latin ? "0 0.18em" : undefined }}>
              {w.text}
            </span>
          );
        })}
      </div>
    ));

  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        width: width - 120,
        top: y,
        translate: "0px -50%",
        scale: 0.92 + 0.08 * pop,
        opacity,
        fontFamily: "'Sukhumvit Set', 'Thonburi', sans-serif",
        fontWeight: 700,
        fontSize: 74,
        lineHeight: 1.25,
      }}
    >
      <div style={{ position: "absolute", inset: 0 }}>{layer("outline")}</div>
      <div style={{ position: "absolute", inset: 0 }}>{layer("bar")}</div>
      <div style={{ position: "relative" }}>{layer("fill")}</div>
    </div>
  );
};
