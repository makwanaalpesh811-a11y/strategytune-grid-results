---
name: termux-almari-maintenance
description: "Use when user says almari sahi karo. Organize home."
version: 1.0.0
author: SenseNova
metadata:
  hermes:
    category: devops
---

# Termux Almari + Home Maintenance

User ka maintenance flow: "almari sahi karo", "sab fix karo", "cleanup".

## Core principle

**Pehle backup, phir delete.** User rule (2026-11-04): jo delete karne wale ho wo pehle GitHub private repo me archive karo, phir delete. Originals jahan hai wahi rehne do. Failed/na-aayi kaam bhi repo me daal ke delete.

## Steps (verified 2026-11-04)

1. **Survey** — `du -sh * | sort -rh | head -30` + `find . -maxdepth 1 -type f -size +5M`.
2. **Delete candidates list** — redundant/temp/test (video variants, test frames, tmp audio, test dirs, old zips).
3. **Archive repo create** — `gh repo create <user>/archive-<date> --private --description "..."`.
4. **Copy candidates to archive dir** — `cp` (sirf copy, originals delete nahi abhi).
5. **GitHub 100MB limit** — >100MB file ko `split -b 50M file file_part_` karke commit; `git filter-branch` se history se >100MB file remove karo (pehla commit bhi check karo — `git push` reject hota hai agar history me hai).
6. **Push** — `git push -u origin master` (branch `master` default, `main` nahi). Network slow pe 390M me 15-25 min lag sakta hai — background `notify=true`.
7. **Verify remote** — `git ls-remote --heads origin` + `git ls-tree -r --name-only origin/master | wc -l`.
8. **Delete originals** — backup push complete hone ke baad hi delete (no data loss).
9. **Almari cleanup** — 06_TRANSIENT empty/tiny dirs + 03_DOWNLOADS test TTS dupes (hindi_*.mp3, audio_en.*, *.info.json) delete; devotional videos + std12 books + trading data KEEP.
10. **Verify** — critical files present (`.yt_token.json`, `delta_dash_live.py`, `meesho_bot`, `signal_bot*.py`, `phone.py`, `brain/`, `.delta-exchange-mcp/config.env`), no active processes, sizes.
11. **Archive local tmp delete** — `rm -rf ~/.archive_tmp`.

## GitHub limits

- **100MB/file** — bade files ko `split -b 50M`.
- **Embedded git repos** — `voice_clone_repos/voice-clone` warning; `git rm --cached` ya submodule nahi — bas commit chal jata hai.
- **Private repo** — sensitive (tokens) ke liye private hi; `00_SECRETS/all_tokens_*.tar.gz` private repo me, public me NAHI.

## What to KEEP (never delete)

- `01_STRATEGY/` (trading code), `02_DATA/` (delta candles), `03_LEARNING/` (teacher lessons), `05_MEDIA/` (std12 books), `04_CONFIG/` (signal_bot_env, cleanup_backup memory).
- `03_DOWNLOADS` devotional videos (user ke).
- `obscura/`, `vibe-trading/`, `paper_trade/`, `voicestudio/`, `bt_cache/`, `jadx/`, `brain/`.
- `~/.yt_token.json`, `delta_dash_live.py`, `meesho_bot/`, `signal_bot*.py`, `phone.py`.

## Pitfalls

- **jadx.zip 100.11MB** — GitHub 100MB limit cross; `split` + `filter-branch` zaroori.
- **Branch `master`** — Termux git default master; `git push -u origin main` fail hoga.
- **/sdcard files file manager me empty dikh sakte hain** — `chmod -R g+rX,o+rX` fix.
- **Network slow** — 390M push me 15-25 min; background + wait.
