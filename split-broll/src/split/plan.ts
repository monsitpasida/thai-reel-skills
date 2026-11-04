import { Focus, Size, SplitEasing } from "./geometry";
import { BrollCut, KenBurns } from "./ContextualSplitInsert";

/** One entry of the Master Edit Plan (source of truth, times in seconds). */
export type SplitPlanItem = {
  type: "contextual-split-insert";
  start: number;
  end: number;
  visual: string;
  layout: "top-broll-bottom-speaker";
  topRatio?: number;
  bottomRatio?: number;
  seamStyle?: "soft-blur-feather";
  /** Why this insert exists: explain | visualize | prove | context | demonstrate | reset-attention */
  reason?: string;
  /** What is being said over it — for review only. */
  spokenContext?: string;
  /** Seconds into the visual to start from. */
  visualStart?: number;
  /** Subject point of the visual (0..1) to keep visible in the top area. */
  focus?: Focus;
  /** Keep the B-roll's own sound only when it carries the moment. */
  visualAudio?: boolean;
  visualVolume?: number;
  /** "auto" plays a soft whoosh only when it will not feel repetitive. */
  sfx?: "auto" | "whoosh" | "none";
  /** Override the caption center line (px) while split. */
  captionY?: number;
  /** Cut to other visuals inside the same split (`at` = seconds on the main timeline). */
  cuts?: { at: number; visual: string; visualStart?: number; focus?: Focus }[];
};

/** Real product photo shown on the word that names it (seconds on the main timeline). */
export type ProductPlanItem = {
  start: number;
  end: number;
  image: string;
  /** Corner of the B-roll area to sit in, away from the B-roll subject. */
  side?: "left" | "right";
  /** What is being said — for review only. */
  spokenContext?: string;
  /** Where the image came from. */
  source?: string;
};

export type EditPlan = {
  inserts: SplitPlanItem[];
  products?: ProductPlanItem[];
  whoosh?: string;
  pop?: string;
};

export type SplitInsertSpec = {
  id: string;
  brollVideo: string;
  brollCuts: BrollCut[];
  startFrame: number;
  durationInFrames: number;
  topRatio: number;
  transitionFrames: number;
  exitFrames: number;
  blurAmount: number;
  featherSize: number;
  brollStartTime: number;
  brollFocus: Focus;
  brollSize?: Size;
  brollVolume: number;
  whoosh: string | null;
  easing: SplitEasing;
  kenBurns: KenBurns;
  captionY?: number;
};

const MIN_S = 1.5;
const MAX_S = 4;
// A whoosh closer than this to the previous insert starts to sound like a template.
const WHOOSH_MIN_GAP_S = 4;

// Small, deterministic variations so consecutive inserts never move identically.
// Enter: 0.30–0.37 s, exit: 0.27–0.33 s — all inside the 250–400 / 250–350 ms brief.
const ENTER_S = [0.33, 0.37, 0.3];
const EXIT_S = [0.3, 0.33, 0.27];
const EASINGS: SplitEasing[] = ["ease-out", "spring", "ease-out"];
const KEN_BURNS: KenBurns[] = ["push-in", "drift-left", "pull-out", "drift-right"];

export const planToInserts = (
  plan: EditPlan,
  fps: number,
  sizes: Record<string, Size> = {},
): SplitInsertSpec[] => {
  const items = plan.inserts
    .filter((i) => i.type === "contextual-split-insert")
    .slice()
    .sort((a, b) => a.start - b.start);

  const specs: SplitInsertSpec[] = [];
  let prevEnd = -Infinity;

  items.forEach((item, index) => {
    let start = item.start;
    const end = item.end;
    if (start < prevEnd) {
      console.warn(`[split] insert ${index} overlaps the previous one; starting it at ${prevEnd}s`);
      start = prevEnd;
    }
    const dur = end - start;
    if (dur < MIN_S || dur > MAX_S) {
      console.warn(
        `[split] insert ${index} (${start}s–${end}s) is ${dur.toFixed(2)}s; B-roll inserts should be ${MIN_S}–${MAX_S}s`,
      );
    }
    if (dur <= 0) return;

    const sfx = item.sfx ?? "auto";
    const gap = start - prevEnd;
    const wantsWhoosh = sfx === "whoosh" || (sfx === "auto" && gap >= WHOOSH_MIN_GAP_S);

    const startFrame = Math.round(start * fps);
    const durationInFrames = Math.round(end * fps) - startFrame;
    const transitionFrames = Math.round(ENTER_S[index % ENTER_S.length] * fps);
    const exitFrames = Math.round(EXIT_S[index % EXIT_S.length] * fps);

    specs.push({
      id: `split-${index}`,
      brollVideo: item.visual,
      brollCuts: (item.cuts ?? [])
        .filter((c) => c.at > start && c.at < end)
        .map((c) => ({
          atFrame: Math.round(c.at * fps) - startFrame,
          src: c.visual,
          startTime: c.visualStart ?? 0,
          focus: c.focus,
          size: sizes[c.visual],
        })),
      startFrame,
      // Never let the enter and exit transitions collide on very short inserts.
      durationInFrames: Math.max(durationInFrames, transitionFrames + exitFrames + 1),
      topRatio: item.topRatio ?? 0.58,
      transitionFrames,
      exitFrames,
      blurAmount: 14,
      featherSize: 96,
      brollStartTime: item.visualStart ?? 0,
      brollFocus: item.focus ?? { x: 0.5, y: 0.5 },
      brollSize: sizes[item.visual],
      brollVolume: item.visualAudio ? (item.visualVolume ?? 0.6) : 0,
      whoosh: wantsWhoosh ? (plan.whoosh ?? null) : null,
      easing: EASINGS[index % EASINGS.length],
      kenBurns: KEN_BURNS[index % KEN_BURNS.length],
      captionY: item.captionY,
    });
    prevEnd = end;
  });

  return specs;
};
