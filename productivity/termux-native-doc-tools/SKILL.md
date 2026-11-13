---
name: termux-native-doc-tools
description: "Termux PDF/OCR/image via pkg tools when pip times out."
version: 1.0.0
author: SenseNova (curator)
license: MIT
platforms: [android]
metadata:
  hermes:
    tags: [termux, android, ocr, pdf, poppler, tesseract, pkg-install]
    category: productivity
    related_skills: [pdf]
---

# Termux Native Document Tools

Python `pip install pymupdf / pdfplumber / pdfminer / marker-pdf` frequently times out on Termux (large wheels, no GPU, flaky network). The reliable path is Termux's `pkg` — native packages, fast install, no wheels. Reach for this skill whenever a Python PDF/OCR/image tool install hangs or fails on this user's Android Termux environment.

## When to Use

- On Android Termux and `pip install <pdf/ocr/image lib>` is slow, hanging, or OOMing.
- Handling scanned/image-only PDFs that `read_file` or `pypdf` return as "binary / empty text".
- Rasterizing PDF pages to PNG for `vision_analyze` or OCR.
- Image manipulation on-device without heavy Python deps.

The `pdf` skill (bundled) documents the desktop Python path. This skill covers the **Termux-native fallback** — when the Python path is not viable.

## Setup (once, idempotent)

```bash
pkg update -y >/dev/null 2>&1
pkg install -y tesseract poppler imagemagick
```

Verifies presence without `which` (unavailable on Termux):

```bash
for b in pdftoppm pdftotext pdfinfo tesseract convert; do
  [ -x "/data/data/com.termux/files/usr/bin/$b" ] && echo "OK $b" || echo "MISS $b"
done
```

## Scanned-PDF → Text Workflow

For PDFs where `pdftotext file.pdf - | wc -c` returns 0 (image-only pages):

```bash
PDF=/path/to/file.pdf
WORK=/sdcard/Hermes_Files/uploads/ocr_work   # or any writable dir
mkdir -p "$WORK" && cd "$WORK"

# 1. Rasterize (200 DPI is the OCR sweet spot; 300 for very small fonts)
pdftoppm -r 200 -png "$PDF" page

# 2. OCR each page (PSM 6 = single uniform block — right for most reports)
> all_text.txt
for f in page-*.png; do
  tesseract "$f" stdout --psm 6 2>/dev/null >> all_text.txt
done

# 3. Sanity check
wc -l all_text.txt   # 0 lines means PSM needs tuning
```

**PSM (page-segmentation mode) cheatsheet:**

| PSM | Use case |
|-----|----------|
| 3   | Default; auto-detect (mixed layout) |
| 4   | Columnar text (academic papers, magazines) |
| 6   | Uniform block of text — **most business reports, backtest outputs** |
| 7   | Single line (captions, stamps) |
| 11  | Sparse text (receipts, mostly-blank pages) |

Wrong PSM silently produces garbage — line count is your smoke test.

## PDFs to PNG (for vision_analyze)

```bash
# Small batch, JPEG is smaller — fine for vision
pdftoppm -jpeg -r 150 -f 1 -l 5 "$PDF" /path/page

# Full-res for OCR
pdftoppm -r 200 -png "$PDF" /path/page
```

`pdftoppm` page args are 1-based. `-f N -l N` extracts a single page.

## Image Ops (ImageMagick)

```bash
convert input.png -resize 2000x2000\> output.png   # shrink if >2000px
convert a.png b.png -append combined.png            # stack vertically
convert input.png -crop 800x600+100+100 crop.png    # WxH+X+Y
convert *.png +append mosaic.png                    # side by side
```

For Termux, always use `convert` (not `magick` — the latter is the ImageMagick v7 CLI; both exist but `convert` is universally present).

## HTML → PNG for Telegram delivery (Playwright Firefox, proot)

An HTML diagram/report does NOT render on Telegram as a message — send a PNG screenshot. On this Termux host, Chromium headless-shell crashes in proot; **Firefox (Playwright) works**.

