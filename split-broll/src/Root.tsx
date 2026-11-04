import { Composition } from "remotion";
import captions from "./data/captions.json";
import editPlan from "./data/edit-plan.json";
import {
  calculateSplitReelMetadata,
  SplitReel,
  SplitReelProps,
} from "./SplitReel";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SplitReel"
        component={SplitReel}
        durationInFrames={30 * 60}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calculateSplitReelMetadata}
        defaultProps={{
          mainVideo: "demo/speaker.mp4",
          editPlan: editPlan as SplitReelProps["editPlan"],
          captions: captions as SplitReelProps["captions"],
          speakerFocusY: 0.45,
        }}
      />
    </>
  );
};
