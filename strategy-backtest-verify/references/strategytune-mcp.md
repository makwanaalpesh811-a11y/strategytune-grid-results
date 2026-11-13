# StrategyTune MCP (via Big Pickle / opencode) — depth reference

Setup, script format, hard limits, and the failure/retry patterns that cost time. Load this when working on StrategyTune backtests; the always-on workflow gates live in SKILL.md.

## Setup (one-time, done 2026-11-13)

```bash
# in proot ubuntu
opencode mcp add strategytune --url https://strategytune.com/mcp
opencode mcp auth strategytune   # OAuth URL opens in browser -> Allow -> token saved
```

- **Config `/root/.config/opencode/opencode.jsonc` needs `mcp.strategytune.enabled: true`** or the tools DO NOT load in `opencode run` (symptom: the model answers `NO_TOOLS`).
- Verify: `opencode mcp list` shows `✓ strategytune connected`; `opencode mcp debug strategytune` shows authenticated + refresh token.
- OAuth token auto-refreshes; `opencode mcp auth <name>` to re-auth if it expires.

## Tool naming & count

- MCP tools appear as `strategytune_*` (e.g. `strategytune_run_backtest`, `strategytune_save_script`, `strategytune_get_run_result`, `strategytune_get_knowledge`, `strategytune_find_instruments`, `strategytune_duplicate_script`).
- ~37 tools total. Read-only vs write/delete tools — permission groups configured on the connector page.

## Strategy script format (TypeScript, NOT plain TS)

- `export default class implements Script { onUpdate(ctx: Context) { ... } }` — plus optional `onInit` / `onFinish`.
- **Gate per-bar logic on `ctx.isNewBar`** — `onUpdate` fires many times inside a forming bar; without the gate you open N trades per bar.
- `ctx.bars.close(n)`, `open/high/low/time(n)`, `count`; `ctx.account.position`, `closedPnl`, `startingBalance`, `equity`, `lastClosedTrade`; `ctx.inputs.<key>` (typed).
- Orders: `ctx.orders.marketOrder({ side: "Long"|"Short", size, slDistance, tpDistance })` or `{ risk: { percent } }`, plus `slPrice`/`tpPrice`. Pending: `limitOrder`/`stopOrder`.
- Custom metrics: `ctx.stats.custom.set(name, value)` — read them back from `get_run_result`.
- `save_script` needs BOTH `metadata_json` (name, inputs, historyBars, strategy:{}) AND `code`. Compile is free; a bad script errors with a `failed`/compiled message, not a crash.
- `duplicate_script` is the cheap way to clone a working script for a param variation (compile is free).

## Backtest run

- `strategytune_run_backtest { interval, script_id, start, end, starting_balance, ticker, data_provider, wait_seconds }`.
- `data_provider` = `icmarkets` / `pepperstone`. **Use full ticker names** — short aliases FAIL (`NAS100`, `XAUUSD`, `GER40`, `US500` return 0 results). Real names: `S&P 500`, `Nasdaq 100`, `DAX`, `Dow Jones 30`, `Gold`, `BTCUSD`, `ETHUSD`.
- Tickers are `TICKER` not symbol — search `strategytune_find_instruments { q }` first if unsure.
- Poll `strategytune_get_run_status` / `strategytune_get_run_result`; trades via `strategytune_get_session_trades { record_id, limit }`.

## Hard limits (platform, Free plan)

- **1,000 order operations per run cap** — high-frequency strategies hit this and stop early (partial result, NOT a failure). Use a shorter window or fewer trades/day for dense sweeps.
- **1 instrument + 1 timeframe per run** — no multi-symbol / multi-TF. Multi-TF strategies need a single-TF proxy (loses the staircase edge — say so honestly).
- **No commission / slippage model** — only recorded bid/ask. Net off mentally for low-edge strategies.
- Free = 10 min compute/day, 2 parallel runs, 1-year range cap. Pro = 24h / 5 runs / unlimited. Failed runs count; cancelled don't; queue time & compiles are free.
- Compute meter resets 00:00 UTC. A 4h 2-month run costs ~2-3s; a 15m run costs more and may hit the order cap.

## MCP timeout retry pattern (error -32001)

`strategytune_run_backtest` (and occasionally `get_knowledge`/`get_script`) may return `MCP error -32001: Request timed out` at the client layer **while the run still exists server-side**. Do NOT treat it as failure:

1. Retry the SAME cell — identical params dedup to the same run, **no extra compute quota**.
2. Use `wait_seconds: 15-20` (lower than default) to shrink the client wait and reduce timeouts.
3. Batch 3-4 combos per `opencode run` call; verify each returned a run id or dedup, then continue. Never stop the whole sweep on a single timeout.

## Passing long task text to Big Pickle (Termux + proot)

Two traps both cost time this session:
- **Termux `/tmp` is not writable** (permission denied). Write the task file under `$HOME` (Termux home), e.g. `~/task.txt`.
- **Inside proot, `~/task.txt` is `/root/task.txt` and does NOT see the Termux file.** Reference it by the real path: `/data/data/com.termux/files/home/task.txt`.
- **Never embed multi-line task text in `bash -c "..."`** — quoting breaks (`unexpected EOF while looking for matching \"`). Use `opencode run --model opencode/big-pickle "$(cat /data/data/com.termux/files/home/task.txt)"`.

## Cross-instrument dollar-denominated SL/TP scaling

