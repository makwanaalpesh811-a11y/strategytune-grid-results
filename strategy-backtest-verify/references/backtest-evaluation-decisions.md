# Backtest evaluation decisions

Rules for judging whether a backtested config is worth recommending. Apply AFTER the run, before reporting to the user.

## Luck / significance test — the null is per-chunk BREAK-EVEN, not 50%
A binomial z-test against 50% is too generous for a strategy with asymmetric RR: the break-even win rate is `1/(1+RR)`, which for a low-RR strategy is ~52-58%, not 50%. Test against the pooled break-even win rate (weight by trades per chunk), and per chunk against that chunk's own BE.
- `z = (win_rate - BE) / sqrt(BE*(1-BE)/n)`; pooled BE = `sum(BE_c * n_c)/N`.
- Concrete impact (Bybit funding-capture, 366 trades, 70.8% win): z=7.95 vs null 50%, but **z=7.00 vs pooled BE (52.5%)** — still highly significant. Per-chunk: C1 z=0.22 NOT significant (n=5 only), C2-C6 z=2.4-4.4 significant.
- Report per-chunk and pooled, and flag chunks with tiny n as not significant — a single chunk with n=5 at 100% is luck, not evidence.
- If the strategy is 1 trade/day and each trade is at a distinct funding time, clustering by funding time does NOT dilute the test (366 trades = 366 distinct clusters). Only cluster-dilute when multiple trades share one funding time.

## Watchlist/selection look-ahead — build on TRAIN, test on TEST
If a watchlist, star-rating, or "top coins" list is built from FULL-period data, its backtest is optimistic. The list itself must be selected only on the train window, then applied unchanged to the test window.
- Build watchlist from TRAIN only (e.g. first 70% by time): same per-chunk BE threshold + net>0 + min-trades.
- Apply that TRAIN watchlist to TEST — this is the honest out-of-sample number.
- Compare TRAIN-watchlist-on-TEST vs FULL-watchlist-on-TEST; a large gap = look-ahead bias. Report BOTH, and report the TRAIN one as the honest OOS.
- Concrete impact (Bybit funding-capture, 331-coin watchlist): FULL-period watchlist on TEST = 68.1% win / +$722.87 / DD -4.56%; TRAIN-only watchlist on TEST = **60.6% / +$214.11 / DD -14.92%**. 125 of 331 coins (37.8%) came only from full-period data — the look-ahead inflated net ~3.4x.
- A FULL-watchlist-on-FULL run (in-sample) is even more inflated: 68.1% / +$2,452.67 / DD -2.51% on the same data — do not quote it as the strategy's edge.

## Consistency (monthly-positive ratio) — user's hard gate

Buckets daily PnL by YYYY-MM, counts months with PnL > 0, divides by total months.
- `>= 75%` (9/12 months positive) → PASS the gate, candidate.
- `< 75%` → REJECT regardless of total net. A +net with 11/23 positive months (48%) is a luck profile: it made its money in a couple of big months and bled the rest.

Why the gate matters: prop-firm evaluations are a 1-2 month window. A strategy that only works in 1-2 months of a year can pass by timing luck, then fail the funded account — the user explicitly rejects this.

## Walk-forward (train/test split)

- Fit on the train window, hold parameters FIXED, evaluate on the test window.
- Config robust if it is strong on BOTH windows (e.g. ETH-D4 Lb=40/MA50/vol1% was #5 of 336 on OOS while the best-train config collapsed to -70% DD on OOS).
- Best-train config that fails OOS = overfit, reject (e.g. +21% train → -19% OOS).
- Report OOS result prominently; do not bury it under the train number.

## Cost model completeness

A pass-rate claim needs: fee + slippage + funding (if perpetual). Omitting funding/slippage inflates the pass rate; an optimistic engine is not a valid pass claim. See walk-forward-costs.md for the full cost recipe.

## Funding-capture specific (Delta)

Funding events = rate CHANGES in the FUNDING:<SYM> 1h series (not every row; the rate repeats between settlements). Interval = most common change spacing (8h/4h/1h — detect, don't hardcode). Capture the funding payment, but the PRICE MOVE over the hold window is usually larger than the fee — a naive long/short-at-event strategy tends to net negative even when total funding captured is large (AINUSD: $9010 funding vs -$1101 net, because price move + $166 fees exceeded the funding edge). Do not report "funding captured" as profit; report net after price move + fees.