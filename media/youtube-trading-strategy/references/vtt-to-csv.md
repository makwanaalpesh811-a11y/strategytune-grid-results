# VTT → Clean CSV Transcript Extractor

Use when user asks for transcripts as CSV ("transcript do CSV me"). Termux Python, no extra deps.

## Why this recipe exists

YouTube VTT auto-captions repeat text cumulatively: each cue contains ALL text said so far, plus the new segment. Naive extract produces 3x duplicates. Also, timestamps come as `HH:MM:SS.mmm` OR `MM:SS.mmm` depending on total duration.

## Working Recipe (tested on 3 HFT videos, ~5000 cues total)

```python
import re, csv
from pathlib import Path

def parse_ts(ts_str):
    m = re.search(r'(\d+):(\d+):(\d+)\.(\d+)', ts_str)
    if m:
        h, mn, s, ms = m.groups()
        return int(h)*3600000 + int(mn)*60000 + int(s)*1000 + int(ms)
    m = re.search(r'(\d+):(\d+)\.(\d+)', ts_str)
    if m:
        mn, s, ms = m.groups()
        return int(mn)*60000 + int(s)*1000 + int(ms)
    return None

def fmt_ts(ms):
    s = ms // 1000
    return f"{s//60:02d}:{s%60:02d}.{ms%1000:03d}"

def clean_vtt(vtt_path, csv_path, meta):
    txt = Path(vtt_path).read_text(errors='ignore')
    cues = []
    start_ms = end_ms = None
    current_text = []
    for line in txt.split('\n'):
        if line.startswith(('WEBVTT','NOTE','Kind:','Language:','STYLE','REGION','COUNT')):
            continue
        if '-->' in line:
            if start_ms is not None and current_text:
                t = ' '.join(l.strip() for l in current_text if l.strip())
                t = re.sub(r'<[^>]+>', '', t).strip()
                if t: cues.append((start_ms, end_ms, t))
            parts = line.split('-->', 1)
            start_ms, end_ms = parse_ts(parts[0]), parse_ts(parts[1])
            current_text = []
            continue
        line = line.strip()
        if not line or line.startswith(('align:','position:')): continue
        line = re.sub(r'<[^>]+>', '', line).strip()
        if line: current_text.append(line)
    if start_ms is not None and current_text:
        t = ' '.join(l for l in current_text if l.strip())
        if t: cues.append((start_ms, end_ms, t))
    
    # Remove cumulative prefix — each cue contains all prior text
    deduped = []
    prev_full = ""
    for s, e, t in cues:
        if prev_full and t.startswith(prev_full):
            t = t[len(prev_full):].strip()
        if t:
            deduped.append((s, e, t))
            prev_full = t
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['index','video_id','video_title','channel',
                     'start_time','end_time','start_ms','end_ms','text'])
        for i, (s, e, t) in enumerate(deduped):
            w.writerow([i+1, meta['id'], meta['title'], meta['channel'],
                        fmt_ts(s), fmt_ts(e), s, e, t])
    return len(deduped)
```

## CSV Schema

`index, video_id, video_title, channel, start_time, end_time, start_ms, end_ms, text`

- `start_time`/`end_time`: `MM:SS.mmm` (human readable)
- `start_ms`/`end_ms`: integer ms (machine sortable)
- `text`: deduplicated new sentence for this cue

## Pitfalls

- **Skip `t == prev` dedup alone** — that only removes consecutive exact duplicates, not cumulative prefixes. Must strip prior text.
- **`t.startswith(prev_full)` check** handles VTT's cumulative pattern: each new cue repeats all previously-spoken text plus new words. Strip the prefix, keep only the delta.
- **Rolling `prev_full = t`** after each strip — not `prev_full = prev_full + t` — because we only track the last sentence to catch the next overlap.
- **Timestamp regex must try `HH:MM:SS.mmm` first, then `MM:SS.mmm`** — videos >1h use the long form, short ones use short.
- **Strip VTT inline tags `<c>...</c>`** — they're word-level highlight spans, not content.
- **Skip lines starting with `align:` or `position:`** — they're cue-level styling metadata.
- Save to `~/Hermes_Almari/02_DATA/hft_transcripts/<vid>.csv` for multi-video work.

## Sanity Check

- 8-min video → ~180-200 unique cues
- 30-min video → ~700-800 unique cues  
- 73-min video → ~1700-1800 unique cues

If you get 5x+ that, your dedup is broken (VTT cumulative repetition still leaking).
