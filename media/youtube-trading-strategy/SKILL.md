---
name: youtube-trading-strategy
version: 1.0
description: Learn strategy from YouTube safely, build/modify backtest.
tags: ["youtube", "trading", "strategy", "backtest", "safety"]
---

# YouTube Trading Strategy (Learn + Build)

Take a YouTube video showing a trading strategy → extract rules → build safe backtest → compare metrics. **No live orders.**

## Safety Rules (Always On)

1. **`DELTA_MCP_MODE=trade` DISABLED** — read-only market data only
2. **No API keys in scripts** — secrets live in `~/.delta-exchange-mcp/config.env`
3. **Never invent** price / SL / TP / RR not in transcript — flag "not specified"
4. **Backtest only** with public historical data
5. **Concise output** — user hates verbose filler

## Workflow

### 0. Multi-Video Discipline (mandatory)

When the user sends **more than one** strategy video, do NOT merge their logic into a single backtest by default. Users will call this out ("3 video ka logic mix nahi kiya na") — they want to see each video's distinct logic kept separate, then compared.

Default flow:
1. Extract rules from **each** video independently, cite line numbers
2. Diff them side-by-side (what's shared, what's unique per video)
3. Run **one backtest per video** on the same dataset, same parameters
4. Add a head-to-head comparison table
5. Ask before running combined versions

Only combine when user explicitly says "mix", "combine", or "merge".

### 1. Fetch Transcript
```bash
# yt-dlp on Termux (needs deno)
pkg install deno
yt-dlp --remote-components ejs:npm \
  --write-auto-sub --sub-langs "en,hi" \
  -o "%(id)s.%(ext)s" "URL"
```

**Fallback:** if `en` transcript missing, retry with `hi`. Iterate `FetchedTranscript` directly — no `to_raw_dict`.

### 2. Extract Rules

Fill each slot from transcript (cite line numbers):

```
Strategy name:
Symbol / market:
Timeframe:
Entry trigger:
SL rule:
TP rule:
RR expected:
Position sizing:
Filters (time / news / trend):
Exit conditions:
```

### 3. Save to Data Folder
```
~/Hermes_Almari/02_DATA/strategy_yt_<vid>_<name>.md
```
2-POV format: **What** (rule) + **Why** (transcript quote).

### 4. Build Backtest
Use existing skill `hermes-crypto-grid-backtest` or write standalone:

```python
# Skeleton
import pandas as pd
df = pd.read_csv('ada_m15_candles.csv')
positions = []
for i in range(1, len(df)):
    if entry_signal(df, i):
        positions.append(open_position(df, i))
    update_positions(df, i)

# Compute metrics
metrics = compute_metrics(positions)
print(metrics)
```

### 5. Compare Metrics

| Metric | Meaning | Target |
|---|---|---|
| CAGR | Annual return | >20% |
| Max Drawdown | Worst peak-to-trough | <20% |
| Sharpe | Risk-adjusted return | >1.0 |
| Win rate | % profitable trades | >40% |
| Profit factor | Gross profit / gross loss | >1.2 |

**Baseline (ADA):**
- ADA 15m EMA300 SL=1% TP=6% RR=1:6 → +206%, PF 1.175
- ADA 2h ATR → PF 2.21, +404%
- HFT EMA50+Trail ETHUSD 1m (2025-12 → 2026-08): +432% PF 27 (no slip), +398% PF 8.4 (20 pip spread + 10 pip slip). See `references/slippage-sensitivity.md` for the sensitivity table.

### 6. Slippage / Spread Sensitivity — mandatory for HFT and scalping claims

YouTube EA demos usually quote returns at **zero slippage** on an unrealistic spread. Before signing off on any backtest result for a sub-15m timeframe strategy, run the same strategy across at least 3 spread/slippage combos and check that the return sign doesn't flip. See `references/slippage-sensitivity.md`.

## Pitfalls

- **YouTube-MCP** needs `GOOGLE_API_KEY` — skip per no-credential rule
- **`uvx` blocked** on Android aarch64 (pip takes 300s+)
- Vague strategies ("be bullish") aren't testable — reject
- Survivorship bias — most YouTube strategies don't survive backtest
- Docs URLs often blocked — say so honestly

## Related Skills
- `youtube-trading-workflow` — end-to-end pipeline
- `youtube-strategy-analysis` — extraction templates
- `hermes-crypto-grid-backtest` — backtesting engine
