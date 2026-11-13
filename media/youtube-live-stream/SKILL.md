---
name: youtube-live-stream
description: Stream a live trading dashboard to YouTube via ffmpeg RTMP.
---

# YouTube Live Stream — Data Dashboard via ffmpeg RTMP

Stream a live-rendered dashboard (market/trading data) to YouTube Live without screen capture or ADB. Frames are rendered in Python from live API/WebSocket data, piped to ffmpeg, pushed to YouTube RTMP.

## Primary script: ~/delta_dash_live.py (user-designed)

Delta-Exchange-style terminal dashboard (ETHUSD default). Pure stdlib (no numpy/matplotlib) + ffmpeg for text rendering. Env-configured, ~1008 lines.

## Env vars (all optional but functional gates)

| Var | Meaning | Where it comes from |
|---|---|---|
| `DELTA_KEY` | Delta Exchange API key | `~/.delta-exchange-mcp/config.env` → `DELTA_API_KEY` |
| `DELTA_SECRET` | Delta Exchange API secret | `~/.delta-exchange-mcp/config.env` → `DELTA_API_SECRET` |
| `YT_KEY` | YouTube RTMP **stream key** (NOT the OAuth token) | YouTube Studio → Create → Go Live |
| `SYM` | Symbol (default ETHUSD) | — |
| `TF` | Timeframe (default 15m) | — |
| `USDINR` | INR rate; `₹` shown when >0 | — |
| `FPS`/`OUTFPS` | Render/encode fps (5/15 default) | — |
| `VBR`/`PRESET` | bitrate / x264 preset (6000k / veryfast) | — |

Load Delta keys from config.env before running:
```bash
export DELTA_KEY=$(grep '^DELTA_API_KEY=' ~/.delta-exchange-mcp/config.env | cut -d= -f2-)
export DELTA_SECRET=$(grep '^DELTA_API_SECRET=' ~/.delta-exchange-mcp/config.env | cut -d= -f2-)
```

## Two run modes (decided by YT_KEY presence)

```bash
# TEST mode — no YT_KEY: renders 60s to test.flv, real Delta data, exits
python3 delta_dash_live.py

# LIVE mode — YT_KEY set: pushes to rtmp://a.rtmp.youtube.com/live2/<YT_KEY>
YT_KEY=<stream-key> python3 delta_dash_live.py
```

Test mode is the verification gate: `test.flv` ~6.3MB / ~60s with real data means Delta keys + ffmpeg render pipeline work. Extract a frame to preview:
```bash
ffmpeg -y -v error -ss 50 -i test.flv -frames:v 1 dashboard_preview.png
```

## Live prerequisites (exact checklist)

1. **Delta keys** — `DELTA_API_KEY`/`DELTA_API_SECRET` in `~/.delta-exchange-mcp/config.env` (read-only key gives positions/account too).
2. **ffmpeg** installed.
3. **YouTube OAuth token** valid for the target channel (`~/.yt_token.json`, refreshable). Without a live token, YT APIs fail with 400/401.
4. **Live broadcast created in Studio first** — the script only RTMP-pushes; it does NOT create the broadcast. Stream key comes from Create → Go Live.

## Fonts

- Regular: `/system/fonts/Roboto-Regular.ttf` (exists).
- Bold: no `/system/fonts/Roboto-Bold.ttf` on this device — use `DroidSans-Bold.ttf` fallback if `FONTB` unset fails.

## Background music

Copyright rule (hard): only **CC0 / royalty-free** tracks. A copyrighted song — even an instrumental/no-vocal version of it — matches Content ID by melody and risks a live block or strike. "Making a BGM of someone's song" does NOT clear copyright. Use only royalty-free sources (YouTube Audio Library, Pixabay, incompetech CC, Free Music Archive).

Download a CC0 track with yt-dlp:
```bash
yt-dlp -f 'bestaudio[ext=m4a]/bestaudio' --no-playlist -o bgm.mp3 '<cc-video-url>'
```
Verify with `ffprobe` (valid duration/sample-rate) before use.

**Two-track mix** (e.g. On My Way + Bella Ciao) → `references/audio-mix.md` (WAV-first + libmp3lame recipe; `-stream_loop` and AAC both fail on mixed mp3 sources).

