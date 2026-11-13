---
name: apk-reverse-engineering
description: Use when reverse-engineering an Android APK on Termux.
---

# APK Reverse Engineering on Termux (aarch64)

Decompile and inspect an Android APK offline on Termux. Covers tool install, download-host selection, and the APK transfer rule.

## Tool install (verified on Termux aarch64)

- `pkg install -y openjdk-17` — Java is required by both tools.
- **apktool is NOT on pip** (`pip install apktool` finds no version). Download the jar from the iBotPeaches GitHub release: `curl -sL -o apktool.jar https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar`. Run via `java -jar apktool.jar --version` (v2.9.3 verified).
- **jadx** from the skylot/jadx GitHub release: `curl -sL -o jadx.zip <.../jadx-1.5.0.zip` then `unzip -q jadx.zip -d jadx`. Run via `~/jadx/bin/jadx` (v1.5.0 verified).
- Verify both before use: `java -jar apktool.jar --version` and `ls jadx/bin/jadx`.

## Getting the APK onto Termux

- **APKs are 17–96 MB — they NEVER fit the Telegram document path (>20 MB refused).** Do not ask the user to send an APK via Telegram; it will fail with "document too large".
- Working on-device route: Play Store install → `adb pull $(adb shell pm path <pkg> | cut -d: -f2) <dest>`. Requires ADB setup (see phone-adb-automation).
- If a download URL is needed instead, see host selection below.

## Download-host selection (don't guess mirrors)

Probe reachability FIRST with a TCP connect test (cheap, no HTTP, no rate-limit risk), then download only from hosts that answered:

```python
import socket
for h in ('d.apkpure.net', 'uptodown.com', 'apkfab.com', 'apkdone.com', 'www.apkmirror.com'):
    try:
        s = socket.create_connection((socket.gethostbyname(h), 443), timeout=6)
        print(h, 'OK'); s.close()
    except Exception as e:
        print(h, 'FAIL:', str(e)[:40])
```

On this device `d.apkpure.net`/`download.apkpure.net`/`apkcombo.app` resolve in DNS but the TCP 443 connect times out (network-level block) — curl then returns HTTP 000 forever and that is NOT retryable. `uptodown`, `apkfab`, `apkdone`, `apkmirror`, GitHub, F-Droid connect fine. **DNS resolve + no TCP connect = blocked, not down.**

## Workflow

1. Install Java + apktool + jadx (above).
2. Get the APK (Play Store → adb pull, or a probed-reachable mirror).
3. `apktool d app.apk -o out/` for resources/smali; `jadx -d out/ app.apk` for Java source.
4. Grep the decompiled output for the RNG / bot-decision / shuffle logic: `grep -riE "random|shuffle|rng|deck|seed" out/`. Offline games are client-side (predictable); online games move this server-side (see pitfalls).

## Pitfalls

- **Offline vs online RNG.** Offline APK: card distribution is client-side, so the RNG is in the APK and predictable after RE. Online real-money: distribution is server-side + RNG-certified + anti-cheat — RE cannot change win probability, and attempting to is cheating (account ban + money loss).
- **Do not present decompile attempts as validated until the APK is actually in hand and decompiled.** This skill's install/probe/transfer steps are verified; the decompile output itself depends on the specific APK.
- **User context (this user):** wants an offline game RE'd to understand RNG/bot patterns, then a helper (not a bot) that suggests moves while they play. Real-money online rummy is banned in India (2025 Act) — do not recommend it.
