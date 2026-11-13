---
name: delta-trading-live-stream
description: Use when streaming live Delta trades to YouTube via ffmpeg.
---

# Delta Trading Data → YouTube Live Stream

Stream a live trading dashboard to YouTube Live using the pure-API route: Delta WebSocket + REST → Python renders 1280×720 frames → ffmpeg (drawtext + libx264) → RTMP → YouTube. No ADB, no screen capture, no OBS.

## The script

`~/delta_dash_live.py` — stdlib-only, Termux + ffmpeg. User-designed. Renders a Delta Exchange-style terminal (nav, price header, candlestick chart, SELL/BUY, positions panel, account panel) from live Delta data and pushes it to YouTube Live.

## Run

```bash
cd ~
YT_KEY=<stream_key> \
DELTA_KEY=<api_key> DELTA_SECRET=<api_secret> \
SYM=ETHUSD TF=15m FPS=5 \
FONT=/system/fonts/Roboto-Regular.ttf \
FONTB=/system/fonts/DroidSans-Bold.ttf \
python3 delta_dash_live.py
```

| Env | Purpose | Empty → |
|---|---|---|
| `YT_KEY` | YouTube stream key | saves `test.flv` (60s), no network |
| `DELTA_KEY`/`DELTA_SECRET` | Delta API key (Trade scope) | positions 0/0, Account "-"; candles/price still work |
| `SYM` | Symbol (default ETHUSD) | — |
| `TF` | Timeframe 1m/5m/15m/30m/1h (default 15m) | — |
| `FPS` | Frame rate (default 5; 10 verified) | — |
| `USDINR` | Set to show ₹ instead of $ | $ |
| `FONT`/`FONTB` | Font paths (see pitfalls) | — |
| `SCALE` | Render scale (default 1.5 → 1920×1080 native) | 1280×720 logical |
| `OUTFPS` | Output fps (default 15; 10/15 verified) | — |
| `NC` | Candle count 10–300 (default 57; 100 verified clean) | 57 |
| `WW`/`WH` | Render resolution override (default 1280×720 logical × SCALE) | — |
| `OUTW`/`OUTH` | Final output scale after render (upscale path) | — |
| `VBR` | Video bitrate (default 6000k) | 6000k |
| `PRESET` | x264 preset (default veryfast) | veryfast |
| `TEST_SECS` | Test-run duration when YT_KEY unset (default 60) | 60 |

## Verified on this device (Termux aarch64)

- ffmpeg 8.1.2 has drawtext, rtmp, libx264 ✅
- Output: 1280×720, exact 10 fps (602 frames / 60.2 s, 0.1 s timestamps, zero dropped frames), ~689 kbps, 1 min ≈ 5 MB → 15 min ≈ 75 MB
- Real Delta data flows: live price, candles, 24h change, index price, 24h vol, OI, funding + live countdown
- `test.flv` renders and exits cleanly when `YT_KEY` unset
- **SCALE=1.5 (default) renders 1920×1080 natively** — NOT upscale. Verified: 1080p output, 15 fps, real-time encode (~60 s video in ~63 s), ~1.2 Mbps. Text is crisp (high contrast), 57 candles detected exactly (8.4 px wide, 18 px spacing, no overlap).
- **NC=100 verified clean** — 100 candles, ~5 px spacing, no overlap; grid + price labels stay readable. NC≥200 makes candles nearly invisible.
- Data is verified REAL (no fake/hardcode): script has no random/mock data; `os.urandom` only for the WebSocket handshake key. Frame values match the live Delta `/v2/tickers` response (difference is just elapsed time — price moved between render and check).

## Pipeline

```
Delta WebSocket (socket.india.delta.exchange: candlestick_<TF> + v2/ticker)  ← push
Delta REST (tickers, positions/margined, wallet/balances, orders)            ← 3s polling
        ↓
Python renders 1280×720 RGB frame → ffmpeg stdin
        ↓
ffmpeg: rawvideo → drawtext (textfile reload=1) → fps → libx264 → flv
        ↓
RTMP: rtmp://a.rtmp.youtube.com/live2/<YT_KEY>
```

Signed REST calls use the HMAC header (api-key, timestamp, signature over `GET+ts+path`). WebSocket is the max-speed path for price/candles; polling fills the rest.

## YouTube Live prerequisites

- Token fresh (expired → 401 → re-auth via `youtube-colab-oauth`) with `youtube.force-ssl` scope
- Channel verified: unverified = **15 min max** stream; verified = 12 hr
- API order: `liveBroadcasts.insert` → `liveStreams.insert` (RTMP URL + key) → `liveBroadcasts.bind` → feed ffmpeg → `liveBroadcasts.transition` to complete

## Auto-stop risks (why a live stream ends on its own)

- **Unverified channel = 15 min hard limit** (YouTube's rule, cannot be bypassed). Verify phone number in Studio → 12 hr.
- **Verified channel = 12 hr max per stream** — after that, create a new broadcast.
- **ffmpeg/data stall** — script has no watchdog yet; a feed gap gets the stream killed within ~2 min. Plan: watchdog + auto-restart loop (stream dies → re-create broadcast → re-bind → resume, ~10–20 s gap).
- **30 min screenrecord cap is NOT relevant to the pure-API route** — only to ADB screen capture.

## Pitfalls

- **Roboto-Bold.ttf missing on this device** (`/system/fonts/Roboto-Bold.ttf` does not exist). Set `FONTB=/system/fonts/DroidSans-Bold.ttf`; otherwise the script silently falls back to FONT and bold text renders non-bold.
- **Missing keys are normal, not errors.** No DELTA_KEY → positions 0/0, Account "-". No YT_KEY → `test.flv` 60s then exit.
- **ffmpeg stdin write OSError → "ffmpeg band ho gaya"** — ffmpeg died; verify the process before debugging the script.
- **`dash_tmp/` is created by the script** for drawtext textfiles (reload=1) — needs writable $HOME path (/tmp writes fail on Termux).
- **drawtext textfile + reload=1** is the fast-update mechanism; don't swap to `text=` (per-frame filter rebuild is slow).
- **RTMP URL must match the bound stream key** — `rtmp://a.rtmp.youtube.com/live2/<YT_KEY>` exactly.
- **`vision_analyze` on the rendered frame can timeout** (seen repeatedly at 1080p/1920px). Fall back to pixel analysis in Python: decode the PNG (zlib + unfilter), sample regions for contrast (text = high contrast, e.g. 236/14), and count candle columns by detecting green/red pixels in the chart band. That is how a 1080p frame was verified when vision_analyze failed.

## User preferences

- **Pure-API dashboard over ADB screenrecord for trading live** ("YouTube live me adb use nahi kare ge"). Don't push ADB.
- **Max-speed data** — WebSocket push for price/chart, not polling.
- **Show a demo frame/video before going live** — deliver a rendered still + MP4 first, get approval.
- **The dashboard is the user's own design** — run/extend `~/delta_dash_live.py`, don't rewrite it.
- Hinglish, short, bullet answers.

## ADB alternative (rejected for trading, still valid for any app screen)

`adb exec-out screenrecord --output-format=h264 -` pipes the phone screen as a live h264 stream into ffmpeg → RTMP. `screencap` is a single photo, NOT the live tool. Android caps each `screenrecord` session at ~30 min → loop restart for continuous. Requires screen ON, app visible, charging, stay-awake.
