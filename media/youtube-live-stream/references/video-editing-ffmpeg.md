# ffmpeg video-editing recipes (for live/upload pipeline)

ffmpeg is the correct editing tool for the live pipeline — CapCut is banned on Indian Play Store, has no CLI/API (GUI only), and ADB-tap automation of its timeline is fragile. These recipes operate on already-downloaded clips before they go through `norm -> concat -> RTMP`.

## Crop + watermark (bottom-right)
```bash
ffmpeg -y -i in.mp4 -i logo.png \
  -filter_complex "[0:v]crop=1280:720:(in_w-1280)/2:(in_h-720)/2[v];[v][1:v]overlay=W-w-20:H-h-20" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac out_01.mp4
```

## Trim (5s–35s)
```bash
ffmpeg -y -ss 00:00:05 -to 00:00:35 -i out_01.mp4 -c:v libx264 -crf 20 -c:a aac trim_01.mp4
```

## Background-music mix (original + BGM @15%)
```bash
ffmpeg -y -i in.mp4 -stream_loop -1 -i bgm.mp3 \
  -filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.15[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -shortest out_bgm.mp4
```

## Flash-cut (rapid strobe) effect
Alternates real footage with a full-frame black overlay every `X` seconds, via a `drawbox` timeline expression. This is a SYNTHETIC rapid-cut effect (works on a single continuous shot — no scene cuts needed).
```bash
# 0.1s on / 0.1s off = ~5 strobe cycles per second (30fps => 3 frames per phase)
ffmpeg -y -i in.mp4 \
  -vf "drawbox=color=black:t=fill:enable='gte(mod(t,0.2),0.1)'" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a copy out_flashcut.mp4
```
Verified: 12.31s source, 368 frames, 157 black frames (42.7%), H.264+AAC (audio copied unchanged).

**Photosensitivity warning**: a 5 Hz strobe can trigger epileptic seizures — add a flash warning on YouTube or reduce intensity (e.g. `mod(t,0.5)` → 2 Hz, or keep flash fraction lower). Big Pickle flagged this; do not ship 5 Hz without a warning.

## Loop-concat -> RTMP (unlimited)
```bash
ffmpeg -re -stream_loop -1 -i concat.mp4 \
  -c:v libx264 -preset veryfast -b:v 4000k -maxrate 4000k -bufsize 8000k \
  -pix_fmt yuv420p -g 60 -c:a aac -b:a 128k -ar 44100 \
  -f flv "rtmp://a.rtmp.youtube.com/live2/$YT_KEY"
```

## Free GUI editors (one-off creative edits, India-available)
VN Video Editor, InShot, Instagram Edits, KineMaster (no watermark on manual export). On PC: DaVinci Resolve (free). Export MP4, then drop into the `norm -> concat -> RTMP` pipeline.

## VFR gotcha
CapCut/GUI editors can export **VFR** (variable framerate), which breaks concat. Always normalize (`-vf fps=`) before concatenating — the pipeline's normalize step handles this.