**Live-pipeline BGM loop (delta_dash_live.py):** ffmpeg cmd me `-f lavfi -i anullsrc=r=44100:cl=stereo` ko `-stream_loop -1 -i <abs-path>/mix.mp3` se replace karo (~line 962). `-stream_loop -1` single mp3 as direct ffmpeg input works (live RTMP push verified) — mix file pehle se ready honi chahiye (WAV-first recipe). Script me hardcoded `~/mix.mp3` path mat dalo; env var ya `os.path.expanduser` use karo.

## Full API-based live workflow (verified 2026-11-04)

The Studio-first approach works, but the API path below is fully verified end-to-end on this device (Radhe Krishna channel, 520 subs) and avoids manual Studio steps. Steps in order:

### 1. Refresh access token
```python
# ~/.yt_token.json = {access_token, refresh_token, client_id, client_secret, ...}
tok = json.load(open(os.path.expanduser('~/.yt_token.json')))
# POST https://oauth2.googleapis.com/token with client_id, client_secret, refresh_token, grant_type=refresh_token
# -> new access_token (expires 3599s, auto-refresh)
```

### 2. Get or reuse a live stream
```python
# GET https://www.googleapis.com/youtube/v3/liveStreams?part=snippet,cdn,status&mine=true&maxResults=50
# pick one with status.streamStatus; ingest key = cdn.ingestionInfo.streamName
# Stream key (RTMP suffix) = that streamName, e.g. 'd7q6-dmtd-9qt7-urya-bae7'
# RTMP URL = cdn.ingestionInfo.ingestionAddress + '/' + streamName
```

### 3. Create broadcast with enableAutoStart=True
```python
# POST /liveBroadcasts?part=snippet,status,contentDetails
# body = {
#   'snippet': {'title': '...', 'scheduledStartTime': now_iso},
#   'status': {'privacyStatus': 'unlisted', 'selfDeclaredMadeForKids': False},
#   'contentDetails': {'enableAutoStart': True, 'enableAutoStop': True, 'enableDvr': True,
#     'enableEmbed': True, 'enableContentEncryption': False, 'enableLowLatency': False,
#     'projection': 'rectangular', 'latencyPreference': 'normal',
#     'monitorStream': {'enableMonitorStream': True, 'broadcastStreamDelayMs': 0}}
# }
# **enableAutoStart MUST be set at create time** — it cannot be modified later (403 'Modification of enableAutoStart is not allowed').
# scheduledStartTime is required (400 otherwise).
```

**Create response shape — check BOTH `items` and top-level `id`.** `POST /liveBroadcasts` sometimes returns `{"items":[...]}`, sometimes the raw broadcast object (`{"kind","id","snippet",...}` with NO `items` key). Checking only `items[0]` and treating empty as failure wrongly reports "CREATE FAIL" while the broadcast was actually created (a top-level `id` is present). Success check: `items[0].id` OR `resp.get("id")`. On an ambiguous response, GET `/liveBroadcasts?part=id,status&mine=true&maxResults=5` and pick the newest `created`/`ready` broadcast before binding — never re-POST blindly (each POST creates a new orphan broadcast). Persist the live state (broadcast_id, stream_id, stream_key) to a JSON file so restart/recovery reuses the bound pair instead of re-querying.

### 4. Bind stream to broadcast
```bash
curl -X POST 'https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?part=snippet,status,contentDetails&id=<BID>&streamId=<SID>'
# body can be empty (data=b''); returns status.ready + boundStreamId
```

### 4b. Upload custom thumbnail (multipart, no requests lib)
```python
# POST https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=<BID>
# Content-Type: multipart/form-data; boundary=<boundary>
# field name = 'thumbnail', filename='thumbnail.jpg', Content-Type: image/jpeg
# body = --<b>\r\nContent-Disposition: form-data; name="thumbnail"; filename="thumbnail.jpg"\r\nContent-Type: image/jpeg\r\n\r\n<JPEG bytes>\r\n--<b>--\r\n
# Response: items[0].default.url = https://i.ytimg.com/vi/<BID>/default.jpg  (204/200 = success)
```
Thumbnail upload broadcast `ready` pe hota hai (live hone ke baad bhi chalta hai). 1280x720 JPG standard; reference image ko seedha use karo, naya design mat banao jab user "yehi use hoga" bole.

