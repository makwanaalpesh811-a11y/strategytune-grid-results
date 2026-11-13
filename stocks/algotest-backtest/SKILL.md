---
name: algotest-backtest
description: Use for AlgoTest login, master, or ETH grid backtest.
---

# AlgoTest (algotest.in) — Login, Master, Grid Backtest

## Login (verified 2026-11-07)
- Credentials: phone `7878104500` + password (env `ALGO_PHONE`/`ALGO_PASS` — code me hardcoded NAHI).
- **Playwright + Firefox** in proot-distro Ubuntu (Chromium headless-shell crashes in proot).
- `POST https://api.algotest.in/login` → 200 `{"login":true}`. No OTP/2FA. Auth cookies: access_token_cookie + csrf_access_token.
- Script: `~/myproject/login_algotest.js` (proot).

## Master (done 2026-11-07)
- **142 endpoints**: Account 27, Execution 23, Marketplace 21, Strategy 16, Broker 14, Backtest 14, Signals 11, Portfolio 8, Crypto 7, Market Data 1.
- API base: `api.algotest.in`. Probe: 59×200, 1×404, 1×403 (plan-gated).
- **ETH options**: Delta Exchange, 33 underlyings, 266 ETH contracts across 7 expiries. ETH spot ~$2244.
- Reuse: `node algotest_explore.js` (state se, no login); `SKIP_PAGES=1` fast; `ETH_BACKTEST=1` naya backtest.

## ETH Straddle Sell Grid Backtest (done 2026-11-07)
- **Fixed**: Entry 22:00 IST, Exit 07:00 IST, sell ATM CE+PE (straddle), 365 days (Nov 2025–Nov 2026).
- `IntradaySameDay` = correct type (BTST holds ~33h, galat). Expiry=Today rolls nearest daily. PnL USD (UI ₹85/dollar). Lot=1 = 0.01 ETH contract.
- **28 core combos + 4 sizing = 32 runs**. Results in `~/myproject/grid_results.json`, `ETH_STRADDLE_GRID_REPORT.md` (copied to `/sdcard/Hermes_Almari/01_STRATEGY/docs/`).
- **Best balance (recommended): ATM / SL 50% premium / re-entry ON×2** — Win 69.86%, PF 2.477, Calmar 16.70, P/L ₹1,618, MaxDD ₹-97.
- **Max PF: OTM2 / SL 50% / RE ON×1** — PF 3.174, Win 61.10%, R:R 2.02, P/L ₹1,062.
- Sizing: P/L + DD scale linearly (3 lots = 3× both). Capital $1k ≈ 1005 lots.
- Slippage/fees NOT modelled.

## Video UI Steps (Leg Builder → Lazy Leg)
1. Segment Options → Lot 1 → Position Sell → Call (leg1) + Put (leg2) → Expiry Today/Weekly → Strike Type ATM (ATM/OTM1/OTM2).
2. Add Leg ×2. Har leg toggles: Target Profit, Stop Loss, Trail SL, Re-entry Tgt/SL, Simple Momentum.
3. Units dropdown: Points (Pts), Underlying Pts, Percent (%), Underlying %, Delta (pts), Delta (%).
4. Re-entry options: RE ASAP, RE ASAP↔, RE MOMENTUM, RE MOMENTUM↔, RE COST, RE COST↔, Lazy Leg.
5. Lazy Leg form: name "lazy1", create. Values 0 = invalid (turant exit) — set real values.
6. Video flow verified: Leg#1 Call → Leg#2 Put → re-entry dropdown → lazy1 Weekly → toggles OFF→6 ON.

