---
name: voice-gateway-service
description: Use when user says voice wala gateway on/off karo.
version: 1.0.0
author: SenseNova (curator)
license: MIT
platforms: [android, linux, macos]
metadata:
  hermes:
    tags: [voice, gateway, server, api, termux, wakehermesclaw]
    category: productivity
    related_skills: [telegram-gateway-setup]
---

# Voice Gateway Service (Hermes Voice API)

Manage the on-device voice API server that the WakeHermesClaw app talks to: `127.0.0.1:8642`, key in `~/.hermes/voice_api_key`, model `hermes-agent`. This is a SEPARATE system from the Telegram gateway — turning one on/off does NOT affect the other.

## When to Use

- User says "voice wala gateway on karo" / "voice wala gate off karo" / "voice server band karo".
- Troubleshooting the WakeHermesClaw voice app not reaching Hermes.
- Any ask about the voice server's status.

Don't use for: the Telegram gateway (`hermes gateway run`) — that is a different service with its own env vars and flow (see `telegram-gateway-setup`).

## Turn OFF (the common case)

1. Check what is on port 8642 and what processes exist:

```bash
ss -tlnp 2>/dev/null | grep -E '8642' || echo "PORT 8642 NOTHING"
pgrep -af 'voice|8642|hermes.*api|api.*server|uvicorn|fastapi|gunicorn|flask' | grep -v snap || echo "NO VOICE PROC"
```

2. If nothing on the port and no process, it is ALREADY OFF — report that, do not hunt further.

3. If a process owns 8642, kill it:

```bash
pkill -f 'voice.*server|voice_api|uvicorn|gunicorn'
```

## Turn ON

1. Verify the key exists: `cat ~/.hermes/voice_api_key` (should be 49 chars, non-empty).
2. Verify the model name is right: `hermes-agent`.
3. Start the API server in the background on 8642 (command depends on the deployment — the runnable lives under the Hermes install or a wrapper in `~/`).
4. Hold the wake-lock FIRST: `termux-wake-lock` then `pgrep -af 'termux-wake-loc[k]'` (bracket trick — bare name self-matches the wrapper shell, see Pitfalls).
5. Health-check the loop: `curl -s http://127.0.0.1:8642/health` (or the configured health path) returns 200 and the WakeHermesClaw app reaches it.

## Pitfalls

- **Bare `pgrep -af termux-wake-lock` self-matches the wrapper shell and lies.** Same as the Telegram gateway skill: the terminal tool wraps commands in a snapshot script whose command line embeds your text verbatim, so a bare pattern returns a match (false HELD) even when the wake-lock is down. Always use the bracket trick: `pgrep -af 'termux-wake-loc[k]'`.
- **Port 8642 empty does NOT prove the app server is down** — the API server may be a foreground/reconnecting process, or the port binding may have failed. Cross-check `ps aux | grep -iE 'voice|uvicorn|api'` before declaring it off.
- **The voice server and the Telegram gateway are independent.** User may say "voice off karo" while the Telegram gateway stays on — do NOT touch `hermes gateway run` for a voice request, and vice versa. The two share the wake-lock (dropping it kills both), so when one dies unexpectedly check the wake-lock first.
- **Never guess the wake-lock state from `hermes gateway status`** — that only reports the Telegram gateway process, not the voice server.

## Verify

- OFF: no process on 8642 and `pgrep` returns nothing for the voice patterns.
- ON: curl health check returns 200 and the WakeHermesClaw app reaches it.
- User can issue a voice command and gets a Hermes response.

## Not This Skill

- The Telegram gateway (`hermes gateway run`) — different env vars, token, allowlist flow.
- Editing the WakeHermesClaw app config on the phone (that is the user's app, outside Hermes).
- The `voice_api_key` generation flow — covered by the voice setup work in the user profile.
