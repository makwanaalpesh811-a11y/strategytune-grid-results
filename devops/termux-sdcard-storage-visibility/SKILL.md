---
name: termux-sdcard-storage-visibility
version: 1.0.0
author: Alpesh Makwana
license: MIT
platforms: [android, termux]
description: "Use when Android File Manager can't see Termux SD files."
---

# Termux SD-Card Storage Visibility

When a user on Android reports that files Hermes created on the SD card are not visible in their file manager (or a folder looks empty), diagnose and fix ownership + permissions, then force a file-manager refresh.

## Symptom patterns

- "Almari folder looks empty" when Hermes just wrote files there.
- Some files show, others don't, in the same directory.
- Different file managers (Material Files, Solid Explorer, AIDA64, system manager) behave differently.
- Files exist when listed from Termux (`ls /sdcard/Hermes_Almari` works) but the GUI shows nothing.

## Root cause (Android 10+)

SD card on Android is a `fuse` mount with SELinux context `fuse:s0`. Termux runs as `u0_a483` (or similar `u0_aXXX`); files it writes take ownership `u0_aXXX:media_rw`. The file manager runs as a different `u0_aYYY` context. If permissions are `0640` (owner+group only), a different app in a different SELinux context sees the file as absent.

Files are written to `/sdcard/` from Termux fine (SD is group-writable), so the file exists on disk — visibility is a **mode + context** issue, not a permissions-to-write issue.

## Diagnostic flow

1. Confirm the files actually exist:
   ```bash
   ls -la /sdcard/Hermes_Almari/
   du -sh /sdcard/Hermes_Almari/
   ```
2. Inspect ownership + mode:
   ```bash
   stat /sdcard/Hermes_Almari/00_BLUEPRINT.md
   id   # confirm current Termux uid (u0_a483)
   ```
   If the file's `uid` differs from the file manager's uid AND mode is `0640` (group only), that's the bug.
3. Check SELinux context — should show `u:object_r:fuse:s0` (expected on Android SD).

## Fix (apply in this order)

1. **Chmod — group+other readable:**
   ```bash
   chmod -R g+rX,o+rX /sdcard/Hermes_Almari/
   ```
   `X` (capital) = grant execute on directories only, not files. This is the crucial fix; most Termux file managers only fail because of the missing group bit.
2. **Touch top-level folder mtimes to force refresh:**
   ```bash
   touch /sdcard/Hermes_Almari/00_BLUEPRINT.md /sdcard/Hermes_Almari/00_EXECUTION_PLAN.md
   for d in /sdcard/Hermes_Almari/*/; do touch "$d"; done
   ```
3. **If still invisible, clear file-manager cache** — user opens Settings → Apps → File Manager → Clear Cache. This is user-side, can't be automated.

## Pitfalls

- **Don't `chown -R u0_a483:media_rw` on files you don't own.** SD root (`/sdcard/`) is owned by `media_rw:media_rw`; files under it typically take ownership `u0_aYYY:media_rw` where `u0_aYYY` is whichever app last touched them. `chown` from Termux usually succeeds on files it created but can fail with EPERM on files owned by other apps — skip those. The chmod step works regardless of ownership because SD is group-writable.
- **`termux-setup-storage` wipes the `~/storage` symlink farm.** It refuses to run if dangling symlinks exist and aborts. Don't run it to fix visibility — chmod is the correct fix. Run it only to (re)grant Termux SD access after a boot where access was lost.
- **Don't `chmod -R 777`.** The SD mount is a fuse filesystem with restrictive SELinux policy; 777 is over-permissive and can trigger Android file-scanner warnings. `g+rX,o+rX` (or numeric `644` files / `755` dirs) is sufficient and is what Android expects.
- **The fix must be reapplied after any bulk copy from another app.** When `cp` from a file manager writes into Almari, the new files inherit the file manager's `u0_aYYY:media_rw` ownership and can land with `0640` mode — same bug, new files. Any workflow that pulls files from the GUI into Almari must end with the chmod command above.
- **`~/Hermes_Almari` symlink must resolve.** After moving the master copy to SD (`/sdcard/Hermes_Almari/`), keep a `~/Hermes_Almari` symlink so `~/Hermes_Almari/...` paths continue to work. If the symlink is broken, all relative-path scripts silently fail.
- **Emoji-named folders (`Hermes_Alarm_Khali_Nahi`) do NOT bypass the visibility bug** — same fuse mount, same ownership rules. They exist only for user discoverability, not for permissions.
- **`/tmp/` doesn't exist on Termux.** Redirect curl/HTTP output to `$HOME/tmp_xxx/` instead.

## Emergency visibility folder pattern

For critical files the user must see regardless of file-manager behavior, also place a copy at the SD root with a distinctive name (emoji is fine for user discoverability):

```bash
mkdir -p /sdcard/Hermes_Alarm_Khali_Nahi/
cp /sdcard/Hermes_Almari/02_DATA/important.csv /sdcard/Hermes_Alarm_Khali_Nahi/
chmod g+rX,o+rX /sdcard/Hermes_Alarm_Khali_Nahi/
```

The SD root is scanned more aggressively by Android's storage scanner than nested subdirectories, so this folder appears in the file manager even when the main Almari tree is missing.

## Verification

After the fix, confirm from Termux:
```bash
stat -c "%a %n" /sdcard/Hermes_Almari/00_BLUEPRINT.md /sdcard/Hermes_Almari/01_STRATEGY /sdcard/Hermes_Almari/02_DATA
# Expect: 664 (files), 775 (dirs)
```

If a file manager still shows the folder as empty after chmod, ask the user to clear the file manager's cache (Settings → Apps → [Manager] → Clear Cache) — that's a UI-side cache, not a filesystem issue.
