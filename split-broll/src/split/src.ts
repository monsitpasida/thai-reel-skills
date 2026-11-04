import { staticFile } from "remotion";

/** Plan paths are relative to public/ unless they are already URLs. */
export const resolveSrc = (src: string) =>
  /^(https?:|blob:|data:)/.test(src) ? src : staticFile(src);
