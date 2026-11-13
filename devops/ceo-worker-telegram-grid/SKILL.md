---
name: ceo-worker-telegram-grid
description: Use for multi-phone CEO+worker grid via Telegram.
---

# CEO + Worker Phone Grid (Telegram-based, No USB)

## Status: SAVED (idea only, not built)
Plan shared 2026-10-27. Implementation pending — user explicit GO ke baad.

## The Core Idea
- **CEO Phone** = main Hermes Agent + Telegram gateway + adb (control center)
- **Worker Phones** = each with Hermes Agent + Telegram gateway + their own bot
- **NO USB cable, NO OTG** — everything over Telegram (internet), unlimited range

## Why Telegram > USB
- Unlimited range (internet) vs cable 2m
- No OTG/powered-hub needed
- No per-phone "Allow USB debugging" dialog
- No cable power drain
- Each phone independent (parallel work)

## How Commands Reach a Worker
```
CEO Hermes → sendMessage API (bot<WORKER_TOKEN>, chat_id) → worker's Hermes polling → does work (adb/scripts) → replies via sendMessage
```
Need per-worker: `worker_bot_token` + `worker_chat_id` — **config file me, kabhi repo/GitHub pe nahi**.

## Option A: Direct bot (simplest)
Each worker phone has its OWN bot token (BotFather, free).

## Option B: Shared Telegram Group (most practical, RECOMMENDED)
Group "Team CEO + Workers": CEO bot + Worker1/2/3 bots + owner.
- CEO sends command → group; worker does work → replies group; owner sees everything.

## Important Constraints
1. Each worker needs its OWN bot token (one bot = one phone, polling conflict otherwise)
2. Local AI model on each phone NOT possible (Termux py3.14: no PyTorch/numpy wheels) — each runs Hermes via cloud API instead
3. Speed: ~1-2s per Telegram command — fine for automation, too slow for live trading
4. Screen ON + app visible needed for any adb/app automation
5. Login/OTP/CAPTCHA: user does it (never ask credentials)

## Suggested Roles (future)
- Worker 1 = Flipkart bot
- Worker 2 = Meesho automation
- Worker 3 = YouTube upload
- CEO = collect reports + decisions

## SECURITY (IMPORTANT)
- Bot tokens, chat IDs, API keys NEVER in repo/skill — only local config
- If any sensitive value was pushed, rotate the token immediately

## Related
- `phone-adb-automation` skill (single-phone ADB control)
- `telegram-gateway-setup` skill (gateway setup on each phone)
