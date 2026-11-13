---
name: delta-youtube-live-stream
description: Use when live-streaming trading data to YouTube.
---

# Delta → YouTube Live Trading Stream

User's live-trading-to-YouTube project. User DESIGNED the dashboard script themselves; I test/verify/improve it.

## The script

`~/delta_dash_live.py` — **stdlib only** (NO numpy, NO pandas). Renders a Delta Exchange-style terminal dashboard from live API data and pipes frames to ffmpeg → RTMP → YouTube Live.

```bash
# live mode (needs YT_KEY)
YT_KEY=<streamkey> DELTA_KEY=.. DELTA_SECRET=.. python3 ~/delta_dash_live.py
# test mode (no YT_KEY -> writes test.flv, 60s)
python3 ~/delta_dash_live.py
```

## Data sources (all REAL, verified)

- **WebSocket** `socket.india.delta.exchange` → `candlestick_<TF>` + `v2/ticker` (live push, ms speed)
- **REST** `api.india.delta.exchange` → `/v2/tickers/<SYM>`, `/v2/positions/margined` (signed), `/v2/wallet/balances` (signed), `/v2/orders?state=open` (signed)
- Signed calls use HMAC-SHA256: `GET + ts + path`, api-key/timestamp/signature headers
- Positions PnL = `(bid|ask − entry) × size × contract_value`; contract_value read per-symbol

## Env vars

`SYM` (ETHUSD), `TF` (15m), `DELTA_KEY`, `DELTA_SECRET`, `YT_KEY`, `SCALE` (1.5→1080p), `NC` (candles, 57), `FPS` (5 in), `OUTFPS` (15), `TEST_SECS`, `VBR` (6000k), `PRESET` (veryfast), `WW/WH`, `OUTW/OUTH`, `FONT/FONTB`, `USDINR`/`CURSYM`

## Rendering

- Logical 1280×720 × SCALE (1.5 → 1920×1080 native). Grid/candle spacing adaptive to NC.
- Bitmap glyph atlas for price tags; drawtext (ffmpeg) for static labels with reload=1.
- Candle width auto-shrinks as NC grows: NC=57→18px spacing, NC=100→9px, NC=150→6px.
- Output: `libx264 -profile high -b:v VBR -g OUTFPS*2 -pix_fmt yuv420p` + aac 64k → RTMP.

## Verified facts

- **User prefers 720p/10fps look** (called first version "acha") but accepted SCALE=1.5 (1080p/15fps) native render. Both work; runtime env decides.
- Real-time encode confirmed: 60s video ≈ 60s wall. 10fps/720p ≈ 690kbps, 15fps/1080p ≈ 1.2Mbps.
- Data 100% real — verified frame vs live API match; NO random/hardcoded values (os.urandom only in WS handshake).
- WebSocket gives near-zero latency (preferred over polling).

## Pitfalls

- **YouTube token EXPIRED (invalid_grant)** — refresh token dead. Re-auth via Colab OAuth skill `youtube-colab-oauth` (full 4-scope token).
- **Channel UNVERIFIED → 15 min hard live limit.** Phone verify → 12 hr. Auto-stop is YouTube's rule, cannot bypass.
- **Auto-stop handling:** broadcast ends / data stalls → need watchdog + auto re-create broadcast + re-live (gap ~10-20s). Not yet built — build if user wants continuous.
- **screenrecord NOT used** — dashboard approach is ADB-free (no 30-min limit, no phone-screen dependency).
- Vision_analyze can timeout on large 1920×1080 PNGs — verify via pixel analysis (contrast/candle-count) instead.
- `pos_loop` only runs if BOTH KEY and SEC set; without keys positions/account show 0/0 and "-".

## User context

- User trades on **Delta AND Paradigm** (Paradigm screenshot: ETHUSD options, P-ETH-2650 / C-ETH-2650, -1 Lot each).
- User wants **max-speed data (WebSocket), verified real data only, no fake values**.
- Wants candle size adjustable (NC env) — done.
- Live streaming to YouTube of their real trades is the goal; 720p/10fps or 1080p/15fps.
