---
name: strategy-backtest-verify
description: Use before grid/param sweep on a user-provided strategy.
version: 1.0.0
---

# Strategy Backtest Verify Workflow

When the user gives a strategy script and asks for a grid backtest, follow this EXACT order. Never skip steps. User will reject if you modify strategy logic — reproduce exactly.

## Rule 0: Never modify strategy logic

If the user provides a strategy (e.g. `backtest()` function), copy it VERBATIM into the grid runner. Do not rewrite ATR, EMA, indicators, or entry/exit conditions "for speed" — user will reject.

## Step 1: Diff rewrite vs original

Before running anything, list every difference between your rewrite and the user's original. Focus on:
- Indicator math (EMA, ATR, pivots)
- Entry/exit conditions
- Position management
- Lookahead / shift()
- Any variable renames

Present as a checklist. If user sees a change they didn't authorize, STOP and revert.

## Step 2: Default-params single run

Run the grid on ONE coin + ONE TF + default params. Print:
- Trades count
- Win/Loss split
- PF, total R, avg R

If trades = 0, DO NOT proceed to full grid. Debug instead.

## Step 3: Funnel debug counters

If default params give 0 (or suspiciously low) trades, add per-condition counters in the backtest loop:

For LONG (mirror for SHORT):
```
c > EMA bars
  2+ swing highs
    p2 < p1 (downtrend)
      age filter passed
        c > trendline
          c > p2 (above swing)
            now=True
              now AND NOT prev (fresh cross)
                SIG generated
                  Positions opened
                    Trades closed
```

Print each stage with count + % of previous stage. This shows exactly where signals die.

## Step 4: Only then run full grid

After confirming trade flow with funnel:
- Cache data per (coin, tf) at ~/bt_cache/
- Append results to CSV incrementally (crash-safe)
- Report: top combos, stability analysis, lucky-point warning

### Indicator + split rule (CRITICAL)

Compute `add_indicators()` on the FULL df FIRST, THEN do the 70/30 train/test split.

```python
# WRONG — indicators computed independently on each split:
df_train_i = add_indicators(df_train, ema)   # EMA warmup restarts at 0
df_test_i  = add_indicators(df_test, ema)     # test set EMA ≠ train EMA

# RIGHT — full df first, then slice:
df_i = add_indicators(df, ema)                # EMA built over entire history
df_train = df_i.iloc[:split].reset_index(drop=True)
df_test  = df_i.iloc[split:].reset_index(drop=True)
```

**Why:** EMA at bar 0 of `df_test` is meaningless if computed in isolation — you want EMA to reflect the full price history up to that bar, including train-period bars. Splitting first also wastes compute (recompute per split).

**Same rule applies to ATR** — the ATR column at position 0 of `df_test` must be the same as its value in the full-df ATR, not a fresh EWM from scratch.

### Report structure (user preferences)

For out-of-sample honesty (walk-forward split, cost modeling, pass-rate/days-to-pass reporting), see `references/walk-forward-costs.md`. Read it before claiming a prop-firm pass rate or any "keeps working" claim.

### Sample-safe rating (USER DIRECTIVE — raw win rate alone is luck)

Raw win rate is NOT the rating. A coin with 3 trades at 100% is luck; a coin with 100 trades at 75% with good RR/DD is real edge. Use a composite score:

```python
# Wilson lower bound — penalizes small samples (3/3=100% -> ~56%, 100/100=75% stays high)
def wilson(w, n, z=1.96):
    if n == 0: return 0
    p = w / n; denom = 1 + z*z / n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / denom

# Composite: Wilson win% + net/trade + log(PF) - DD penalty (bounded, no explosion)
def score(d):
    n = max(1, d['trades'])
    wr = wilson(d['win'], n)
    npt = d['net'] / n
    pf = d['gw'] / max(0.1, d['gl'])
    lpf = math.log10(max(pf, 0.1))          # log keeps PF bounded (220 -> ~2.3)
    dd_pen = abs(d['dd']) / max(1, n)
    return 0.45*wr*100 + 0.30*math.tanh(npt)*50 + 0.25*lpf*30 - dd_pen*3
```

