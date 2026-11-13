---
name: youtube-strategy-analysis
version: 1.0
description: Learn trading strategy from YouTube transcript safely.
tags: ["youtube", "trading", "strategy", "transcript", "backtest"]
---

# YouTube Trading Strategy Analysis

Extract trading strategy from YouTube videos → backtest → refine. **Safe, no live trading.**

## Always-On Rules

1. **DELTA_MCP_MODE=trade DISABLED** — never place live orders
2. **No API keys in code** — read from `~/.delta-exchange-mcp/config.env` if present
3. **Never invent** exact price/SL/TP/RR numbers missing from transcript — say "not specified"
4. **Backtest only** with public historical data (delta-exchange-mcp or ADA ticks)
5. **2-POV format** per step (What + Why)
6. **Cite transcript** line numbers when quoting

## Procedure

### Step 1: Fetch Transcript
```bash
yt-dlp --remote-components ejs:npm --write-auto-sub --sub-langs "en,hi" -o "%(id)s.%(ext)s" "URL"
# If en fails, retry with hi; iterate FetchedTranscript directly (no to_raw_dict)
```

### Step 2: Extract Strategy Components
For each element, record **what** the video says + **source line**:

| Component | Extract | Example |
|---|---|---|
| Entry trigger | Indicator + level | "EMA200 cross" |
| SL placement | Distance/ATR multiplier | "1x ATR" (or "not specified") |
| TP target | R multiple or % | "2R" |
| RR ratio | Expected:Actual | 1:2 |
| Position size | Fixed % or Kelly | "1% risk" |
| Timeframe | Chart interval | "15m" |
| Filter | Session/trend | "uptrend only" |
| Duration | Hold period | "3-5 days" |

### Step 3: Save to Skill Format
Write to `~/Hermes_Almari/02_DATA/strategy_from_youtube_<vid>.md`:
```markdown
# Strategy: <name>
Source: <YouTube URL>
Fetched: <date>

## Entry
- What: ...
- Why (transcript): line 42: "..."

## Exit
- SL: ...
- TP: ...

## Filters
...
```

### Step 4: Backtest
```bash
python3 ~/analyze_ada_pct.py --strategy "<config>"
# Or use hermes-crypto-grid-backtest skill
```

### Step 5: Report Metrics
- Win rate
- Profit factor
- Max drawdown
- CAGR
- Sharpe ratio

## Pitfalls

- **YouTube-MCP** (github) needs GOOGLE_API_KEY — skip per no-credential rule
- Don't accept vague strategy ("be bullish") as testable
- Compare with user's existing best: **ADA 15m EMA300 SL=1% TP=6% RR=1:6 → +206%, PF 1.175**
- User prefers concise output — no extra explanation
- If user's Std 10 level, avoid jargon — plain language

## Reference
See `references/strategy-analysis.md` for extraction templates.