```bash
proot-distro login ubuntu -- bash -c 'cd /root/myproject && node -e "
const { firefox } = require(\"/root/myproject/node_modules/playwright\");
(async () => {
  const b = await firefox.launch();
  const p = await b.newPage({ viewport: { width: 1100, height: 900 } });
  await p.goto(\"file:///data/data/com.termux/files/home/diagram.html\");
  await p.waitForTimeout(2000);
  await p.screenshot({ path: \"/root/myproject/diagram.png\", fullPage: true });
  await b.close(); console.log(\"done\");
})();"'
```

- Playwright module lives at `/root/myproject/node_modules/playwright` (NOT `/tmp/opencode/node_modules`) — use the absolute require path.
- Firefox binary: `/root/.cache/ms-playwright/firefox-1572/firefox/firefox`.
- Then `cp` the PNG into `$HOME` (host-visible) and send as `MEDIA:`.
- `fullPage: true` captures the whole diagram card, not just the viewport.

## Pitfalls

- **Files written to `/sdcard/Hermes_Almari/` (or any /sdcard path) show up empty in File Manager apps** because they are owned by `u0_a317:media_rw` with mode `660`/`2770`, and most third-party file managers (Material Files, Solid Explorer, etc.) filter out files not owned by the calling user or lacking world-readable bits. Termux itself reads them fine, but the phone UI shows nothing. Fix in one line:
  ```bash
  chmod -R g+rX,o+rX /sdcard/Hermes_Almari/
  ```
  Then touch the top-level dir to nudge file-manager caches:
  ```bash
  touch /sdcard/Hermes_Almari && for d in /sdcard/Hermes_Almari/*/; do touch "$d"; done
  ```
  Verify with `stat -c '%a %n' <path>` — files should show `644`/`755` (or at minimum group+other readable). `chown -R u0_a483:media_rw` also works but resets ownership to the current Termux user ID, which may break other apps that wrote the files. `chmod` is safer.
- **Do not retry `pip install pymupdf`** on Termux — it will not converge. Switch to `pkg install poppler` immediately. The wheel is a native .so that pip struggles to download/build on Android.
- **`/tmp` is not writable for scripts** in this environment. Write scripts to `$HOME` (e.g. `/data/data/com.termux/files/home/check.py`) and delete after use; `write_file` tool handles this cleanly.
- **`zip` is NOT installed in proot-distro Ubuntu** (`bash: zip: command not found`). Building a ZIP for delivery: use Python `zipfile` in a script (`write_file` then run), not the `zip` CLI. `python3 -c` heredocs with nested quotes/escapes are error-prone on Termux — write the script with `write_file` and run it.
- **`which` does not exist** on Termux (`/bin/which` is not linked). Use `[ -x /data/data/com.termux/files/usr/bin/<tool> ]` for presence checks.
- **`read_file` on binary PDFs returns `is_binary: true` with no text** — that is the signal to switch to OCR, not to retry. Do not report this as "no content in the PDF."
- **Heredocs in `terminal`** may hit approval friction on Termux. For multi-page OCR loops, write a small `.sh` file with `write_file` and run it, or use a one-liner `for` directly in the command.
- **OCR quality is font-size-sensitive**: if `tesseract` output looks like random noise (`fgzoi`, `ﬂ`), rasterize again at 300 DPI rather than tuning PSM.
- **`pkg install` is fast once; don't re-run unnecessarily.** `pkg update -y` before `pkg install -y` on first use only.

## Verify

- `pdftotext file.pdf - | wc -c` → 0 bytes means image-only, go OCR path.
- `wc -l ocr_all.txt` → non-zero line count after OCR means text landed.
- Spot-check first 200 chars of OCR output for the doc title / a known phrase; if that's garbled, PSM or DPI is wrong.

## Not This Skill

- Desktop PDF manipulation (merge/split/forms/stamps/watermarks) — use the bundled `pdf` skill.
- Text-based PDFs on desktop — `pymupdf` or `web_extract` is faster.
- HTML→PDF — headless browser, not OCR.