Do NOT use raw PF directly in a weighted sum — it explodes (PF 220 from a 9-trade streak). Log it.

### Per-chunk break-even thresholds (USER logic: chunk-specific win rate)

Chunks with small RR (break-even zone) need HIGH win rate; chunks with big RR can take lower. Compute per-chunk break-even win rate from the data, then filter coins per chunk:

```python
BE_win = 1/(1+RR)*100   # RR = avgWin/avgLoss per chunk
# C1-C3 (RR 0.6-0.7): BE ~58-63% -> require >= BE
# C6 (RR ~0.93, big profit/loss): BE ~52% -> require >= BE only
```

### Luck-removal check (USER directive: one coin big profit = not the edge)

Before recommending any set, drop the top-N profit coins and re-run. If net stays positive (e.g. top5 removed -> still +$59 on 79 coins), the edge is NOT a single lucky coin. If net flips negative after dropping top1, flag it.

Also check concentration: top1 coin should be < ~15% of total net (AIOTUSD was 10.7% = acceptable).

### 1-trade/day + walk-forward (USER asked for daily-scaled validation)

For a daily-cadence strategy, simulate 1 trade/day (pick best available per priority), then walk-forward split the data into 2 halves: select on half1, verify on half2. Require OOS (half2) to keep win% and net positive — otherwise the selection is in-sample overfit.

### Consistency gate (USER DIRECTIVE — hard requirement)

A strategy that passes only 1-2 months of 12 is luck, not edge — the user will reject it. Before recommending any config as a pass candidate, compute MONTHLY PnL from the daily series and require **consistency >= 75%** (at least 9 of 12 months positive). If the best config in a scan lands at 48% (11/23), the whole scan has no durable edge — do not cherry-pick the top net as "the winner". Report the consistency column for every finalist and mark configs below 75% as REJECT. The monthly breakdown is computed by bucketing the daily PnL series by `YYYY-MM`; the daily series must carry dates (a bare float series loses this). If your engine drops dates at dump time, re-derive the series with dates via the engine's `run_series()`-style call, not from the JSON dump.

A single in-sample win is not evidence: a config that returns +21% on the search window (2023-24) but -19% on out-of-sample (2025-26) is overfit — reject it, even when the search-window number looks strong. Report the OOS result prominently, not buried.

1. **Top 15 filter**: `trades >= MIN_TRADES` AND `train_pf > 1` AND `test_pf > 1` AND `train_trades >= MIN_TRAIN_TRADES` AND `test_trades >= MIN_TEST_TRADES`. Require MIN_TRAIN_TRADES and MIN_TEST_TRADES (default 15 each) — a combo with 30 total trades but 28 in train and 2 in test is not testable.

2. **Best per (coin, tf)**: sort by `min(train_pf, test_pf)`, NOT by train_pf or test_pf alone. A combo with train=10, test=0.1 is worse than train=1.5, test=1.5 — the min captures both robustness and out-of-sample strength.

3. **Lucky-point detection**: For each top combo, enumerate 1-step neighbors in parameter space (same coin/tf/pl/pr, ±1 step on ema, atr_mult, rr — 2^3 = 8 neighbors). Count how many have PF < 1. If >50% of neighbors have PF < 1, mark the combo as 🚨 LUCKY. If <=50%, mark as ✅ STABLE. Recommend only STABLE combos.

4. **Cross-coin consensus**: Group valid combos by (tf, ema, atr_mult, rr, pl, pr) and count distinct coins. Combos with `coins >= 2` where both train_pf > 1 and test_pf > 1 are much stronger candidates — the parameter survives across assets. Report this separately.

5. **Stale CSV handling**: Delete `~/grid_results.csv`, `~/grid_top15.csv`, `~/grid_best_per_symbol.csv`, `~/grid_cross_coin_consensus.csv` at run start. Never append to a stale CSV — you'll get duplicates and stale rows pollute rankings.

### Fetch resilience

