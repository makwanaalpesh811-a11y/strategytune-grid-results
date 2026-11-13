# Walk-Forward & Cost Modeling (out-of-sample honesty)

These rules apply when a backtest claims a prop-firm pass rate or any "will it keep working" claim.

## Clean walk-forward
- Search on an EARLIER window (train), pick the best config, then test it UNCHANGED on a LATER window (test). Report BOTH windows — never report train numbers as the strategy's result.
- A config that wins only the train window is OVERFIT. Prefer the config that HOLDS out-of-sample.
- Example (ETH, 2026-11-11): Lb=10/lo/no-MA/no-VT was +57.1% train / FTMO 63.3%, but on test -10.9% / FTMO 3.7% (DD -70%). ETH-D4 (Lb=40/ls/MA50/vt=0.01) ranked #5 of 336 on test with FTMO 88.2% / FN2 77.0% WITH costs.
- Rule of thumb: bare short-lookback momentum (Lb~10, no MA, no vol-target) is overfit; add a trend/vol filter (MA + vol-target) and the config becomes robust.

## Costs to model
- Crypto perps: fee 0.10%/side + slippage 0.05%/side + funding 0.01% per 8h = 0.03%/day on a held position.
- Funding is material on positional holds and frequently omitted (optimistic). Apply all three.
- NIFTY: flat Rs 45 + 0.026% notional per round trip.

## Fee model is VENUE-SPECIFIC — never reuse one venue's fee on another
The fee model lives in the engine's `FEE_PCT` and is NOT portable across exchanges. Before reusing an engine on a new venue, verify the venue's taker/maker fee structure and whether any entry-free offer applies. A "funding capture" engine written for one venue silently undercharges on another.
- Delta India perpetuals: 15-min entry-free offer → **exit-only 0.05%** (correct for Delta).
- Bybit USDT perps: **no entry-free offer** → **entry + exit taker ≈ 0.055% × 2 = 0.11%** round trip.
- Symptom of a wrong fee model: the backtest looks fine but the user, who trades the second venue, knows the fee is higher — check `fee_pct` in the engine's output rows before quoting net.
- Concrete impact (Bybit 1-trade/day, $200 notional): exit-only 0.05% gave +$299.71 / 70.8% / DD -2.61%; correcting to entry+exit 0.11% gives **+$255.79 / 66.7% / DD -2.90%** (12/13 months still positive). Extra fee = 0.06% × notional per trade ($0.12 at $200 notional).

## Pass-rate / days-to-pass reporting
- Report median/p25/p75/p90 days-to-pass, not just pass-rate. Capital size does NOT change the % distribution (k scales proportionally).
- Active-days definitions differ: `pos!=0` (held) vs `pnl!=0` (any P&L). Report which you mean.
- Why a daily momentum strategy trades less in some years: the trailing exit BLOCKS the exited direction until momentum flips; with a long lookback, flips are rare in trending years. Count MA-blocked vs trail-exit vs active per year at the engine level to settle it.

## Prop-firm rule sets (used in this class)
- FTMO 2-Step P1: 10% target / 5% daily loss / 10% static DD / 4 min days.
- FundedNext 2-Step P1: 8% target / 5% daily / 10% DD / 5 min days + Quick-Strike consistency <40%.
- Options are NOT available on prop-firm forex/CFD venues — futures/CFD only.
