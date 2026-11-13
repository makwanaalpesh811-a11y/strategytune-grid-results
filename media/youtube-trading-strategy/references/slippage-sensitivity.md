# Slippage / Spread Sensitivity Table

For any backtest on a sub-15m timeframe strategy (HFT, scalping), the reported return is only credible if it survives realistic spread + slippage.

## Why this matters

YouTube EA demos almost always quote **zero slippage** on an unrealistic spread. A 1-minute strategy makes 30+ trades/day, so even 5 pips of slippage per trade × 30 trades × 30 days = thousands of pips lost — often enough to flip a positive result into a losing one. This session's ETHUSD 1m HFT backtest held +398% return even at 20 pip spread + 10 pip slip, which is why it wasn't dismissed as garbage; but that was the outlier, not the norm.

## Required scenarios (run all, present all)

Always run at least these 3 combos so the reader can judge robustness:

| Scenario | Spread | Slippage per trade | Use |
|---|---|---|---|
| **Video claim** | strategy's own value | 0 | Upper bound |
| **Realistic** | 2× video spread | 20% of SL | Middle estimate |
| **Stress** | 3× video spread | 50% of SL | Worst case for the session |

For FX majors: 1–3 pips spread, 1–2 pips slippage. For ETH: 5–20 pips spread (=$0.05–$0.20), 5–15 pips slippage. For US30 index: $3–$10 spread, $1–$4 slippage. For Gold XAU: 20–100 points spread, 10–40 points slippage.

## Template skeleton

```python
def run_backtest(spread, slippage, step=60):
    # entry: adjust by slippage in the adverse direction
    # long entry: entry_price = close + slippage
    # short entry: entry_price = close - slippage
    # exit at SL: pnl computed against exit_p = sl_price - slippage (long) / + slippage (short)
    ...

scenarios = [
    (0.05, 0.00, "Video claim"),
    (0.10, 0.05, "Realistic"),
    (0.30, 0.15, "Stress"),
]
for s, sl, name in scenarios:
    r = run_backtest(s, sl)
    print(f"{name:12s} spread=${s} slip=${sl} ret={r['return']:+.1f}% PF={r['pf']:.2f} DD={r['max_dd']:.2f}%")
```

## Read the result

- Return stays **positive and above 20% annualized** across all three scenarios → strategy is robust to cost assumptions. Test on a different symbol to rule out survivorship.
- Return flips sign between video-claim and realistic → **reject**. It's a commission/slippage machine.
- Return halved but stays positive → note it in the report, don't hide it.

## Sample: ETHUSD 1m HFT EMA50+Trail (Dec 2025 → Aug 2026, 8 months)

| Spread | Slippage | Return | Max DD | Trades | PF |
|---|---|---|---|---|---|
| $0.05 | $0.00 | +435% | 0.14% | 487 | 52.0 |
| $0.10 | $0.00 | +432% | 0.26% | 481 | 27.4 |
| $0.10 | $0.05 | +427% | 0.30% | 481 | 23.7 |
| $0.20 | $0.10 | +410% | 0.62% | 472 | 12.3 |
| $0.30 | $0.15 | +398% | 0.95% | 468 | 8.4 |

Robust: return only drops 8 percentage points across 6× spread increase. Rare — flag it as outlier-positive and confirm on ADA or another symbol before betting real money.

## Common traps

- **Not applying slippage to entry** — you must pay spread at entry too, not just at exit.
- **Using same SL pips for long and short** — asymmetry matters when spread is 20% of SL.
- **Reporting only the video-claim row** — the whole point of the sensitivity is transparency.
- **Forgetting to also run it at step=1** (every 1m) — stepping by 60 hides the intra-hour trades where slippage bleeds the most.