Wrap `fetch_delta()` in try/except:
```python
try:
    df, _ = fetch_delta(coin, tf, days, cache_dir=cache_dir)
    if len(df) < MIN_CANDLES:
        print(f"  SKIP {coin} {tf}: too few candles ({len(df)})")
        continue
except Exception as e:
    print(f"  SKIP {coin} {tf}: {e}")
    continue
```

Never let a single coin/tf failure abort the whole grid.

## StrategyTune MCP (Big Pickle) — setup & lessons

Full depth (setup commands, script format, hard limits, MCP timeout retry, task-file passing, cross-instrument SL/TP scaling): see `references/strategytune-mcp.md`. Load it before any StrategyTune work.

### The OOS validation trap (CRITICAL — cost the whole "best combo" claim)

A grid that finds a high pass-rate cell on ONE window is **not** an edge — it is a regime snapshot. This session: SL 500/TP 50 on Gold showed **81.6%** 15-day pass on 2026-09→11, but the SAME combo on the non-overlapping earlier window (2026-05→09) collapsed to **0%** (0/92 windows), −46.6%, PF 0.80, and its −$902 worst day / 60.6% max DD breach the 5%/10% gates outright so no window could ever pass. The 81.6% was one favorable Gold regime.

**Rule:** never present a single-window in-sample pass rate as evidence. Before claiming a pass candidate:
1. Test the SAME combo on a **non-overlapping earlier window** (OOS). If pass rate collapses, it was luck — report that plainly, do not soften it.
2. Test the SAME combo on a **second instrument** (cross-instrument robustness) — a gold-regime artifact won't survive.
3. Test on a **longer window** (6 months, not 2) and compare SL variants on the same span.
4. Watch the **worst day and max DD vs the gates**: if a single stop is ≥ the daily-loss limit, or the day allows 2 losses > the limit, NO window can pass regardless of win rate — that geometry is structurally dead for the ruleset.

### High-win-rate ≠ edge (already-learned, reinforced)

A 90% win rate with a 1:6.4 payoff skew is a byproduct of the geometry, not skill. Measure expectancy (net/trade) and PF; if PF ≈ 1.0-1.2 and edge ≈ 0.02R, the win rate is cosmetic. Long-bias through an up-trending sample explains "profit" as much as edge does.

### Prop-challenge geometry is structural, not tunable

A high-win-rate small-TP strategy (tiny TP, wide SL) CANNOT pass a consistency rule (best day > 30% of profit) — daily upside is capped by the small TP while one stop wipes the day. There is no R:R tweak that makes it both consistency-legal and drawdown-legal with a ~0 edge. If this is the geometry, the answer is: find a real edge (PF ≥ 1.3), don't tune R:R.

### Dense grid (USER PREFERENCE — no big gaps)

The user wants a MAX grid with **no large gaps between SL values and no large gaps between TP values**. Do not sample SL at 100/175/250/400/500 and TP at 25/50/100/150/200 — that leaves wide empty bands that can hide the plateau. Use fine steps (e.g. SL step 50, TP step 12.5) so the grid reveals whether high pass rate is a **contiguous plateau** or just **isolated spikes**. Report that distinction — an isolated spike is likely a lucky point; a plateau is more robust.

### Direct MCP client beats Big Pickle round-trip (THIS SESSION)

For grid sweeps, run StrategyTune MCP **directly from Python** (`st_mcp.py`) instead of `opencode run` → Big Pickle. Why: `opencode run` round-trips the whole conversation, times out at ~30s+/cell with `-32001 Request timed out`, and loses results; a direct `urllib` client does a cell in ~8s with no timeout. Grid of 42 combos in ~5 min (direct) vs 3+ workers timing out (via Big Pickle).