User convention: thumbnail `Live_Strategy_N_thumbnail.jpg` me `01_STRATEGY/docs/` ke saath save hoti hai — reference image wahi se upload karo.

### 5. Start pushing RTMP (this triggers autoStart → lifeCycleStatus live)
```bash
# With enableAutoStart=True, YouTube transitions ready->live by itself once the stream is active+healthy.
# No manual transition needed. (Manual transition gives 403 'Invalid transition' / 'Stream is inactive' until data flows.)
```

### 6. Make public (optional)
```python
# PUT /liveBroadcasts?part=status  body={'id':BID,'status':{'privacyStatus':'public','selfDeclaredMadeForKids':False}}
# Allowed while live.
```
Setting `privacyStatus: 'public'` directly in the step-3 create body also works (verified 2026-11-05) — the broadcast comes up `live` + `public` without a separate PUT. Use the create-time field when you know it's going public; use the PUT only when flipping unlisted→public after the stream is already live.

### 7. User convention: save the strategy doc
After a verified live run, the user expects a numbered strategy file in the almari docs folder:
```
/sdcard/Hermes_Almari/01_STRATEGY/docs/Live_Strategy_N.md
```
Follow the `Live_Strategy_1.md` shape: Overview (script, data, destination, bitrate) → Flow (7 steps) → Setup commands → Settings table → Issues fixed → Pitfalls. Number increments per new live strategy; overwrite the same N only when fixing that strategy. This is the user's standing convention, not optional — they call it out by name ("Live Strategy 1 ki file banao").

### 7. Stop + delete
```bash
# kill the ffmpeg/python processes, then:
# POST /liveBroadcasts/transition?broadcastStatus=complete&id=<BID>  body={'id':BID,'status':{'lifeCycleStatus':'complete'}}
# DELETE /liveBroadcasts?id=<BID>  (204 = success)
```

**Full stop + delete (verified 2026-11-04):**
```python
# 1. kill stream processes
# 2. GET /liveBroadcasts?part=snippet,status&mine=true&maxResults=50 -> active = lifeCycleStatus in (live,liveStarting,ready,created)
# 3. for each active id:
#    POST /liveBroadcasts/transition?part=status&id=<BID>&broadcastStatus=complete  (403 Forbidden ok — some already complete)
#    DELETE /liveBroadcasts?id=<BID>  (204 = success)
# 4. verify: GET again -> active count 0
```

## Dashboard P/L fix — must match Delta app (verified 2026-11-06)

User convention: dashboard me position data **Delta app jaisa hi** dikhna chahiye — entry price, app-match percentage, asli (close-able) P/L. API ke `unrealized_pnl` field pe **bharosa mat karo** — wo mark-price se hota hai (galat direction + galat magnitude).

**Three bugs found + fixed in `delta_dash_live.py`:**

1. **Entry price display** — dashboard me `q["off"]` (current bid/ask) dikha raha tha; fix = `q["en"]` (entry_price). Position card me **entry price** dikhna chahiye, current mark nahi.
2. **Contract value** — ETH options ka `contract_value = 0.01` (0.01 ETH/lot), `1.0` nahi. Ticker se lo, `None`/missing ho to **0.01** fallback (`float(tk.get("contract_value") or 0.01)`). Galat `cv=1.0` se P/L 100x bada aata hai.
3. **UPL + percentage formula (app-match):**
   - `off = bid if sz > 0 else ask` (short → ask)
   - `upo = (en - off) * sz * cv`  (short ke liye (entry-offer) direction)
   - `pct = (en - off) / en * 100`
   - `tot += upo` (offer-based total, NOT API `unrealized_pnl`)

**Verify:** fresh data pe `python3 -c` se app screenshot ke % se compare karo (P-ETH/C-ETH % match). App +28/-32 type % aata hai, margin-based 14-15% galat hai.

