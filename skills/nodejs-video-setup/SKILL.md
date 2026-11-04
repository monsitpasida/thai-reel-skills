---
name: nodejs-video-setup
description: Check and set up the Node.js toolchain (node, npm, npx, nvm) on macOS for video tooling such as Remotion, HyperFrames and ElevenLabs JS SDK, and write small Node scripts that drive FFmpeg. Use when a video task needs Node or a node/npm command fails.
---

# Node.js for video work

## Check
`node -v && npm -v && which node`
- Remotion needs Node 18+ (use current LTS). HyperFrames needs Node 22+.
- If missing on macOS, prefer one of:
  - `brew install node` (simple), or
  - nvm: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash`, reopen terminal, `nvm install --lts && nvm alias default 'lts/*'`
- Ask before installing anything system-wide. Never use `sudo npm install -g`.

## Project basics
- New project: `mkdir my-video && cd my-video && npm init -y`
- Remotion: `npx create-video@latest` then `npm run dev` (Studio) / `npx remotion render`.
- HyperFrames: `npx hyperframes init my-video`.
- ElevenLabs: `npm i @elevenlabs/elevenlabs-js` (not the old `elevenlabs` package). Keep the key in `.env` as `ELEVENLABS_API_KEY`; add `.env` to `.gitignore`.
- Use `"type": "module"` in package.json for `import` syntax.

## Driving FFmpeg from Node
```js
import { spawn } from "node:child_process";
export function ffmpeg(args) {
  return new Promise((res, rej) => {
    const p = spawn("ffmpeg", ["-hide_banner", "-y", ...args], { stdio: ["ignore", "inherit", "inherit"] });
    p.on("close", c => (c === 0 ? res() : rej(new Error(`ffmpeg exited ${c}`))));
  });
}
// await ffmpeg(["-i", "in.mp4", "-ss", "5", "-to", "15", "-c:v", "libx264", "-crf", "20", "out.mp4"]);
```
- Pass args as an array (no shell string) so paths with spaces/Thai work and nothing is injected.
- For durations use `ffprobe -v error -show_entries format=duration -of csv=p=0 file`.
- Batch jobs: run 2–4 encodes in parallel at most; FFmpeg already uses multiple cores.

## Common errors
- `command not found: npx` → Node not on PATH; reopen terminal or `source ~/.zshrc` after nvm install.
- `EACCES` on global installs → use nvm or `npx` instead of global installs.
- Unsupported engine / syntax errors in deps → Node too old; `nvm install --lts`.