Key facts about the direct client:
- MCP call format is **`tools/call`** with `{"name": "<tool>", "arguments": {...}}` — NOT a bare `run_backtest` method. Method name must be `strategytune_<tool>`.
- Auth file: `/root/.local/share/opencode/mcp-auth.json` (proot) → copy to `$HOME/.hermes/cache/st_mcp_auth.json`. Keys: `strategytune.tokens.accessToken/refreshToken/expiresAt`.
- Token refresh: OAuth `oauth/token` with refresh_token + client_id (from the auth URL). `get_valid_token()` refreshes when `expiresAt` near. Handle `HTTP Error 401` by re-fetching token.
- `save_session:false` research runs have NO record → `get_session_trades` fails ("session not found"). For trades, re-run with `save_session:true`, find `recordId` via `strategytune_list_automated_sessions` history, then `get_session_trades(record_id=...)` with pagination (`offset`/`nextOffset`, `total`).
- OOS window returns `customStats:{}` (empty) → `passRate*` = 0. Use **netPnl** as the OOS robustness metric, not pass rate.
- `run_backtest` args: `script_id`, `ticker`, `data_provider`, `interval` (1/3/5/15/30/60/240/1440), `start`, `end` (ms epoch), `starting_balance`, `save_session`, `inputs` (map of script input names). Wrong key names → `-32602 Input validation error`.
- SSL handshake timeouts happen sporadically — wrap each cell in retry (3 attempts), resume from done-set.

### Plot per-combo graphs from trades (USER PREFERENCE — "sab ke graf", "mix mat dena")

The user wants **one graph per combo**, not one combined/mixed chart. For each top combo: fetch trades (save_session route), then plot a 3-panel figure (equity curve + drawdown% + daily PnL bars) with `8%/6%` target lines. Verify with `vision_analyze` before sending. Save as `SL{sl}_TP{str(tp).replace('.','_')}_equity_dd.png`. Use Termux python (has matplotlib/pandas), NOT proot python (no matplotlib).

### Risk/reward sanity check before claiming (REINFORCED)

For a tiny-TP/wide-SL grid cell, compute break-even win rate `BE = SL/(SL+TP)` and compare to actual win rate. This session SL500/TP37.5: BE = 500/537.5 = 93.0% but actual 88.9% < BE → long-run losing despite 86.8% pass rate and +$3710. Max DD 15-22% also breaches prop 10% limit. A high pass-rate cell with win rate below break-even is a **mathematically losing strategy** — report it, don't crown it.

### Compute budget management

- Free plan = 600s/day. A 4h 2-month run ≈ 2-3s compute but ~30s+ WALL-CLOCK per cell (launch + poll + fetch + retry). A 42-combo dense grid therefore needs 4-5 background workers (~10-13 cells each) using the done-set resume pattern — compute quota is not the constraint, worker wall-time is. A 6-month run costs more and hits the order cap on high-frequency settings — check budget before each sweep, and prefer the short window for the sweep + OOS for the winner.
- Check remaining budget before a sweep (list sessions / knowledge about compute); runs already computing finish normally and script saves keep working when quota is hit.

### Parallel validation workers (USER PREFERENCE — "sab ko kam bat do")

When validating a candidate combo, the user wants ALL workers dispatched at once, not sequential. Run the three OOS checks in parallel as separate `opencode run` processes (background, notify=true):
1. OOS earlier-window
2. Cross-instrument (2nd instrument)
3. Long-window + SL variant comparison

Each as its own background `terminal` process. They share the same MCP server (compute budget is the constraint, not tool access) — 3 parallel runs is fine on Free's 2-parallel-run limit only if they queue; otherwise stagger to 2 at a time. Give each worker a self-contained task file (`task_*.txt` under `$HOME`) and a clear verdict prompt. Collect all results before concluding — one worker's timeout does not invalidate the others.

## Common bugs to watch for

1. **`np.maximum.reduce` propagates NaN** — user's pandas `.max(axis=1)` skips NaN. If rewriting ATR in numpy, `pc = close.shift(1)` starts NaN → `np.maximum.reduce` gives all-NaN TR → all-NaN ATR → `risk > 0` always False → 0 trades silently. FIX: use pandas concat+max(axis=1) or use `np.nanmax`.