## Save strategy (verified 2026-11-08)
`POST /strategy` = SAVE endpoint (NOT a backtest payload). Body schema (strict — extra top-level fields cause 400):
```json
{"name": "...", "folder": null, "strategy": {
  "Ticker": "DELTA_ETHUSD", "StrategyType": "StrategyType.IntradaySameDay",
  "ListOfLegConfigs": [ {CE+PE sell, ATM, Lot 1, SL 50%, Reentry Immediate x2, Expiry Today, Entry 22:00/Exit 07:00} ],
  "EntryIndicators": {...}, "ExitIndicators": {...}},
  "attributes": {"template": "Straddle920", "positional": false}}
```
- Auth: cookies from `algotest_state.json` (access_token_cookie + csrf_access_token) + **`X-CSRF-TOKEN-ACCESS`** header (NOT `X-CSRF-Token`).
- **Save from .algtst.json export:** body = `{name, folder: None, strategy, attributes}` — DROP top-level `version` (extra top-level keys → 400). `save_stegelsell.py` is the working template (re-login first: token gets revoked between sessions; creds via env ALGO_PHONE/ALGO_PASS, not hardcoded).
- Access token gets **revoked** between sessions — re-login (login_algotest.js, now saves storageState) before save. `POST /auth` with Bearer is NOT the same as cookie auth.
- Save returns `200 {"_id":"..."}`; verify via `GET /strategy/<id>` (name + template match).
- Duplicate: save with a DIFFERENT name (e.g. "FULL GRID BEST ...") — never overwrite a saved strategy the user asked to keep.
- **Rename strategy in place (verified 2026-11-12):** `PUT /strategy/<id>` with body `{name, strategy, attributes}` (NO `folder`, NO `_id` — both cause 400 "Additional properties are not allowed"; POST tolerates `folder`, PUT does NOT). Body accepts `version` optionally. PUT returns `200 {"_id":"..."}`. Verify via GET `/strategy/<id>` (name round-trip). In-place rename keeps the SAME id — no duplicate created. Example: 'Stegel sell' -> '🖤🖤2' (id `6af5e3317a07369cc42bf817`) — PUT 200, GET name `🖤🖤2`, template/ticker/legs all unchanged. Script: `rename_stegelsell.py`.
- **Emoji-name convention (user preference):** user names saved strategies with emoji runs ("🖤🖤🖤", "🩷🩷🩷") — use the emoji string VERBATIM as the strategy `name`. Emoji must round-trip through save+verify (GET /strategy/<id> returns the same emoji; Big's verify checks name match — if it doesn't match, the payload was mangled).
- Full-grid best (16/17 runs): ATM/SL50/RE×2, 22:00→07:00 — Profit 19.04, Win 69.86%, PF 2.477, DD -1.14.
- **Saved so far (verified 200 + name match):** FULL GRID BEST ATM SL50 RE2 (ETH `6aefeb264f1f87dcfb3838ce`), BTC v02 Short Strangle OTM5 SL200 RE1 (`6af03b7ca326307a85995ff6`), BTC GRID BEST OTM5 SL50 RE1 (`6af04cadc8fb07c149e057ae`), 🖤🖤🖤 ETH ATM SL50 RE2 (`6af14a94417e0cb88a4f0ee5`), 🩷🩷🩷 BTC OTM5 SL50 RE1 (`6af14b24f7cd1afea891a639`), 🩷🩷🩷 OTM3 (`6af1725fa1784f0b8e6a4715`), ❤️‍🩹❤️‍🩹 prop-firm OTM5 SL30 (`6af340389659699b9cf8874a`), 🎯🎯🎯 PROP OTM5 SL30 (`6af330eef9a425d423b7cfc6`), **Stegel sell** (`6af5e3317a07369cc42bf817`, ETH ATM straddle sell, lazy-leg re-entry, SL130% — from `stegelsell.algtst.json`, 2026-11-12).
- **BTC grid day-time best (21 runs):** 09:15→17:29 | OTM5 | SL 50% | RE AtCost×1 — 675 trades, $2,471.54, Win 63.56%, PF 3.699, DD -$61.42. 09:15 = India open (IST), 17:29 = before Delta daily expiry (0DTE strangle, no overnight gap).