**User preference (verbatim):** "Dono me difference bahut hai percentage pogishan profit me" → dashboard ko app se exact match karna hai. "Data jaisa aa raha hai wahi dikhao" → fabricated/reinvented data kabhi nahi, jo API de raha hai wahi render karo.

## Delta API 401 fix (verified 2026-11-05)

Live dashboard me `bal: HTTP Error 401` / `pos: HTTP Error 401` = Delta API signature issue. **ROOT CAUSE + FIX (2026-11-05):**

1. **India API** — key India ke liye hai. Base URL = `https://api.india.delta.exchange` (global `api.delta.exchange` = `invalid_api_key`). Script line 10 pehle se India API.
2. **Timestamp = SECONDS** — Delta India API **seconds** expect karta hai, milliseconds nahi. Script me `ts = str(int(time.time()))` (line ~184). **Milliseconds = `expired_signature`!**
3. **Signature format** — `HMAC-SHA256(secret, "GET" + ts + path)` (path me `/v2/` prefix included).
4. **Secret 60 chars, key 30 chars** — sahi length chahiye (corrupt 3 chars = fail).

**Verified:** `BALANCE OK: 7 balances` with India API + seconds. Secret 60 chars correct.

**Diagnostic (quick):**
```bash
python3 -c """
import json, os, re, time, hmac, hashlib, urllib.request
cfg=open(os.path.expanduser('~/.delta-exchange-mcp/config.env')).read()
key=re.search(r'^DELTA_API_KEY=(.+)$',cfg,re.M).group(1).strip()
sec=re.search(r'^DELTA_API_SECRET=(.+)$',cfg,re.M).group(1).strip()
ts=str(int(time.time())); path='/v2/wallet/balances'
sig=hmac.new(sec.encode(), ('GET'+ts+path).encode(), hashlib.sha256).hexdigest()
req=urllib.request.Request('https://api.india.delta.exchange'+path, headers={'api-key':key,'timestamp':ts,'signature':sig})
try:
    r=json.load(urllib.request.urlopen(req)); print('BALANCE OK:', len(r.get('result',[])))
except Exception as e: print('401:', str(e)[:80])
"""
```

**Pitfall (error-code → cause):** `/v2/time` endpoint 404 deta hai — server time error response context me milta hai. `expired_signature` = timestamp galat (ms) ya secret galat. `invalid_api_key` = galat base URL (global vs India). **`ip_not_whitelisted_for_api_key` = key ke liye IP whitelist nahi kiya.**

**IP whitelist fix (mobile device):**

`ip_not_whitelisted_for_api_key` tab aata hai jab API key pe restrict IPs set hain aur device ka current IP whitelist me nahi. Mobile network IP har baar badalta hai (IPv4 + IPv6 dono), isliye:

1. Delta Exchange India (`india.delta.exchange`) → login → **Profile → API Keys** → us key pe edit.
2. IP whitelist me **`0.0.0.0/0`** add karo (sab IP allow — mobile ke liye zaroori, warna har network change pe 401).
3. Save → verify: `python3 -c "..."` (upar diagnostic) → `BALANCE OK`.

Current IP nikaalne ke liye: `curl -s https://api.ipify.org` (IPv4) + `curl -s https://api64.ipify.org` (IPv6).

**Diagnostic sequence (401 dekhne pe, is order me):**
1. `invalid_api_key` → base URL check: `https://api.india.delta.exchange` hona chahiye (global = galat key).
2. `expired_signature` → timestamp SECONDS me chahiye (ms nahi); phir secret length 60.
3. `ip_not_whitelisted_for_api_key` → upar IP whitelist fix.

Ye teen alag root causes hain — ek 401 ke teen possible reasons. Is order me diagnose karo, ek-ek ko cross karo.

## Network/bitrate tuning (critical on mobile)