2. **Delta API param names**: `/v2/history/candles` needs `start`+`end` (unix seconds), NOT `from`/`to`. Wrong names return `bad_schema` with `"start is required"`.

3. **Delta 4000 candle cap per request**: 365d 1h = 8760 candles → needs pagination (2000 candles × ceil(8760/2000) requests).

4. **`~/bt_cache/*.csv` has two timestamp formats mixed** — some older cache files were written with unix seconds (`1776686400,...`), newer ones with ISO datetime strings (`2025-10-03 15:00:00,...`). Naive `np.genfromtxt(..., names=True)` followed by `D["time"].astype(np.int64)` raises `ValueError: invalid literal for int() with base 10: np.str_('2025-...')` on the ISO file. FIX: detect first row and branch —
   ```python
   first = str(D["time"][0]).strip()
   if first.isdigit():
       t = D["time"].astype(np.int64)
   else:
       from datetime import datetime
       t = np.array([int(datetime.fromisoformat(str(x)).timestamp()) for x in D["time"]])
   ```
   Wrap in try/except with cache delete + refetch as fallback. Do not silently skip — the user has both formats in production.

5. **Compounding PnL requires ratio math, not addition** — when a strategy trades multiple times and PnL must compound, use `eq *= (1 + ret)` where `ret = (exit-entry)/entry` for longs and `ret = (entry-exit)/entry` for shorts. Do NOT use `eq += (exit-entry)` — that gives BTC-scale PnL (e.g. `-286%` on BTCUSD 4h from a single losing trade) instead of true return percentage. For percentage-based return reporting, initialize `eq = 1.0` and report `(eq-1)*100`, or track `eq_ratio` separately from cash.

6. **Classic Supertrend has two flavors and only one produces flips.** The "naive" version (`if close < lower_basic: direction=-1`) never flips because `lower_basic` isn't a ratcheting band — close sits above it in a downtrend so direction stays `1` forever, giving ~1 trade/year instead of 40-100. Correct classic Supertrend maintains *final* upper/lower bands with ratcheting:
   ```python
   if basic_upper[i] < final_upper[i-1] or c[i-1] > final_upper[i-1]:
       final_upper[i] = basic_upper[i]
   else:
       final_upper[i] = final_upper[i-1]   # ratchet down on bearish side
   # mirror for final_lower
   # flip only when close pierces the ratched band:
   if prev_dir == 1 and c[i] < final_lower[i]: dir = -1
   if prev_dir == -1 and c[i] > final_upper[i]: dir = 1
   ```
   Initialize `dir=1` at the first valid ATR index (not at index 0, which is NaN-warmup). If your Supertrend gives <10 trades over 365d of hourly data on BTC, the band ratchet is missing — not the parameters.

7. **ADX with `wma(wma(x,n),n)` returns all-zero when x has leading NaN.** In `wma(wma(h-l,n),n)` the inner WMA's first `n` values are NaN; the outer WMA then treats those as NaN and outputs NaN, then often converts to 0 downstream. Symptom: `adx[-5:]` prints `[0. 0. 0. 0. 0.]` — every entry filter using `adx > threshold` fires forever or never. If you can't get working ADX in a short time, drop it from the entry gate rather than ship broken. Simple EMA filter + trend flip is often enough.

## Example bug from 2026-10-02

User gave `ema300_tl_swing_backtest.py`. I rewrote ATR with numpy for speed:
```python
# WRONG — propagates NaN
pc = df["close"].shift(1).values  # pc[0]=NaN
tr = np.maximum.reduce([...])     # all NaN
```
Funnel debug showed 142 signals generated but 0 positions opened (because `risk = atr[t] * atr_mult = NaN * 2 = NaN`, and `NaN > 0` is False).

Fix: use pandas concat+max(axis=1) which skips NaN, and ewm(alpha=1/n).mean() which propagates NaN-safe.

## User interaction

- User language: Hinglish/Gujarati
- Wants short bullets + tables
- Wants the diff printed BEFORE running (not after)
- User will reject any strategy modification — reproduce exactly
- If user says "Option X" referring to a numbered list, follow it literally
