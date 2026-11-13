---
name: chinese-hindi-dubbing
description: Chinese to Hindi dubbing with timestamp sync.
---

# Chinese → Hindi Dubbing

Use this skill whenever a user uploads a Chinese video and requests Hindi dubbing, voice replacement, Hindi subtitles, or audio synchronization.

## Non-negotiable rules

- Treat each Chinese dialogue segment's original `start` and `end` as a timing lock.
- Never generate one long TTS file for the whole video.
- Generate one Hindi audio segment per dialogue thought-group, normally 1–6 seconds.
- Keep one consistent Hindi voice per character throughout the video.
- Never change video speed to solve dialogue timing.
- Use an original voice quality such as `soft, youthful, shy, warm, anime-style`; never claim or imitate an exact copyrighted character or real person's voice.
- Keep product names, numbers, names, intent, and factual meaning accurate.
- Run the sample-first voice quality gate in `references/voice_quality.md` before batch generation.

## Workflow

### 1. Inspect and transcribe

Run `ffprobe` on the input video and record duration, dimensions, frame rate, audio streams, sample rate, and channels. Transcribe Chinese speech with timestamps. Keep, for every segment: `id`, `start`, `end`, `speaker`, Chinese text, and confidence. Split long ASR blocks at pauses, punctuation, and speaker changes. If timestamps look unreliable, use VAD or forced alignment before generating TTS. Reject invalid or unexplained timestamp gaps before TTS.

### 2. Adapt the Hindi script

Create a timing table:

`id | start | end | slot | speaker | Chinese | natural Hindi | target duration`

Translate for natural spoken Hindi, not word-for-word subtitles. Fit the Hindi wording to `slot = end - start`. Rewrite a line shorter before using speed adjustment. Do not add explanations, labels, or stage directions to spoken TTS text.

### 3. Voice quality gate

Read `references/voice_quality.md`. Generate one 8–10 second sample with the intended expressive Hindi voice and wait for user approval before generating the full batch. Do not use gTTS or flat/offline robotic TTS for final expressive dubbing. If no suitable expressive Hindi voice is available, stop after the sample and report the limitation.

### 4. Generate segment audio

Generate each segment separately with the same voice for the same speaker. Use `language_code: hi-IN`. Put only words to be spoken in the TTS transcript; put delivery directions in the style field. Measure each returned WAV with `ffprobe`.

### 5. Fit audio to its source slot

For every segment:

```text
slot = source_end - source_start
actual = measured_audio_duration

if actual <= slot:
    keep natural speed and place at source_start
elif actual > slot:
    rewrite Hindi shorter and regenerate
    if still slightly long, use pitch-preserving FFmpeg atempo
    keep normal fit ratios between 0.92 and 1.08 when possible
    never exceed 0.85–1.15 without another rewrite and a sync-risk flag
```

If a line is shorter than its slot, leave the remaining time as natural silence. Do not stretch a short line unnaturally. Place every fitted segment at its exact source start; never allow it to leak into the next segment.

### 5. Preserve the video and assemble audio

Preserve the original video stream, dimensions, frame rate, and duration. If the original audio has separable ambience/music, duck or mute Chinese dialogue while retaining ambience and effects. If it cannot be separated, retain the source at very low volume only when it does not compete with Hindi; otherwise replace it and document the choice.

Use the bundled `scripts/assemble_timeline.py` when segment WAVs and a JSON timing manifest are available. It creates a full-length Hindi timeline, places audio at timestamps, applies only mild `atempo` corrections, mixes optional low-level ambience, and writes a QC manifest.

### 6. Subtitles and output

Create Hindi subtitles using the same source timestamps as the fitted dialogue. Keep subtitles readable and split long lines into at most two lines. Always deliver:

- `dubbed_hindi.mp4`
- `dubbed_hindi.srt`
- `dub_manifest.json`
- `sync_report.txt`

### 7. Quality control

Before delivery:

- Verify every segment starts within 50 ms of its source start.
- Verify every segment ends no later than source end + 50 ms.
- Check that no dialogue segments overlap unexpectedly.
- Listen to pronunciation, names, numbers, emotion, pauses, and loudness.
- Watch/listen at the beginning, a dense middle section, and the ending.
- Run `ffprobe` on the final MP4 and confirm it is playable, has the expected duration, video stream, and audio stream.
- Mark difficult cases as `sync_risk`: overlapping speakers, music masking, unreliable ASR, very short slots, or visible lips that do not match Hindi phonemes.

## Error recovery

If a segment is too long, regenerate only that segment with shorter Hindi wording. If TTS fails, retry the same segment with the same voice. Do not regenerate the entire video for one bad segment. If original dialogue cannot be removed without artifacts, explain that timing sync is complete but the source speech may remain faintly audible. Audio timing sync does not guarantee phoneme-level mouth/lip sync; use a dedicated lip-sync model after the fitted Hindi track when requested.

## Bundled resources

- Read `references/timing_and_ffmpeg.md` for timing math, FFmpeg patterns, and manifest schema.
- Run `scripts/assemble_timeline.py --help` for deterministic timeline assembly.
