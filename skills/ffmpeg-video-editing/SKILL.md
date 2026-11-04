---
name: ffmpeg-video-editing
description: Cut, trim, join, resize, crop, add audio/subtitles/text, change speed, and export video with FFmpeg. Use for any clip-editing or conversion task on video or audio files.
---

# FFmpeg video editing

Before starting: run `ffmpeg -version`. If missing on macOS: `brew install ffmpeg` (needs Homebrew).
Always inspect the input first:
`ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate -of json in.mp4`

Rules
- Never overwrite the source; write to a new file (`-n` refuses overwrite, `-y` only for your own outputs).
- Default export: `-c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart`
- `-c copy` is instant but cuts only on keyframes; re-encode when the cut must be frame-exact.
- After rendering, verify with ffprobe (duration, streams) and grab a frame: `ffmpeg -ss 2 -i out.mp4 -frames:v 1 check.jpg`.
- Quote paths that contain spaces or Thai characters.

## Trim
Fast (keyframe): `ffmpeg -ss 00:01:05 -to 00:01:30 -i in.mp4 -c copy cut.mp4`
Exact: `ffmpeg -i in.mp4 -ss 65 -to 90 -c:v libx264 -crf 20 -preset veryfast -c:a aac cut.mp4`

## Join clips
Same codec/size: write `list.txt` lines `file 'a.mp4'` then `ffmpeg -f concat -safe 0 -i list.txt -c copy joined.mp4`
Different sources: `ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v]scale=1920:1080,setsar=1,fps=30[v0];[1:v]scale=1920:1080,setsar=1,fps=30[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" joined.mp4`
Crossfade: `-filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=<len_a-0.5>[v];[0:a][1:a]acrossfade=d=0.5[a]"`

## Remove a middle section (keep 0–10s and 20s–end)
`ffmpeg -i in.mp4 -filter_complex "[0:v]trim=0:10,setpts=PTS-STARTPTS[v1];[0:a]atrim=0:10,asetpts=PTS-STARTPTS[a1];[0:v]trim=start=20,setpts=PTS-STARTPTS[v2];[0:a]atrim=start=20,asetpts=PTS-STARTPTS[a2];[v1][a1][v2][a2]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" out.mp4`

## Vertical 9:16 (TikTok/Reels/Shorts)
Center crop: `-vf "crop=ih*9/16:ih,scale=1080:1920"`
Blurred-background fit: `-filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"`

## Audio
Replace: `ffmpeg -i v.mp4 -i music.mp3 -map 0:v -map 1:a -c:v copy -shortest out.mp4`
Mix music under voice: `-filter_complex "[1:a]volume=0.15[m];[0:a][m]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]" -c:v copy`
Extract: `ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 audio.wav` (Whisper-ready)
Normalize loudness: `-af loudnorm=I=-14:TP=-1.5:LRA=11`
Mute: `-an`

## Subtitles
Burn in: `-vf "subtitles=subs.srt:force_style='FontName=Sukhumvit Set,FontSize=18,Outline=2'"` (Thai needs a Thai-capable font)
Soft track: `ffmpeg -i in.mp4 -i subs.srt -c copy -c:s mov_text out.mp4`

## Text, logo, speed, other
Text: `-vf "drawtext=text='Hello':fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:fontsize=64:fontcolor=white:x=(w-tw)/2:y=h-150"`
Logo: `-i logo.png -filter_complex "overlay=W-w-40:40"`
Speed 2x: `-filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]"`
Fade: `-vf "fade=in:0:d=0.5,fade=out:st=<end-0.5>:d=0.5" -af "afade=in:d=0.5,afade=out:st=<end-0.5>:d=0.5"`
GIF: `-vf "fps=12,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse"`
Compress for sharing: raise CRF to 26–28 and/or `-vf scale=-2:720`.
Thumbnail grid for review: `ffmpeg -i in.mp4 -vf "fps=1/5,scale=320:-1,tile=4x4" -frames:v 1 contact.jpg`
Silence detection (find dead air to cut): `ffmpeg -i in.mp4 -af silencedetect=n=-35dB:d=0.6 -f null - 2>&1 | grep silence_`
