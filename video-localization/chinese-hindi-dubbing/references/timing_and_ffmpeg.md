# Timing and FFmpeg Reference

## Timing math

For each source segment, calculate `slot = source_end - source_start`. Generate and measure a WAV, then compare `actual_duration` with `slot`. Place it at `source_start`; the audio must end no later than `source_end + 0.05` seconds. If it is long, rewrite the Hindi first. Use mild pitch-preserving `atempo` only as a fallback.

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 segment.wav
ffmpeg -y -i segment.wav -filter:a "atempo=1.04" segment_fit.wav
```

For ratios outside 0.85–1.15, regenerate with shorter or more complete Hindi wording instead of making robotic speech.

## Input inspection

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels -of json input.mp4
```

## Manifest schema

```json
[
  {
    "id": 1,
    "source_start": 0.10,
    "source_end": 10.70,
    "speaker": "speaker_1",
    "text": "बोली जाने वाली हिंदी line",
    "audio_file": "/absolute/path/to/segment_01.wav",
    "measured_duration": 10.52,
    "fit_ratio": 1.0,
    "qc": "pass"
  }
]
```

## Assembly

Use the bundled script:

```bash
python3 scripts/assemble_timeline.py \
  --video source.mp4 \
  --manifest dub_manifest.json \
  --output dubbed_hindi.mp4 \
  --original-volume 0.08
```

The script keeps the source video stream, places each Hindi WAV on the timestamp timeline, mixes low-level original audio as optional ambience, and encodes the result as AAC. If original Chinese speech remains distracting, set `--original-volume 0` and document that original ambience was removed.

## Subtitles

Use source segment timestamps for Hindi SRT. Keep each subtitle readable, normally no more than two lines. Subtitle timing should follow the fitted audio, not a newly guessed translation timing.

## Limitations

Timestamp-locked dubbing fixes when speech plays, not phoneme-level mouth movement. If the face is visible and exact lip movement is required, run a dedicated lip-sync stage after creating the fitted Hindi track. If the original audio is a single mixed track, perfect Chinese speech removal may introduce artifacts; report this honestly.
