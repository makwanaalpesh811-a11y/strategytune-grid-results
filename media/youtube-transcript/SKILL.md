---
name: youtube-transcript
version: 1.1
description: "Fetch YouTube transcript safely. No keys, no trade. Short yt.py script + YouTube search via web_search."
---

## Transcript fetch

Library: `youtube_transcript_api` (pip install).

**Use the short script `yt.py` (14 lines):**

```python
import sys, re, json, urllib.request, urllib.parse
from youtube_transcript_api import YouTubeTranscriptApi

vid = sys.argv[1] if len(sys.argv)>1 else "Xnk-fIfyLDU"
try:
    u = "https://www.youtube.com/oembed?url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}") + "&format=json"
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=15) as r:
        print("TITLE:", json.load(r).get("title"))
except Exception as e: print("NO TITLE")
for L in (["hi"],["en"],["hi","en"]):
    try:
        t = list(YouTubeTranscriptApi().fetch(vid, languages=L))
        p = f"{vid}_transcript.txt"
        open(p,"w").write("\n".join(f"[{int(s.start):4d}] {s.text.strip()}" for s in t))
        print(f"OK {len(t)} seg | {t[-1].start+ (t[-1].duration or 0):.0f}s | {p}")
        break
    except Exception as e: print("FAIL",L, type(e).__name__)
```

**Run:** `python3 yt.py VIDEO_ID`  → title + segment count + duration + saved txt.

**Pitfalls (avoid these):**
- `fetch([vid], ...)` — list दिये तो `v=['VID']` बनता है, 400 error। video_id must be single string.
- `list_transcripts()` — current API में नहीं है। सिरफ़ `fetch()` और `list()` हैं。
- पुराना import `from youtube_transcript_api import Transcripts, NoTranscriptFound` fail करता है। Use `YouTubeTranscriptApi` directly.
- Try order: `["hi"]` → `["en"]` → `["hi","en"]`. First one that works wins.

**Example:** `python3 yt.py Xnk-fIfyLDU` → 187 seg, 495s, saved as `Xnk-fIfyLDU_transcript.txt`.

## YouTube search (no browser needed)

`web_search` टूल + `site:youtube.com` operator:

```python
web_search(query="RSI ATR breakout strategy backtest site:youtube.com", limit=5)
```

Gives: title, URL, description, transcript snippets.
Not given: views, likes, thumbnails, comments, full transcript (use this skill for that).

**Full flow:** search (web_search) → link मिलता है → transcript (yt.py) → rules निकालो.

## Safety

- No keys, no trade, no DELTA_MCP_MODE. Transcript only.
- Strategy claims must be verified against full transcript, not just description snippets.
- If rules (entry/exit/SL/TP/fees) not in transcript → "Video में specified नहीं है" — never invent defaults.
