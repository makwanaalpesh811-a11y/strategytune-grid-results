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