Dollar-denominated `slUsd`/`tpUsd` are instrument-specific. `SL 500 / TP 50` on Gold ($2-4k/oz) means a different % risk on BTCUSD ($60-100k) — it can give 0 trades or all-stop. For a new instrument, first compute the average daily range via a `run_code` probe (or scale SL/TP as a % of daily range to match the reference instrument's risk), THEN run the grid.

## Grid result reuse

`get_run_status`/`get_run_result` on an already-computed run is cheap. When a cell's run timed out client-side but exists, re-request the SAME params to dedup and pull the result — do not re-run blindly.

## Direct Python MCP client (fast path for dense sweeps)

Big Pickle's `opencode run` round-trip costs ~30s+ per cell and times out a 42-cell dense grid (only ~8 cells survive a 290s worker, and `-32001` timeouts compound). For parameter sweeps, call the MCP directly from Python instead of routing through `opencode run`. The working client is `$HOME/st_mcp.py` (Termux path, but launched inside proot ubuntu so it can reach the proot filesystem).

```python
# st_mcp.py — minimal streamable-HTTP MCP client
# mcp_call(name, params, token, timeout=40):
#   POST {base_url}/mcp  body={"jsonrpc":"2.0","id":1,"method":"tools/call",
#                           "params":{"name":name,"arguments":params}}
#   headers: Authorization: Bearer <token>, Content-Type: application/json
#   Accept: application/json,text/event-stream   (SSE responses supported)
# get_valid_token():  checks expiry, refreshes via /oauth/token if needed
# load_token():  reads accessToken/refreshToken/expiresAt from auth cache
```

- **Call format (CRITICAL):** streamable HTTP uses JSON-RPC method `tools/call` with `params.name` + `params.arguments`. Calling by bare method name (`{"method":"run_backtest"}`) returns `Method not found` and silently zeroes every cell. Tool names are the `strategytune_*` names from `opencode mcp list` (`strategytune_run_backtest`, etc.) — NOT the bare `run_backtest`.
- **Token refresh:** the access token expires (~1h; read `expiresAt` or the JWT `exp` claim). POST `/oauth/token` with `grant_type=refresh_token&refresh_token=...&client_id=...` to mint a new access token. Wrap every call in `get_valid_token()` so the client survives a mid-sweep expiry — without it the grid dies at the first expired token.
- **Result parsing:** `get_run_result` returns stats inside `result.content[0].text` as a JSON **string** — NOT in `result.stats`. Parse that string; nested structure is `stats.stats` (basic metrics) and `stats.customStats` (your `ctx.stats.custom` values, e.g. pass rates). Naive `result.get("stats")` extraction yields all-zero metrics for every cell — looks like "every combo fails" but is a parse bug.
- **Auth file:** proot opencode saves tokens at `/root/.local/share/opencode/mcp-auth.json`; copy to a Termux-visible path (`.hermes/cache/st_mcp_auth.json`) so a Termux-launched client can read it.
- **Keep ONE grid CSV path for the whole sweep.** The proot Big Pickle recovery wrote `/root/SLPT_dense_grid.csv` while the direct client wrote `Hermes_Almari/02_DATA/SLPT_dense_grid.csv` — two files, needed a manual merge before ranking. Decide one path and pass it to every cell-writer; never let two writers fork the grid.
- **In-sample dense-grid winner is still in-sample.** A finer grid only refines the plateau on ONE window. This session SL350/TP37.5 hit 86.8% 15-day pass on the 2-month Gold window — HIGHER than the SL500/TP50's 81.6% that later failed OOS at 0% (0/92, PF 0.80). A higher in-sample number on the same window is NOT stronger evidence; the OOS gate in SKILL.md still applies before any "best" claim. Report the winner as "best in-sample", never "the strategy".

### Dense-grid cell run cost

A 4h 2-month run ≈ 2-3s of COMPUTE, but ~30s+ of WALL-CLOCK per cell (run launch latency + status polling + result fetch + occasional retry). A 42-cell grid therefore needs **4-5 separate background workers** (~10-13 cells each at `timeout 570`), not one. Compute quota is not the constraint — worker wall-time is. Split the grid and rely on the done-set resume pattern below.

Use `wait_seconds: 15-20` and a short per-cell `mcp_call` timeout so a hung cell fails fast and the loop continues to the next cell. Append each cell row to the CSV immediately after its result (crash-safe); never buffer the whole sweep in memory and write at the end.

### Resume pattern for multi-worker sweeps (REQUIRED for >10 cells)

Each worker reads the existing CSV at start and builds a `done` set of `(SL, TP)` pairs; the loop skips any cell already in it. This makes every subsequent worker cheap (it resumes at the first missing cell, not from the top) and means a killed/timed-out worker loses nothing. Without this, re-running the grid redoes all done cells and doubles the wall-clock.

```python
done = set()
with open(CSV) as f:
    next(f)
    for line in f:
        parts = line.strip().split(",")
        if len(parts) >= 2:
            done.add((parts[0], parts[1]))
```

### SSL handshake timeout (transient — retry, never treat as failure)

A cell may fail with `<urlopen error _ssl.c:1063: The handshake operation timed out>`. This is a transient network/SSL blip, NOT a bad param — the loop should catch it, log `ERR`, and move on (the cell stays missing from the CSV). The next resume worker picks it up and it succeeds on retry. Do not stop the sweep or conclude the combo is broken. This session: SL500/TP50, SL550/TP37.5, SL600/TP25 all failed once with this and succeeded on the resume worker.
