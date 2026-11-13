---
name: youtube-trading-workflow
version: 1.0
description: YouTube transcript to safe trading strategy workflow.
tags: ["youtube", "trading", "workflow", "backtest"]
---

# YouTube → Trading Strategy Workflow

End-to-end pipeline: **video URL → rules → backtest → metrics → iterate**.

## Always-On Rules

- **No extra prose** — bullet steps only
- **2-POV format** per step (What + Why)
- **`DELTA_MCP_MODE=trade` DISABLED** — market data only
- **No API keys** in scripts
- **`uvx` blocked** on Android aarch64 (pip 300s+) — use `pkg install` or skip
- **Docs URL blocked** — say so honestly, don't fabricate
- **Unresolved binary** — if a dep can't run, say so

## Pipeline (5 Stages)

### 1. Fetch Transcript
```
What: yt-dlp with sub-langs "en,hi"
Why: Hindi + English coverage; en fallback to hi
```

**Termux setup (once):**
```bash
pkg install deno
yt-dlp --remote-components ejs:npm
```

### 2. Extract Rules
```
What: read transcript line by line, tag rules
Why: video talks → need concrete IF/THEN for backtest
```

Output template:
```
ENTRY: {trigger, timeframe, filter}
EXIT:  {SL, TP, time_stop}
SIZING: {risk%, max_positions}
```

### 3. Save Skill + 2-POV
```
What: write to ~/Hermes_Almari/02_DATA/strategy_yt_<vid>.md
Why: persist for backtest + user review
```

### 4. Backtest
```
What: run against public candles (ADA 15m/2h, NIFTY, BTC)
Why: no live risk, verifiable numbers
```

Use `hermes-crypto-grid-backtest` skill or standalone script.

### 5. Metrics + Iterate
```
What: CAGR, max drawdown, Sharpe, win rate, PF
Why: compare with baseline (ADA EMA300 PF 1.175)
```

**Decision:**
- PF > 1.2 + DD < 20% → KEEP, log to paper trade
- PF < 1.0 → REVERT, mark as "YouTube hype"
- In between → MODIFY (tighten SL, add filter)

## Files Involved

| Path | Purpose |
|---|---|
| `~/Hermes_Almari/02_DATA/ada_m15_candles.csv` | Backtest data |
| `~/Hermes_Almari/02_DATA/ada_m2_candles.csv` | Backtest data |
| `~/Hermes_Almari/02_DATA/strategy_yt_*.md` | Extracted strategies |
| `~/analyze_ada_pct.py` | Existing backtest script |

## Example Session

```
User: "Watch this video, extract strategy"
→ Fetch transcript (URL)
→ Extract: "EMA20 cross on 15m, SL 1%, TP 3%"
→ Save: ~/02_DATA/strategy_yt_LTulYQ_YRGo.md
→ Backtest: ADA 15m 3 months → PF 1.05
→ Verdict: WORSE than baseline (PF 1.175) — do not use
→ Log: paper trade decision "skip"
```

## Pitfalls

- Video creator shows 3 winning trades — cherry-picked
- No SL mentioned → reject, not testable
- "100% wins" — statistical impossibility at scale
- Screenshot of dashboard only → no methodology