Mobile uplink is the binding constraint. Measured on this device (Nov 2026): upload ~90-110 KB/s ≈ **0.7-0.9 Mbps**.
- **Video file loop (H.264 500k)**: health `good` at 500k. ✔
- **Dashboard render (drawtext, 720p, OUTFPS=10)**: health `ok`/`bad` at 500k, `bad` at 800k, `bad` at 2000k/3000k.
- Rule: **set VBR to ~60-70% of measured upload speed**, and keep OUTFPS=10, FPS=5, SCALE=1.0 (720p) on mobile.
- `videoIngestionStarved` / `bitrateLow` = too much data for uplink; lower VBR or move to WiFi.
- **`audioBitrateLow`** = audio bitrate < 128k. Script had `-b:a 64k`; YouTube needs **128k minimum**. Fix: `-b:a 128k` in the ffmpeg cmd (delta_dash_live.py line ~966).
- Health flips `ok`↔`bad` with network; a single `good` read after ~20s means the stream is live and viewers see it.

## Playlist / multi-video loop stream (verified 2026-11-08)

Stream multiple downloaded videos back-to-back (1 ke piche 1), looping forever, into ONE live broadcast. Used for Funny Froggy / content-channel live.

### Procedure (order matters)

1. **Download the videos** (yt-dlp, no cookies needed for public IG reels):
   ```bash
   yt-dlp -f 'bestvideo+bestaudio/best' -o '/root/myproject/froggy_%02d.mp4' <url1> <url2> ...
   ```
2. **Check codecs/resolutions first** — they will NOT match:
   ```bash
   for f in froggy_*.mp4; do echo "== $f"; ffprobe -v quiet -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 "$f" | head -2; done
   ```
   Expect vp9 + mixed resolutions (720p, 1080x1920 portrait, 1916x1078) and mixed fps (24 vs 30).
3. **Normalize every clip to ONE uniform format** (this is mandatory, not optional):
   ```bash
   for f in froggy_01.mp4 froggy_02.mp4 ...; do
     ffmpeg -y -i "$f" -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS,fps=24" \
       -c:v libx264 -preset veryfast -maxrate 1200k -bufsize 2400k -c:a aac -b:a 96k -ar 44100 "norm_$f"
   done
   ```
   Concat with `-c copy` of mismatched clips = `Conversion failed!`. Normalizing to x264 + 1280x720 + 24fps + AAC makes `-c copy` concat work.
4. **Write the concat list to a FILE on disk** (not process substitution):
   ```bash
   printf "file '%s'\n" /root/myproject/norm_froggy_01.mp4 /root/myproject/norm_froggy_02.mp4 ... > norm_concat.txt
   # verify: ffmpeg -y -f concat -safe 0 -i norm_concat.txt -c copy test_concat.mp4
   ```
   `-f concat` + `<(...)` process substitution failed in the proot/Ubuntu ffmpeg build — write the list file with `printf` and reference it.
5. **Push to RTMP with `-stream_loop -1` BEFORE `-f concat`** (input side, never output side):
   ```bash
   ffmpeg -re -stream_loop -1 -f concat -safe 0 -i norm_concat.txt \
     -c:v libx264 -preset veryfast -maxrate 500k -bufsize 1000k -pix_fmt yuv420p \
     -c:a aac -b:a 96k -f flv "rtmp://a.rtmp.youtube.com/live2/$STREAM_KEY"
   ```
6. **Verify**: streamStatus `active` + healthStatus `good` after ~25s → then broadcast transition (below).

### Broadcast without enableAutoStart ("UPCOMING" stuck)

If the broadcast was created with only `snippet`+`status` (no `contentDetails.enableAutoStart`), it stays `ready`/"UPCOMING" even while the stream is active. Transition path that works:
```bash
# ready -> testing -> live  (direct ready->live = 403 'Invalid transition')
POST /liveBroadcasts/transition?broadcastStatus=testing&id=<BID>&part=status
# wait ~10-15s
POST /liveBroadcasts/transition?broadcastStatus=live&id=<BID>&part=status
```
`testing` transition returns `None`/empty items (silent) but flips the lifecycle to `testing`; the `live` transition then succeeds. Best practice remains creating WITH `enableAutoStart=True` (auto-transitions on healthy data) — this path is the fallback when you already created without it.

