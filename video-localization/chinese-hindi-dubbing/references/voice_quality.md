# Voice Quality and Natural Hindi TTS

## Required voice quality

Use one expressive native Hindi female voice for the entire character. Preferred qualities: youthful, soft, warm, gentle, slightly high pitch, clear Hindi pronunciation, shy but expressive, natural breathing, natural pauses, and emotional variation. Use an original anime-inspired quality only; do not imitate an exact copyrighted character or real person.

Recommended style string:

```text
soft, youthful, shy, warm and expressive Hindi anime-inspired delivery; natural breathing, gentle pauses, clear pronunciation, emotional variation, not robotic, not monotone, not rushed
```

Keep `style` separate from spoken `text`. Never put instructions such as "speak like Hinata" inside the spoken transcript.

## Forbidden final engines

Do not use gTTS or a flat/offline robotic TTS for final expressive dubbing. They may be used only for a technical timing test when the user explicitly accepts low quality. If no expressive Hindi voice is available, stop after a sample and report the limitation instead of generating dozens of bad segments.

## Sample-first quality gate

Before generating the full batch, generate one 8–10 second Hindi sample:

```text
उम... मैंने तुम्हारे लिए कुछ बनाया है। अगर तुम्हें अच्छा लगे, तो इसे रख लेना... ठीक है?
```

Use the same voice, language code `hi-IN`, and the intended style. Check:

- natural or robotic sound
- clear Hindi pronunciation
- natural pauses and breathing
- emotional variation
- no rushed or flat delivery
- no unwanted spoken instructions

Do not generate the remaining segments until the sample is approved or the user explicitly accepts the limitation.

## TTS request pattern

```json
{
  "language_code": "hi-IN",
  "voice_name": "Leda",
  "turns": [
    {
      "text": "उम... मैंने तुम्हारे लिए कुछ बनाया है। अगर तुम्हें अच्छा लगे, तो इसे रख लेना... ठीक है?",
      "style": "soft, shy, youthful, warm and expressive; natural pauses and gentle emotional variation"
    }
  ]
}
```

Reuse the exact same `voice_name` for every segment of the same character.

## Timing decision code

```python
def decide_audio_fit(actual_duration, source_start, source_end):
    slot = source_end - source_start
    if slot <= 0:
        return {"decision": "skip", "reason": "invalid_slot"}
    ratio = actual_duration / slot
    if ratio <= 1.00:
        return {"decision": "natural", "ratio": ratio}
    if ratio <= 1.08:
        return {"decision": "fit_atempo", "atempo": ratio}
    if ratio <= 1.15:
        return {"decision": "fit_atempo", "atempo": ratio, "sync_risk": True}
    return {"decision": "rewrite", "reason": "too_long", "ratio": ratio}
```
