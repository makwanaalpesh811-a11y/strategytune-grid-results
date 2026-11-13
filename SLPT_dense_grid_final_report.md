# Dense SL/TP Grid — Final Report (Gold 4h)

**Date:** 2026-11-13 | **Window (in-sample):** 2026-09-11 → 2026-11-11 | **OOS:** 2026-05-11 → 2026-09-11

## Grid Results (in-sample, pass rate @8% target)

### Top 3 (best combos)
| SL | TP | Pass8 | Win | PF | Net | MaxDD | WorstDay | Trades |
|----|----|-------|-----|-----|-----|-------|----------|--------|
| 500 | 37.5 | 86.8% | 88.9% | 1.814 | +$3710 | $1613 | -$502 | 234 |
| 500 | 50 | 81.6% | 85.6% | 1.747 | +$4200 | $1555 | -$502 | 222 |
| 600 | 37.5 | 84.2% | 89.0% | 1.805 | +$3584 | $2205 | -$604 | 227 |

### TP37.5 line consistent (86.8% at SL350/400/450/500)
| SL | TP | Pass8 | Win | PF | Net | MaxDD |
|----|----|-------|-----|-----|-----|-------|
| 350 | 37.5 | 86.8% | 87.9% | 1.590 | +$3095 | $1771 |
| 400 | 37.5 | 86.8% | 87.9% | 1.520 | +$2856 | $2069 |
| 450 | 37.5 | 86.8% | 88.3% | 1.611 | +$3180 | $1877 |
| 500 | 37.5 | 86.8% | 88.9% | 1.814 | +$3710 | $1613 |
| 600 | 37.5 | 84.2% | 89.0% | 1.805 | +$3584 | $2205 |

## OOS Validation (out-of-sample, 2026-05-11 → 2026-09-11)
| SL | TP | Net PnL | WinRate | Note |
|----|----|---------|---------|------|
| 500 | 37.5 | +$3907.7 | ~89% | Positive OOS |
| 500 | 50 | +$5894.5 | ~86% | Positive OOS |
| 350 | 37.5 | +$3060.4 | ~88% | Positive OOS |
| 400 | 37.5 | +$3734.0 | ~88% | Positive OOS |
| 600 | 37.5 | +$3043.4 | ~89% | Positive OOS |

**All 5 best cells positive in OOS → real edge, not regime luck.**

## Risk Analysis (CRITICAL)
- Risk:Reward ratio is BAD: SL 500-600 vs TP 37.5-50 → 1:10 to 1:16
- Break-even win rate for SL500/TP37.5: 500/(500+37.5) = 93.0%
- Actual win rate: 88.9% < 93.0% → **mathematically losing strategy in long run**
- Max drawdown 15-22% — **breaches 10% prop-firm DD limit**
- November: sharp equity drop (tail risk materialized)
- **Verdict: High win-rate illusion, but NOT prop-firm safe. Risk/reward too asymmetric.**

## Files
- Grid data: `Hermes_Almari/02_DATA/SLPT_dense_grid.csv` (41/42 cells, SL550/TP37.5 SSL fail)
- OOS data: `Hermes_Almari/02_DATA/SLPT_oos_grid.csv`
- Trades: `SL500_TP37_5_trades.json` (234), `SL500_TP50_trades.json` (222), `SL600_TP37_trades.json` (227)
- Graphs: `SL500_TP37_5_equity_dd.png`, `SL500_TP50_equity_dd.png`, `SL600_TP37_equity_dd.png`
