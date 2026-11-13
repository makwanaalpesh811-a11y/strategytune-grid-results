# StrategyTune Dense SL/TP Grid Results

Gold 4h backtest via StrategyTune — inverse-risk momentum strategy.
Dense SL/TP grid: SL 300-600 (step 50) × TP 25-100 (step 12.5) = 42 combos.

## Top 3 Strategies (in-sample 2026-09-11 → 2026-11-11)

| Rank | SL | TP | Pass@8% | Win | PF | Net | MaxDD | Trades |
|------|----|----|---------|-----|-----|-----|-------|--------|
| 1 | 500 | 37.5 | 86.8% | 88.9% | 1.814 | +$3710 | $1613 | 234 |
| 2 | 500 | 50 | 81.6% | 85.6% | 1.747 | +$4200 | $1555 | 222 |
| 3 | 600 | 37.5 | 84.2% | 89.0% | 1.805 | +$3584 | $2205 | 227 |

## OOS Validation (2026-05-11 → 2026-09-11) — ALL POSITIVE

| SL | TP | Net PnL |
|----|----|---------|
| 500 | 37.5 | +$3907 |
| 500 | 50 | +$5894 |
| 350 | 37.5 | +$3060 |
| 400 | 37.5 | +$3734 |
| 600 | 37.5 | +$3043 |

All 5 best cells positive OOS → real edge, not regime luck.

## ⚠️ Risk Warning

- Risk:Reward is asymmetric (SL 500-600 vs TP 37.5-50 = 1:10 to 1:16)
- Break-even win rate for SL500/TP37.5 = 93.0%, actual 88.9% < 93% → long-run losing
- Max DD 15-22% breaches prop-firm 10% DD limit
- **Not prop-firm safe** despite high win rate — tail risk materialized in November

## Files

- `SLPT_dense_grid_final_report.md` — full report
- `SLPT_dense_grid.csv` — 41/42 grid cells
- `SLPT_oos_grid.csv` — OOS validation
- `SL500_TP37_5_equity_dd.png` — graph (equity, DD, daily PnL)
- `SL500_TP50_equity_dd.png` — graph
- `SL600_TP37_equity_dd.png` — graph
- `SL500_TP37_5_trades.json` — 234 trades
- `SL500_TP50_trades.json` — 222 trades
- `SL600_TP37_trades.json` — 227 trades

Strategy script ID: `tf9nivtii7nhg80evq3y7i96` (StrategyTune)