**Confirm by GET, not by the POST response.** A `transition` POST often returns empty `items` (or `None` lifecycle) even when it SUCCEEDED — that is a silent success, not a failure. Retrying the same POST then gives 403 `Invalid transition`/`Redundant transition` because the transition already happened. To know the real state, `GET /liveBroadcasts?part=status&id=<BID>` and read `lifeCycleStatus` — if it says `live`, stop retrying. Do not loop 4-5 POSTs against 403s when a single GET settles it.

Also: the first `transition?broadcastStatus=live` right after stream goes active can return `None` while the earlier `testing` call already flipped it — re-read lifecycle via GET before deciding.

### Pitfalls (playlist class)
- **`-stream_loop -1` on the OUTPUT url = fatal**: `Option stream_loop ... cannot be applied to output url` — it is an INPUT option. Put it immediately before `-i` (or before `-f concat`).
- **Mixed-resolution concat = `Conversion failed!`** — `-c copy` across 720p/1080x1920/1916x1078 and 24/30fps breaks. Normalize first (step 3).
- **ffmpeg exit 224 / `Broken pipe` (-32)** = network drop or YouTube RTMP cut. Broadcast stays `live`; stream goes `inactive`/`noData`. Restart ONLY the ffmpeg process with the same key/broadcast — do NOT create a new broadcast or new stream key.
- **`yt-dlp -o '%02d'` on individual post URLs = silent no-download**: `%02d` fills only for playlist index. Feeding separate post URLs (not a playlist) makes the FIRST video write to literal `froggy_%02d.mp4` and every later URL report "has already been downloaded" → skip → zero new files. Fix: give each URL an explicit filename (`-o '/root/myproject/froggy_09.mp4' <url>` per video), never the `%02d` template for one-off URLs.
- **IG logged-out scrape source**: profile page = login-wall, and yt-dlp's user extractor is broken (`Unable to extract data`). New reels come from a post page's **"More posts"** section — scrape post-page HTML for shortcodes, then verify media IDs are NEWER than your max downloaded before downloading.

### Extend the loop while live (incremental add)
The live stream keeps running on the current concat while new videos download. To grow it:
1. Download new videos (explicit filenames, see pitfall above) — do NOT touch the running concat.
2. Normalize the NEW files only (same filter as step 3 above).
3. Rebuild the concat list = old normalized + new normalized, in order (`norm_concat_N.txt`). Verify with a `-c copy` test concat (duration sums correctly).
4. Kill the running ffmpeg (stream goes `inactive`/`noData` — broadcast stays `live`).
5. Restart ffmpeg with the SAME stream key and SAME broadcast, new concat: `ffmpeg -re -stream_loop -1 -f concat -safe 0 -i norm_concat_N.txt ... -f flv "rtmp://a.rtmp.youtube.com/live2/$KEY"`.
6. Verify after ~25s: streamStatus `active` + healthStatus `good`. No new broadcast, no new stream key, no transition needed (broadcast already `live`).

**Why**: broadcast and stream key are bound once; only the source changes. New broadcast = new key = needless churn and "UPCOMING" re-wait.

## Copyright Strike Rule (USER DIRECTIVE - HIGH PRIORITY)

- **1 copyright strike aate hi SAB OFF**: live stream turant stop, naye uploads band.
- Strike detect karte hi: stream kill + channel notify.
- Stream se pehle: channel/claims check.
- Copyright risk: kisi aur ka content (Funny Froggy etc.) stream NAHI — strike risk.

## Token file (new, 2026-11-04)

