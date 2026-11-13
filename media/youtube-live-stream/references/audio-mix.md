# Audio Mixing (ffmpeg, Termux)

Two tracks ko mix karne ka recipe — `-stream_loop` aur AAC encoder dono Termux ke ffmpeg me unreliable hain. Ye WAV-based path verified hai.

## Why this path

- `-stream_loop -1 -i input.mp3` → `Conversion failed!` / 0-byte output. **mp3/m4a loop pe kaam nahi karta.**
- `amix`/`amerge` with AAC out (`-c:a aac -b:a 192k`) → `Qavg: nan` + `Conversion failed!`. **AAC encoder m4a/mp3 mixed input pe fail.**
- Do reliable workaround: (1) loop karne ke liye WAV convert karo, (2) mix output bhi WAV me, (3) final `libmp3lame` se MP3.

## Steps (verified)

```bash
# 1. Both sources -> WAV (loop works on WAV)
ffmpeg -y -i main.mp3 -c:a pcm_s16le main.wav
ffmpeg -y -stream_loop -1 -i overlay.mp3 -t <dur> -c:a pcm_s16le overlay_loop.wav

# 2. Mix (WAV -> WAV)
ffmpeg -y -i main.wav -i overlay_loop.wav \
  -filter_complex "[0:a]volume=0.7[a];[1:a]volume=0.3[b];[a][b]amix=inputs=2:duration=first[out]" \
  -map "[out]" -c:a pcm_s16le mix.wav

# 3. Final MP3 (libmp3lame, NOT aac)
ffmpeg -y -i mix.wav -c:a libmp3lame -b:a 192k mix.mp3
```

## Rules

- **Loop = WAV first.** `-stream_loop` is only reliable on WAV/PCM input on Termux ffmpeg.
- **AAC out = fail on mixed sources.** Use `libmp3lame` for the final encode (MP3), or PCM intermediate.
- **Volume balance:** main `0.7`, overlay `0.3` is a sane start; user adjusts.
- **`duration=first`** in amix = main track's length wins; `-t <dur>` on the loop caps overlay length.
- ffprobe output for `duration` before mixing so `-t` is exact.

## Pitfall

- ffprobe/ffmpeg `-t` accepts float seconds; get it with `ffprobe -v error -show_entries format=duration -of csv=p=0 input`.
- 0-byte output + "Failed to find two consecutive MPEG audio frames" on a subsequent ffprobe = previous step silently failed; check exit code of EACH step, don't chain with `&&` blindly.
