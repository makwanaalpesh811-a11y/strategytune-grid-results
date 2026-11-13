# Master Agent Prompt: Chinese Video → Hindi Dub

इस skill को हर Chinese-to-Hindi dubbing task में अनिवार्य workflow की तरह follow करो। User का Chinese video upload होते ही बिना अनावश्यक confirmation के यह पूरा process चलाओ।

## काम
Chinese video की speech को natural Hindi में dub करो। Audio timing को original Chinese dialogue के timestamps के अंदर lock रखो। Video की speed, frame rate और visual duration मत बदलो।

## अनिवार्य workflow

1. `ffprobe` से input video की duration, resolution, FPS, audio stream, sample rate और channels inspect करो।
2. Chinese speech को timestamped ASR से transcribe करो। हर segment के लिए `id`, `start`, `end`, `speaker`, Chinese text और confidence रखो।
3. Long ASR blocks को pause, punctuation और speaker change पर छोटे thought-groups में बाँटो। सामान्यतः segment 1–6 seconds का रखो।
4. Timing table बनाओ: `id | start | end | slot | speaker | Chinese | natural Hindi | target duration`.
5. Natural spoken Hindi translation बनाओ। Names, numbers, brands, meaning और intent न बदलो। Translation को source slot में बोलने योग्य रखो।
6. पूरे video के लिए एक लंबा TTS audio कभी मत बनाओ। हर segment की अलग Hindi TTS audio बनाओ। एक speaker/character के लिए वही voice पूरे video में reuse करो। Hindi के लिए `hi-IN` रखो।
7. Voice style original रखो, जैसे `soft, youthful, shy, warm, anime-style`, लेकिन किसी copyrighted character या real person की exact/cloned voice मत बनाओ।
8. हर WAV की actual duration `ffprobe` से मापो।

## Timing lock

हर segment के लिए:

```text
slot = source_end - source_start
actual = measured_audio_duration
```

- अगर `actual <= slot`, audio को natural speed पर `source_start` पर रखो और बचा समय silence रहने दो।
- अगर `actual > slot`, पहले Hindi translation छोटा करके TTS दोबारा बनाओ।
- फिर भी थोड़ा लंबा हो तो pitch बदले बिना हल्का FFmpeg `atempo` लगाओ। सामान्य ratio 0.92–1.08 रखो। 0.85–1.15 से बाहर जाने पर translation फिर से rewrite करो और `sync_risk` flag करो।
- कोई audio अगली line के ऊपर overlap या `source_end` के बाद leak नहीं होना चाहिए।
- Video की speed बदलकर sync ठीक मत करो।

## Audio assembly

हर fitted Hindi WAV को exact original start timestamp पर timeline में रखो। Original background music और ambience बचाने की कोशिश करो। Chinese speech अलग track में हो तो mute/duck करो। अगर source audio mixed है और Chinese speech साफ अलग नहीं हो सकती, तो original audio को बहुत low volume पर रखो या replace करो और report में बताओ। Hindi voice main audio होनी चाहिए।

Bundled `scripts/assemble_timeline.py` का उपयोग करके final audio timeline बनाओ जब manifest और segment WAV उपलब्ध हों।

## Subtitles और deliverables

Hindi subtitles वही text और original timestamps के साथ बनाओ। Final output में हमेशा यह files दो:

- `dubbed_hindi.mp4`
- `dubbed_hindi.srt`
- `dub_manifest.json`
- `sync_report.txt`

## Final QC

Delivery से पहले:

- हर segment का start source start से ±50 ms के अंदर हो।
- हर segment source end +50 ms से आगे न जाए।
- Unexpected overlap या audio leak न हो।
- शुरुआत, dense middle और ending पर video+audio साथ check करो।
- Pronunciation, names, numbers, emotion, pauses और loudness check करो।
- `ffprobe` से final MP4 की duration, video stream, audio stream और playability verify करो।
- Overlapping speech, music masking, unreliable timestamps, बहुत छोटे slots और visible lips mismatch को `sync_risk` में लिखो।

## Error recovery

एक segment में problem हो तो पूरा video regenerate मत करो। केवल affected segment को shorter Hindi wording के साथ regenerate करो, timeline update करो, manifest और report update करो। Audio timestamp sync और phoneme-level lip-sync अलग चीजें हैं; lips बदलने के लिए fitted Hindi track के बाद dedicated lip-sync tool चलाओ, अगर उपलब्ध हो।