## Off-day analysis (verified 2026-11-09)
- ETH (entry 22:00→exit 07:00 next day) Sunday 22:00 entry skip = only net-losing weekday (52 trades, -$1.08, PF 0.61). Skip → 365→313 trades, profit $19.04→$20.12, PF 2.477→2.986, DD -1.14→-0.82, win 69.86→74.12%.
- BTC (same-day 09:15→17:29) NO day is net-losing — every weekday positive. Removing any day only cuts profit; "DD kam + profit zyada" impossible via day filter alone. Best compromise = Sunday skip: PF 3.70→4.09, DD -61.42→-50.24, profit -$26 (-1%). Mechanical workaround for both: Sunday off + lot 100→102 (~2% bigger) → profit ~$2,494 + DD -$51.
- BTC per-day PnL (675 trades): Mon $792, Tue $409, Wed $353, Thu $252, Fri $413, Sat $226, Sun $26. Sun is weakest, not losing.
- ETH off-day = ENTRY-date based (Sunday 22:00 entry), NOT exit-date. Exit (Mon 07:00) is a consequence of the Sunday entry — skip entry = skip trade.
- Caveat: ETH Sunday sample only 52 trades / -$1.08 — statistically fragile; paper-trade before live.
- Files: `off_day_analysis.py`, `off_day_results.json`, `OFF_DAY_REPORT.md` (proot ~/myproject).

