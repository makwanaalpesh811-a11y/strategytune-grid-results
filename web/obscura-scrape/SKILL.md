---
name: obscura-scrape
description: 'Use when scraping Flipkart/Meesho on Termux via Obscura.'
---

# Obscura Scrape (Flipkart / Meesho / bot-wall sites)

## Setup (already done on this device)
- Binary: `~/obscura/run/obscura` + `obscura-worker` (aarch64 stealth build, v0.2.6)
- Runtime: **Ubuntu container** via `proot-distro login ubuntu` (Termux = bionic, binary = glibc Linux, isliye container chahiye)
- Container me path: `/data/data/com.termux/files/home/obscura/run/`

## Why proot-distro
Obscura binary glibc-linked hai. Termux Android (bionic) pe directly `required file not found` deta hai. Ubuntu container glibc provide karta hai.

## Helper script
`~/obscura/run/obscura_scrape.sh "query" [flipkart|meesho] [limit]`

### Flipkart
- `scrape --stealth -e '<eval>'` — DOM selector se title+price+rating+link
- Eval file se pass karo (`_eval.js`) — nested quotes bash me toot jaate hain
- Title selector: lines me `/iphone|apple|realme|.../` match; price = `₹` wali line; rating = `Ratings` wali line
- Link: `a[href*="/p/"]` ke `.href.split('?')[0]`

### Meesho (SPA lazy-load)
- DOM selector me products NAHI aate (render nahi hota) → `fetch --stealth --dump links` use karo
- Links format: `URL\t title₹price rating`
- Parse: `/p/` wali lines, tab-split, title=price se pehle ka text, strip `\d+ More` / `More` / `Others` prefixes

## Pitfalls
- Nested quotes (`'` + `"`) bash me toot jaate hain → eval ko file me likh kar `$(cat file)` se pass karo
- Meesho DOM scrape = empty. `--dump links` hi kaam karta hai
- `set -e` + pipe me `|| true` use karo (obscura non-zero exit de sakta hai)
- Variable substitution heredoc me nahi hota → `python3 - "$VAR"` argv se pass karo
- Har fetch ~15s le jaata hai, timeout 90-120s rakho