- `~/.yt_token.json` (NOT `~/.youtube_token.json` — the old one's refresh_token was revoked, `invalid_grant`).
- Channel: **Radhe Krishna** `UCCVsg75j-_aw3JGaE9WPARA` (520 subs) — the 500-sub account.
- OAuth client: `409601904723-p4plo4ueheag1mqjmce2l3lobnkckiql.apps.googleusercontent.com` (NEW; secret `GOCSPX-JmH...`).
- Old client `917626090327-...` had a stale/mismatched secret and is NOT used.
- Scopes: youtube, youtube.upload, youtube.force-ssl (NO dedicated live scope needed — `youtube` covers liveBroadcasts).
- refresh_token_expires_in ≈ 604799 (7 days) while consent screen is in **Testing** mode; becomes permanent once **In production**.

## Live frame extraction from someone else's live stream (verified 2026-11-12)

Reverse direction: consume a live stream (any channel) and pull the CURRENT on-screen frame to analyse what the trader is showing — no token, no cookies needed.

### 1. Confirm it's live
```bash
yt-dlp -J '<https://youtube.com/live/<ID>>' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('is_live'), d.get('title'))"
```
`is_live: true` + title = live now. (Or grep the page HTML for `isLiveNow`.)

### 2. Get the HLS manifest URL
```bash
HLS=$(yt-dlp -J '<live-url>' | python3 -c "import json,sys; d=json.load(sys.stdin); print(next(f['url'] for f in d['formats'] if f.get('format_id')=='232'))")
```
itag **232 = 720p** HLS (`m3u8_native`), 230=360p, 231=480p, 270=1080p. The URL is a `manifest.googlevideo.com/.../hls_playlist/...` ~1200-char string — keep it in a shell var, don't truncate or echo-split it.

### 3. Grab 3 seconds and pull one frame
```bash
ffmpeg -y -v error -t 3 -i "$HLS" -frames:v 1 -q:v 2 live_frame.jpg
```
`-t 3` reads only ~3s of the live HLS and exits cleanly — no kill, no partial file.

### 4. Analyse with vision_analyze
Load the jpg and ask what the screen shows (market, price, candle direction, S/R lines, indicators, strategy visible, what the trader is doing).

### FAST wrapper (7s total, trade-timing critical)
`~/grab_live_frame.sh VIDEO_ID [height]` does steps 2+3 in ~7s (HLS fetch + 2s ffmpeg grab). Height: 232=720p (best), 231=480p, 230=360p. Output: `live_analysis/<VID>_live_frame.jpg`. Shebang MUST be `#!/data/data/com.termux/files/usr/bin/bash` (not home dir).

### Pitfalls (live-frame class)
- **Do NOT `yt-dlp --live-from-start` to grab a frame** — a live stream never terminates, so the download runs forever. Killing it leaves a partial file that ffprobe can't read (`Error opening input`). HLS + `-t 3` is the correct grab.
- **The static thumbnail (`maxresdefault_live.jpg`) is NOT the live frame** — it's a promo/static image, and it's CDN-cached (same md5 across cache-bust params). The real on-screen content only comes from the HLS segment grab.
- **Progressive googlevideo URLs (`itag` 137/136/...) 403 on direct fetch** without the right Referer/cookie headers — don't bother; use the m3u8 manifest URL which works directly.
- **`/tmp` writes fail on Termux** — write frames to `$HOME/live_analysis/`.
- **A dead/revoked OAuth token does NOT block this** — live-frame extraction is public and token-free.

## Pitfalls

- **YT_KEY is the stream key, not the OAuth token.** Setting the OAuth access token as YT_KEY pushes to a bogus RTMP URL and fails silently at the source.
- **Script never creates the broadcast.** Studio must have a live stream ready; otherwise RTMP connects to nothing.
- **`invalid_grant` on refresh** = refresh_token revoked/expired (Google drops stale tokens). Re-run the full OAuth flow, not just a refresh.
- **Test before live**: always run once with no YT_KEY to confirm `test.flv` renders real data before touching RTMP.
- **Unverified channel hard limit**: an unverified account may cap a live at ~15 min; phone-verify the channel for longer streams.
- **Connection abort restart (ffmpeg exit -103 / "connection abort")**: `Software caused connection abort` = network drop ya YouTube ne RTMP cut. Broadcast `live` hi rehta hai, stream `inactive`/`noData`. Fix: sirf stream process restart karo (same stream key, same broadcast) — naya broadcast mat banao. `proc` exit code 143 (SIGTERM) normal hai jab tum khud kill karte ho; 1/-103 ka matlab crash.
- **`liveStarting` stall**: broadcast `liveStarting` me atka rahta hai jab stream data insufficient ho (health `bad`). Health `ok` hone par bhi transition me 30-60s lag sakte hain. Manual `transition?broadcastStatus=live` de to **403 `Redundant transition`** aata hai — ye NORMAL hai, matlab autoStart ka transition already chal raha hai. Do NOT create a new broadcast; sirf wait karo + stream bitrate lower karo (500k→350k) agar health `bad` hai. Transition khud `live` ho jayega jab data flow sufficient hoga.
- **Shorts private flow**: channel ke Shorts (regular uploads playlist me NAHI aate) alag se private karne padte hain. `yt-dlp --flat-playlist --print "%(id)s" "https://www.youtube.com/@<handle>/shorts"` → IDs → batch `videos.update` privacyStatus=private. Verify: `@<handle>/shorts` tab khali + API status count. Ye uploads-playlist API ko bypass karta hai — Shorts list ke liye `playlistItems` + `channels.uploads` par bharosa mat karo.
- **API 401 (three distinct causes)**: `invalid_api_key` = galat base URL (India vs global); `expired_signature` = timestamp ms instead of seconds ya secret galat; `ip_not_whitelisted_for_api_key` = IP whitelist missing (upar fix). In teeno ko ek-ek karke cross out karo — ek hi 401 ke teen alag root causes hain.
- **YouTube API auth = Bearer header, NOT key param**: `?key=<access_token>` query param 401 deta hai. Har YouTube API call me `Authorization: Bearer <access_token>` header chahiye (liveBroadcasts, liveStreams, thumbnails, token refresh sab).
- **Bind gotcha (liveBroadcasts/bind)**: `streamId` QUERY param me jata hai (`?id=<BID>&streamId=<SID>`), body me NAHI. Body `{'streamId':...}` ya `{'id':...}` dekar bhejo to `boundStreamId` nahi milta (silent fail). Body empty (`data=b''`) + query params = works.
- **scheduledStartTime format**: `datetime.datetime.utcnow().isoformat()+'Z'` chahiye. `datetime.now(datetime.UTC).isoformat()+'Z'` se `invalidScheduledStartTime` (400) aata hai.
- **liveStreams create part param**: `part=id,snippet,cdn` use karo (status create body me hai, part me NAHI) — `part=id,snippet,cdn,status` se `unexpectedPart`.
- **Content editing for live = ffmpeg, NOT CapCut**: CapCut is banned on Indian Play Store (not available), has no CLI/API (GUI only), and ADB-tap automation of its timeline is fragile — do not build the live pipeline on it. ffmpeg is the correct tool: crop/trim/watermark/music recipes in `references/video-editing-ffmpeg.md`. Free GUI alternatives for one-off creative edits: VN Video Editor, InShot, KineMaster (India-available, no watermark on manual export).
- **IG reel/video download (yt-dlp) needs NO cookies for public posts** — the earlier `empty media response` was transient; retry (or use Big Pickle's Playwright path) resolves it. `-f 'bestvideo+bestaudio/best'` works.
- **Bitrate grinding limit**: health `bad` (videoIngestionStarved) 3+ bitrate reductions ke baad bhi (500k→350k→250k→150k→100k→80k) rahe to network hi problem hai, bitrate nahi. Aur kam karna pointless — stop karo, user ko saaf bolo WiFi/stable network chahiye. Endless bitrate grind mat karo (user frustration signal: "Tere se nahi hoga stop kar de").

## SEO title/description (Live Strategy class)

Search "crypto live trading" ke top channels ka pattern (90 videos, 10 channels analyzed):
- **Title:** `🔴 LIVE TRADING | GOLD & BTC | FOREX | <DATE> #livetrading #goldtrading #cryptotrading` — 🔴 emoji + LIVE + main symbols + date, 3-5 hashtags in title.
- **Top hashtags:** `#livetrading` #cryptotrading #goldtrading #forextrading #bitcoin #crypto #btc #daytrading #intradaytrading #technicalanalysis #tradingstrategy`.
- **Description:** hashtags line top pe (10-15), phir welcome + strategy + results + disclaimer. Broker/telegram links affiliate convention.
- **Disclaimer (hard requirement, user-specified):** options selling = unlimited risk; educational only, not financial advice; backtest ≠ future; slippage/fees excluded. Isko hamesha description me daalo.
- Full SEO report: `~/crypto_live_analysis/SEO_Report.md` (data.json + analysis scripts).