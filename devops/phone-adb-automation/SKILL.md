---
name: phone-adb-automation
description: Use when user wants phone app automation via phone.py ADB.
---

# phone.py ADB Automation (Phone ko PC jaisa control)

## Status: DEFERRED
User said on 2026-10-27: "Ye save kar lo bad me kare ge aage Jake abhi kam nahi hai" — setup NOT done yet. Resume ONLY when user explicitly says to do it.

## What it is
- `~/phone.py` — single file: setup wizard + HTTP API server + client CLI. Stdlib + adb only.
- Controls phone like a PC: cursor, keyboard, screen reading (UIAutomator dump), screenshot.
- No root needed. Uses **Wireless debugging ADB** (same phone, localhost connect).

## INSTALLED (done)
- `pkg install -y android-tools`
- **CRITICAL FIX:** adb gave `CANNOT LINK EXECUTABLE ... _ZNSt6__ndk113__hash_memoryEPKvm` → fixed by `pkg install -y libc++` (upgraded 29→30). Without libc++ 30, adb won't run.
- Verified: `adb version` → 37.0.0p1-android-tools, `adb start-server` OK, daemon running.
- `~/phone.py` syntax OK, chmod +x.

## SETUP STEPS (when user says GO)
1. Phone: Settings → About → Build number ×7 tap (unlock Developer options)
2. Settings → Developer options → **Wireless debugging ON**
3. "Pair device with pairing code" → note **pairing port** + **6-digit code**
4. Ask user for: pairing port (number) + pairing code
5. Run `python3 ~/phone.py setup` (wizard: pair → connect → saves ~/.phone_api.json)
6. Test: `python3 ~/phone.py status` → should show serial + screen dims
7. First live test: Meesho app (user picks)

## Key commands
```
python3 ~/phone.py ui [text]        # screen elements (text,id,clickable,x,y) — BEST
python3 ~/phone.py clicktext "Add Product"  # tap by text
python3 ~/phone.py waittext "Submit" [sec]
python3 ~/phone.py shot [file]      # screenshot PNG
python3 ~/phone.py current          # current app
python3 ~/phone.py open com.flipkart.android
python3 ~/phone.py type "text" [--clear]
python3 ~/phone.py key ENTER|BACK|HOME|TAB|DEL
python3 ~/phone.py scroll down|up|left|right [0.1-0.9]
python3 ~/phone.py drag X1 Y1 X2 Y2 [ms]
python3 ~/phone.py move DX DY | set X Y | click X Y
python3 ~/phone.py serve --bg | stop | status
```
Config: `~/.phone_api.json` (token, port 8765, target). Server auto-starts on client use.

## Scope (what's possible)
- Meesho: app open → scroll products → read → link copy (Cloudflare bypass! UI-based not HTTP)
- Flipkart: same
- Insta: comment reply/DM — SLOW, rate-limit, block risk. Meta Graph API safer for bulk.
- YouTube: upload via app, comment reply
- Telegram: post to group
- Universal: `open` + `clicktext` + `type`

## Limitations (truth)
1. Screen ON + app visible needed (no background)
2. Login/OTP/CAPTCHA — user does it (never ask credentials)
3. Hindi/emoji typing → needs ADBKeyBoard app installed+active (else error)
4. Insta bulk reply = block risk
5. Can't read video/canvas content — only UI elements

## Meesho relevance
Prior Termux:API + browser automation = DEAD ENDS (no tap/screenshot ever existed; agent-browser no android build; Playwright no py3.14 wheels). **phone.py ADB is the ONLY viable on-device automation path.**