## OTM strike sweep + fee adjustment (BTC 🩷, verified 2026-11-09)
- Sweep: OTM1-5 × SL50 × RE AtCost×1, 09:15→17:29, Lot 100. Runner `btc_otm_sweep.js`, results `btc_otm_sweep_results.json`, fee model `btc_otm_fee_analysis.py`, report `BTC_OTM_FEE_REPORT.md`.
- Delta option fee: min(0.010% notional, 3.5% premium) per side + 18% GST. The 3.5%-of-premium cap binds on 62% (OTM1) to 96% (OTM5) of transactions at 0.010% — so for cheap premium the fee is effectively ~3.5% of premium per side (~8.3% round-trip incl GST), NOT notional-based. Rate 0.010% vs 0.030% barely changes OTM4/OTM5.
- Fees eat ~40-60% of gross profit across all OTM levels (user's ~50% suspicion correct strategy-wide, NOT OTM5-specific).
- Gross vs net (0.010% + GST): OTM1 gross $4719.61→net $1853.47 (PF 1.458, fee 60.7%); OTM2 $4057.80→$1758.83 (1.530, 56.7%); OTM3 $3633.16→$1867.00 (1.750, 48.6%); OTM4 $3074.36→$1741.37 (1.967, 43.4%); OTM5 $2471.50→$1444.41 (1.990, 41.6%).
- Best net profit: **OTM3** ($1867 net, holds at 0.030% too: $1617). Best risk-adjusted: **OTM5** (PF 1.99, DD -$94). Best balance: OTM4.
- OTM3 last-30-day entry premium: CE avg $81.97, PE avg $92.06, total avg $174.02/BTC. Lot 100 = 0.1 BTC → avg $17.40/day. 1 lot (0.001 BTC) = $1.74/day avg. Avg is 67.3% of the 675-day average (258.72) — premium currently BELOW long-run norm. Volatile (min $34.92, max $577.50, 30 Oct spike). Sizing: use low-end (~$5-8/lot), not average-based.

## Combined ETH+BTC daily net PnL (verified 2026-11-09)
- `combined_equity.py`, `combined_summary.json` (net_series: date/eth/btc/net/equity/dd/cum_win_rate), `combined_equity_curves.png`, `combined_equity_inr.py` (₹85/$ rate) → `combined_equity_inr.png`.
- Common window 2025-11-06→2026-11-05, Sunday off both, 313 overlapping active days. NET = ETH_pnl + BTC_pnl on entry-date.
- Win days (NET>0) 192, loss days 121, win rate 61.34%. Total NET $760.96 (ETH $20.12 + BTC $740.84). Max DD -$49.71. Avg win +$5.88, avg loss -$3.04. Best day 2025-12-01 +$76.61, worst 2026-03-23 -$24.89. Max 8 consecutive wins, 6 consecutive losses.
- Dono-profit (both>0) 135 days, dono-loss (both<0) 28, mixed 146. Both-profit days list available in net_series.
- INR (₹85/$): total ₹64,682, max DD -₹4,225, avg win ₹500, avg loss -₹258, best day ₹6,512, worst day -₹2,116.
- Chart is proot-internal: host copy at ~/combined_equity_curves.png + ~/combined_equity_inr.png (copy from rootfs path).

## Prop-firm research + strategy (verified 2026-11-09)
- **Prop-firm + options = NO** (legally unavailable). FTMO/FundedNext/TopStep = forex/indices/commodities CFD/futures ONLY, no options. Crypto prop-firms (Breakout/Kraken, HyroTrader) = perps/spot only, no options. Crypto options product doesn't exist in any prop-firm.
- **India prop-firm = grey** — FundedNext on RBI Alert List, payouts taxable, FEMA/LRS issue. **Delta Exchange India / CoinDCX = active ED FEMA probe** (as of 2026-11-09) — real unresolved risk.
- Best actionable route: (1) paper/demo validate first, (2) own capital on Delta Exchange India (strategy's only direct home, small size, clean tax trail), (3) NSE/BSE F&O (SEBI-regulated, but ₹15L min contract, one weekly expiry per exchange, higher STT), (4) US equity-options prop only if pivot to US equities.
- Prop-firm rule sets used: FTMO 2-Step P1 = 10% target / 5% daily loss / 10% static DD / 4 days; FundedNext 2-Step = 8% / 5% / 10% / 5 days + Quick Strike consistency <30%.
- Prop strategy built & PASSED: `🎯🎯🎯 PROP OTM5 SL30` — BTC 0DTE short strangle (Sell OTM5 CE+PE), 09:15→17:29, Lot 100, SL 30%, RE AtCost×1, ID `6af330eef9a425d423b7cfc6`. Backtest (675 days, fees+GST incl): gross $2373.64 win 75.7% DD -$41.14; net $1260 win 60.6% PF 2.11 worst day -$38.08 net maxDD -$67.82. Walk-forward 675 windows: FundedNext @$800 = 95.6% PASS, FTMO @$800 = 95.3%, zero daily-loss/10%-DD violations. Saved as ❤️‍🩹❤️‍🩹 (`6af340389659699b9cf8874a`).
- Caveat: FTMO/FundedNext are forex/CFD venues — strategy passes their RULESET but actual venue is Delta India (crypto). It's a backtest-level simulation, not a real funded account.

## Futures strategies (NIFTY + crypto perps, verified 2026-11-11)
- AlgoTest futures leg types exist: `LegType.FUT` (futures), `LegType.FUT_P` (perpetual FUT), `LegType.CASH`. DefaultLeg uses InstrumentKind + LotConfig Quantity.
- **User goal (hard):** FUTURES-only strategy that passes prop-firm rules (options NOT allowed for prop).
- **Morning entry-cap is THE key lever.** Full-session configs (09:15→15:14) pass only 10–17% of FTMO/FN2 windows; capping entries to ≤10:00/≤09:45 lifts pass-rate to 58–80% with DD ≤7%. When a futures strategy fails, test an entry cutoff BEFORE throwing away SL/TP/re-entry ideas.
- **`StopMonitoringTime` semantics (verified from frontend source + tooltip):** value = minutes from midnight. After the cutoff NO new entries/re-entries and NO SL/TP checks run; open positions ride to the exit time. The separate "No Re-entry After" setting applies ONLY to re-entries (does NOT stop new entries) — so `StopMonitoringTime` is the real full-stop cutoff, NOT "No Re-entry After".
- **NIFTY expressible winners (saved, real IDs):** `NIFTY-BUY0.6-TP0.6-SL0.30-RE2` (`6af38f84d2d2234d8ec4ab11`) + SL0.25/0.35-RE2 + SL0.30/0.35-RE1 (`6af38f85ea1534023a425742`, `6af38f875b98a963098f4de5`, `6af38f88ad2b6936944116e3`, `6af38f8962f5daafc79e9519`) — all `StopMonitoringTime: 720`, exit 14:30, momentum %down 0.6 entry, SL 0.30%, TP 0.6%, RE×2, lot 1. FTMO 0.71 / FN 0.56 (in-sample; synthetic basis path ~0.90 corr).
- **Crypto perps PASS (research-grade):** ETH-D4/D8/D7/D5, BTC-D1, SOL-D6, BTC-I1 (FTMO up to 88.2%, FN2 up to 77.0%) — but they rely on MA / vol-target / long-short which the builder CANNOT express (see section below), so AlgoTest-saved copies are risk shells only; the faithful backtest is the local engine (`daily_engine.py`).
- **Blockers (report plainly, do not fake):** NSE futures backtest quota 25/25 (resets ~mid-month), MCX requires a purchased add-on (`429 — "MCX Plan not available")`. Rolling-window simulation on EXISTING AlgoTest CSVs is the workaround when quota is exhausted — never present it as a fresh AlgoTest backtest.

## Local-engine backtest methodology (clean walk-forward, verified 2026-11-11)
- **Walk-forward split:** search on an EARLIER window (train), pick the best config, then test it UNCHANGED on a LATER window (test). Report BOTH windows. Never report the train numbers as the strategy's result.
- **Costs to model (crypto perps):** fee 0.10%/side + slippage 0.05%/side + funding 0.01% per 8h = **0.03%/day** on a held position. A "clean" backtest applies all three; funding is material on positional holds and is frequently omitted (optimistic).
- **Overfit signal (the trap):** the best-train config by FTMO pass-rate often collapses out-of-sample. Example: Lb=10/lo/no-MA/no-VT was +57.1% train / FTMO 63.3%, but on test -10.9% / FTMO **3.7%** (DD -70%). A config that wins only the train window is overfit. Prefer the config that HOLDS out-of-sample — ETH-D4 (Lb=40/ls/MA50/vt) ranked #5 of 336 on test with FTMO 88.2% / FN2 77.0% WITH costs.
- **Simple short-lookback momentum (Lb=10, no MA, no vol-target) is overfit; Lb=40 + MA50 + vol-target is robust.** When a fast config beats everything in-sample but fails out-of-sample, the lesson is not "momentum doesn't work" — it's that a bare short-lookback momentum has no regime filter; the MA/vol-target version is the stable one.
- **Active-days definitions differ:** `pos!=0` (position held) vs `pnl!=0` (any P&L, incl. fee on a flat day). Report which one you mean — they differ (ETH-D4 2023: 164 vs 179; 2025: 83 vs 97). A user quoting 97 vs 179 is likely reading `pnl!=0`; don't "fix" it.
- **Why a daily momentum strategy trades less in some years:** the trailing exit sets `blocked` for the exited direction until momentum flips. With a long lookback (Lb=40) flips are rare in trending years → fewer active days. The MA filter blocks only ~20-50 days/yr and is NOT the main cause. Diagnostic that settles it: count MA-blocked vs trail-exit vs active per year (engine-level, not hand-sim).
- **Days-to-pass (prop sim, at k sizing): report median/p25/p75/p90, not just pass-rate.** ETH-D4 @k=1.272: FTMO median 91d (p25 48, p90 199), FN2 median 122d (p90 225). Capital size does NOT change the % distribution — k scales proportionally, so $5k/$10k/$25k all give the same days-to-pass.

## USER RULE: AlgoTest engine is the SOURCE OF TRUTH for any saved strategy
- **Hard rule (user correction, emphatic):** "Algo test me use ho, wahi se back test karna tha, khudke engine se nahi — sab statugy me yahi kiya." A strategy saved to AlgoTest MUST be validated by running AlgoTest's OWN backtest engine on the saved strategy ID. Reported profit/win%/PF/DD must come from the AlgoTest backtest CSV/metrics, NEVER from a local/synthetic engine.
- **Local engine results are only a research filter.** Use them to shortlist candidates, but the numbers you present as "the strategy's result" for a saved strategy are the AlgoTest backtest numbers. If you cannot run AlgoTest backtest (quota/schema), say so plainly and do NOT substitute local-engine numbers as if they were AlgoTest's.
- **Before reporting a saved strategy, ALWAYS re-run its backtest through AlgoTest and compare** — if AlgoTest result differs from local-engine, report BOTH and flag the mismatch. Do not silently present the better-looking one.
- **Canonical mismatch magnitude (ETH-D4, 2026-11-11):** local engine vs REAL AlgoTest — Net +$6,024 (+60.2%) vs **+$1,057 (+10.6%)**; MaxDD −9.5% vs **−36.6%**; worst day −3.25% vs **−9.8%** (breaches 5% daily-loss limit); win/PF 47.3/1.59 vs 61.9/1.14; FTMO/FN2 pass **88.2%/77.0% vs 42.3%/39.2%**. A local-engine "88% PASS" can be a **42% FAIL** on the real platform — never quote the local number for a saved strategy.
- **Saved positional FUT_P backtests are Friday-only by construction** (`Positional.Weekly` → `Entry-Weekday` Fridays, ~97 trades, ~52/yr) — the trade-count discrepancy a user will notice vs a daily engine is EXPECTED, not a bug. Explain it, don't "fix" it.

## AlgoTest builder CANNOT express these (FUT_P, verified 2026-11-11)
- **No MA/SMA indicator exists** in the builder. An MA-filter strategy (e.g. MA50/MA200) is NOT expressible — do not claim it is (earlier report section claiming "momentum + MA filter expressible" was WRONG; builder has no MA node).
- **Momentum is same-day %/pts only** — no multi-day lookback. A `Lb=40` trend-entry strategy cannot be built.
- **Vol-target position sizing is not a native block** — must use fixed lots instead (accept higher DD in high-vol periods) or a custom rule.
- **Long+short mode:** builder saves only the long leg; no explicit long-short toggle for FUT_P.
- **Continuous trail is stepped in AlgoTest** — the SL sits 5–10% below peak; a continuous 5% trail is not reproducible.
- Consequence: a saved FUT_P strategy may be only a **"risk shell"** (ticker, expiry, leg type, lot, stepped SL, stop time) — it will NOT reproduce local-engine stats for strategies relying on the above features. Document the mismatch in the save result file and TELL THE USER, do not imply the saved strategy reproduces the researched stats.

## FUT_P save payload (captured from live builder UI, verified 2026-11-11)
- Intercept the real POST (abort it) to capture the exact payload — `eth_d4_recon_v7.js` pattern. Do NOT guess a schema for FUT_P; it differs from the options payload.
- Positional: `attributes.positional: "Positional.Weekly"` + `PositionalIndicator` nodes in Entry/Exit. `StrategyType` STAYS `IntradaySameDay` even for positional weekly.
- Leg: `LegType.FUT_P`, `EntryType/StrikeParameter: None`, `ExpiryKind: Monthly`.
- **Delta-based SL/Trail invalid for FUT_P legs** → use `Percentage` types.
- Trail = stepped `{InstrumentMove, StopLossMove}` and REQUIRES the leg SL to be set first.
- Save result: `POST /strategy` 200 + strategy ID; verify via `GET /strategy/<id>` deep-check + `/strategies` list. Config match = 14/14 checks (ticker, positional, leg, lot, trail, SL backstop).

## AlgoTest strategy builder tool — how it works (verified 2026-11-09)
- Input: instrument + timing + legs (strike criteria) + SL/target/momentum/re-entry → Engine: historical 1-min OHLC day-by-day simulation (strike selection, per-candle SL/target check, re-entry/trail/lazy, exit) → Output: P&L, win%, PF/RR, Max DD, equity curve, year-wise, CSV trade log (+ Payoff/Greeks/MC) → Deploy: save → forward test (paper) → live via broker.
- 8-step flow: 1 Instrument 2 Timing 3 Legs 4 Risk params 5 Save 6 Backtest Engine 7 Output 8 Deploy.
- User's "Pacific options" was a mis-hearing — user means regular put/call options (CE/PE), NOT a Pacific Exchange product. When user says "option" in AlgoTest context, they mean the CE/PE contract, not a navigation menu or a specific product family.

## Playlist backtest (per-video, NO mixing)
- `playlist_backtests.js` (proot, node) — one SEPARATE AlgoTest backtest per video, probe (3-day) + full modes. Output `playlist_backtest_results.json`.
- User rule (hard): 3+ videos = 3 alag backtests + head-to-head table, NEVER 1 combined strategy.
- Indicator-entry videos (EMA/Supertrend crossover) are NOT expressible in the time-based engine → report as `notRun`, do NOT approximate.
- Probe mode validates payloads cheaply first; only 2 of 5 probe runs completed (v02, v04) — full run re-submits.

## Reading results + risk-adjusted ranking

**Read the `metrics` object, NOT `summary`.** A completed record has BOTH:
- `metrics` = normalized keys: `trades`, `overallProfitUsd`, `overallProfitInr`, `winRate`, `lossRate`, `profitFactor`, `maxDrawdownUsd`, `maxDrawdownInr`, `rewardRisk`, `expectancy`, `avgWinUsd`, `avgLossUsd`, `maxWinStreak`, `maxLossStreak`.
- `summary` = AlgoTest raw, CAPITALIZED keys (`OverallProfit`, `MaximumDrawdown`, `NumberOfTrades`, `Expectancy`).
Reading `profit`/`dd`/`win_rate`/`pf` (nonexistent keys) returns `$0.00`/`None` silently — parse `metrics.*` first.

**Rank by profit/maxDD ratio, not raw profit** (user convention: "DD ke samne aache profit wali"). `ratio = overallProfitUsd / abs(maxDrawdownUsd)`. This is the fair cross-instrument comparison (different tickers, different lot sizes) — raw profit alone misleads (v09 had the highest profit $3,473 but DD -$1,233; v02 won at ratio 23.4).

**User's comparison order (hard preference): same-lot FIRST, same-capital only when asked.** When comparing two strategies across instruments, the user's default is "same lot kar do" — scale both to the same lot count and report per-lot profit/DD/ratio BEFORE any capital-based scaling. Do NOT lead with same-capital. The user escalates to same-capital explicitly ("same capital se"), and only after the lot view.

**Scaling a saved strategy to N lots is linear** — P/L and DD scale ×(N/baseLot), ratio (profit/DD) unchanged, PF and win% unchanged. Report ratio only when lots are scaled by the same factor on both sides.

**Contract sizes (Delta Exchange, from live tickers + Big's margin analysis):** ETH 1 lot = 0.01 ETH; BTC 1 lot = 0.001 BTC. Safe capital per unit (margin + DD buffer, incl. ~15% vol-shock): ETH 1 lot ≈ $4.6; BTC 100 lots ≈ $799. Use these to convert lots↔capital and to sanity-check that a "10 lots each" claim is achievable within the user's capital.

**Save numbers from the result file, never from your own brief.** Verify actual `overallProfitUsd`/`maxDrawdownUsd` in the file before reporting — a paraphrased brief can be wrong (brief said $980; file had $2,980.25).

**Per-strategy deliverable (user preference): logic + equity curve + DD curve for EVERY strategy, not just one.** When the user asks for results, provide (a) the entry/exit/sizing logic in plain bullets, (b) a cumulative equity curve chart, and (c) a drawdown curve — for EACH strategy, side by side or as separate panels. Do not report numbers only, and do not chart just the single "best" one. `matplotlib` lives in Termux python (`/data/data/com.termux/files/usr/bin/python3`), NOT proot `/usr/bin/python3` — run chart scripts with Termux python.

## Save (any instrument / any re-entry type)
Save works for ANY ticker and ANY of the dropdown values, not just ETH-ATM-Immediate. Verified save: `DELTA_BTCUSD`, Sell CE+PE `StrikeType.OTM5`, `ExpiryType.Today`, SL 200%, `ReentryType.AtCost` ×1, Lot 100 → `6af03b7ca326307a85995ff6`. Valid re-entry enums: `ReentryType.Immediate`, `ReentryType.AtCost` (both take `{ReentryCount: N}`). SL `Percentage` 200 is valid (not capped at 100).

## Plan file
- `~/algotest_grid_plan.md` (video steps + grid params + results).
- Grid params to sweep: Strike, Target Profit, Stop Loss, Re-entry, Simple Momentum, Expiry.

## Pitfalls
- Chromium crashes in proot → always Firefox+Playwright.
- Credentials via env, never hardcoded (user trading rule).
- `IntradaySameDay` not BTST for 22:00→07:00.
- Video step 9 "Create an..." button — video wahi rukta hai (create nahi hua).
