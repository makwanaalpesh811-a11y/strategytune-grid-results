# Voice Cloning for Anime-Character Hindi Dub

Use when the user wants a specific character's REAL voice (not synthetic) speaking Hindi. On Termux this is impossible (no CUDA, torch OOM) — the path is Google Colab with a T4 GPU.

## What actually works (free Colab T4, ranked)

1. **Chatterbox Multilingual V3 / Hindi pack** (0.5B, MIT, zero-shot, T4-friendly) — simplest, clone from 6-10s reference.
2. **XTTS v2 via `coqui-tts`** (not `TTS`) — most documented, Hindi supported, accepts 6s ref (truncates >12s). Weights are CPML non-commercial.
3. **IndicF5** (0.35B, MIT, native Hindi) — needs ref transcript.
4. **Two-stage:** native Hindi TTS → **Seed-VC v1** (best timbre; v2 also converts accent, avoid for Hindi).

## Wrong tools
- **RVC / so-vits-svc / Fish Audio** = voice CONVERSION, not TTS. Need a Hindi source track; <1 min can't train. RVC FAQ: 5-10 min clean is the floor, 10-30 min recommended. A 6.8s sample cannot train.
- **VoxCPM2 / Qwen3-TTS**: possible but not turnkey for Hindi (Qwen3-TTS officially 10 langs, NOT Hindi; VoxCPM2 issue #288 = unintelligible with non-Japanese ref).

## Reference prep (make-or-break)
- Use only clean speech segments. A song/chewing section is unusable as ref.
- If BGM present: Demucs `--two-stems=vocals` or UVR5 first.
- Then mono, 24kHz, trim silence, normalise ~-23 LUFS, no reverb/EQ.
- 6-10s is minimum; 15-30s of clean dialogue improves similarity noticeably.

## Chatterbox exact recipe
```python
!pip install -q chatterbox-tts
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
model = ChatterboxMultilingualTTS.from_pretrained(device='cuda')
wav = model.generate(
    text=hindi_line, language_id='hi',
    audio_prompt_path='hinata_ref.wav',
    exaggeration=0.5, cfg_weight=0.5, temperature=0.8)
import soundfile as sf
sf.write('seg.wav', wav.squeeze().cpu().numpy(), 24000)
```
Generate ONE sentence at a time (≤300 chars), fixed seed, 24kHz output. Optionally load the `Chatterbox-Multilingual-hi` pack for tighter Hindi. Concat all segs with ffmpeg concat.

## Assembly to final video
- Translate to SHORT Hindi lines (Hindi runs ~10-20% longer than source).
- Per sentence, keep best of 2-4 takes.
- Fit with `atempo` 0.95-1.10 (never >1.15 or it artefacts).
- Duck original BGM -12 to -18dB under dialogue; keep ending song if wanted.
- 100-200ms fades; master -14 LUFS for Instagram.

## Realistic expectation
- 6.8s reference → **~60-75% speaker similarity**: same timbre family, not indistinguishable. Prosody/accent/cries/singing are the model's, not the actress's.
- This yields a good AI fan-dub, NOT a seamless original performance.
- Legal: cloning a real actress's character voice needs permission/labelling for public/monetised use; XTTS (CPML) and Fish (CC-BY-NC-SA) are non-commercial; Chatterbox/IndicF5/VoxCPM2/Qwen3 are MIT/Apache.

## Notebook location (this session's artifact)
`~/Hinata_Voice_Clone_Chatterbox.ipynb` — full 7-cell notebook: install, upload ref, load model, Hindi lines array, generate per-line, concat+export, preview. Ref: `~/hinata_ref.wav` (6.8s clean).
