---
name: telegram-deal-bot
description: Post affiliate deals to a Telegram group via Bot API.
version: 1.0.0
author: Alpesh Makwana (Hermes)
license: MIT
platforms: [termux, linux]
---

# Telegram Deal Bot

Automated Telegram group poster for affiliate/e-commerce product deals. Use when the user wants a bot to push products, coupons, or links to a Telegram group on a schedule or on demand.

## Core Pattern

Three files, one Python script:

```
~/<project>/
├── config.json        # bot_token + group_id (chmod 600, NEVER commit)
├── products.json      # {"products": [{id, name, price, mrp, off, emoji, url, colors, category}]}
└── deal_bot.py        # CLI: verify | test | post | welcome | pin | history
```

All Telegram calls go through `requests.post(f"https://api.telegram.org/bot{token}/<method>", json={...})`. Group IDs always start with `-100`. Read config at runtime from the JSON file, not from environment variables — redaction filters corrupt `os.environ` reads in tool outputs.

## Two Post Flows

**Text-only** (Meesho / affiliate without photos): `sendMessage` with HTML caption. Fast, no image handling.

**Photo album + bio below** (Flipkart scraped photos, user's preferred format): `sendMediaGroup` sends all photos as one album bunch with the product bio + affiliate link as `caption` on the FIRST photo only. See Step 4b for the exact pattern — `attach://file0..N` names in the `media` array must exactly match the `files` multipart keys or Telegram returns 400.

## Steps

### 1. Group + Bot setup

- User creates a Telegram group manually (needs ≥2 members for a supergroup).
- User adds the existing bot to the group.
- Get group ID via `@getidsbot` (add to group, bot auto-posts `-100xxxxxxxxx`).
- **Bot must be ADMIN to pin messages.** Group settings → Edit → Members → find bot → Add to Admins → enable Pin Messages. Without admin, `pinMessage` returns HTTP 404.

### 2. Config file

```json
{"bot_token": "<from BotFather>", "group_id": "-1001234567890"}
```

Read this at script start. Do not store token in env vars or `.env` for automation scripts — env is fine for one-shot reads but tool-output redaction breaks it for repeated calls.

### 3. Post format (HTML mode)

Telegram `parse_mode='HTML'` supports `<b>`, `<i>`, `<s>`, `<a href=\"url\">text</a>`, `<code>`, `<pre>`, `<br>`, `<blockquote>`. NO Markdown. Wrap prices in `<s>` for strikethrough, key CTA in `<a href>` for clickable button-style link.

Template that lands well:

```
🔥 MISHOO DEAL OF THE DAY 🔥
📅 24 Oct, 10:26 PM

👗 <b>Cotton Kurti</b>
💰 <s>₹999</s> → <b>₹499</b> (50% OFF)
⭐ 4.2⭐ | 500+ happy customers
🎨 <b>Colors:</b> Blue | Green | Pink
🚚 <b>Free Delivery</b> | COD Available

━━━━━━━━━━━━━━━━━━━━
👉 <a href="URL"><b>🛒 BUY NOW - ₹499</b></a>
━━━━━━━━━━━━━━━━━━━━
```

### 4. Post + rate-limit

Telegram allows ~30 messages/min globally per chat. Sleep 3s between posts in a batch. `disable_notification=true` on non-Deal-of-Day posts to reduce spam feel.

### 4b. Photo album with bio below (Flipkart-scraped photos)

For scraped Flipkart products, the user wants ALL photos posted as one bunch with the product bio below. Do NOT send each photo as a separate `sendPhoto` — that creates N separate messages. Use `sendMediaGroup` with caption attached to the first photo only:

```python
media = []
for i, p in enumerate(files_list):
    entry = {'media': f'attach://file{i}', 'type': 'photo'}
    if i == 0:  # Caption ONLY on first photo
        entry['caption'] = bio
        entry['parse_mode'] = 'HTML'
    media.append(entry)

files = [(f'file{i}', open(p, 'rb')) for i, p in enumerate(files_list)]

r = requests.post(
    f'https://api.telegram.org/bot{tok}/sendMediaGroup',
    data={'chat_id': grp, 'media': json.dumps(media), 'disable_web_page_preview': 'false'},
    files=files,
    timeout=90,
)
```

**Critical rule:** the `attach://file0` reference in `media[i]` MUST match the multipart key name (`file0`) in the `files` tuple. Mismatch = HTTP 400 with empty body. Also `disable_web_page_preview` must be a string `'false'`/`'true'` in multipart data (not a bool) — bool gets serialized incorrectly and drops the caption.

### 5. Rotation / dedup

Track posted product IDs in `post_history.json` (keep last 100). Sample new posts from `products − recent`. This prevents the bot posting the same product twice in a row across cron runs.

### 6. Cron

Schedule `python3 deal_bot.py post 3` every 3–4 hours via Hermes cronjob or system cron. 6–8 runs/day = ~12–18 posts.

## CLI commands to include

- `verify` — `getChat` to confirm bot access to group
- `test <id>` — post one product with Deal-of-Day header
- `post <count>` — random-sample N products, 3s between posts
- `welcome` / `rules` — send intro/rules message
- `pin <msg_id>` / `unpin` — pin/unpin (requires admin)
- `history` — print post_history.json
- `clear` — delete bot's recent messages (loop `deleteMessage` from N downwards)

## Flipkart Batch Scrape Workflow (`~/meesho_bot/batch/flipkart_batch.py`)

User's canonical script for bulk Flipkart affiliate posts. Stdlib-only, ~530 lines. Full pipeline: URL file → scrape → download images → `sendMediaGroup` → sent.json dedup.

### Key URL rewriting rule (critical for scraping)

`dl.flipkart.com/dl/<slug>/p/<pid>` short URLs redirect to a **React-rendered page with no JSON-LD and no prices in HTML**. Rewrite BEFORE fetching:

1. Extract slug+pid from path: `dl.flipkart.com/dl/<slug>/p/<pid>` → `www.flipkart.com/<slug>/p/<pid>`
2. **Keep ONLY the `pid=XXX` query param.** Extra params (`lid`, `marketplace`, `fm`, `affid`) cause Flipkart to return a stripped-down 1.2 MB page without JSON-LD price data (no `"price"`, no `"finalPrice"`, no `"mrp"`). With only `?pid=X`, the page returns 1.3 MB with full JSON-LD.
3. Save the ORIGINAL input URL to `d["orig_url"]` and use THAT in the caption (preserve user's affiliate tracking params). Only the fetch URL is rewritten.

Example rewrite:
```
# input:  https://dl.flipkart.com/dl/foo-bar-t/p/itm123?pid=ABCDEF&lid=LSTABCDEF&marketplace=FLIPKART&affid=...
# fetch:  https://www.flipkart.com/foo-bar-t/p/itm123?pid=ABCDEF
# caption: use the original input URL (with all params intact)
```

### Price extraction (order matters)

JSON-LD price fields (in priority order): `sellingPrice` → `price` → `finalPrice` → `nepPrice` → `fsp`. The order matters — `finalPrice` often appears BEFORE the actual `price` in the page, so a naive `re.search` without ordering returns the wrong value. Also `"price"` in JSON-LD `offers.price` is the selling price; `"mrp"` is the MRP.

HTML fallback (when JSON-LD missing — happens for some short URLs even after rewrite): search for `₹(\d{2,5})` or `Rs\.(\d{2,5})` near the h1. Filter out values <100 (product prices) and <200 (MRPs).

### Image extraction (3-step filter)

Flipkart image URLs look like `https://rukminimX.flixcart.com/image/W/H/<path>`. Strategy:

1. **Canonical images**: parse JSON-LD `Product.image[]` — these are the actual product images. Force 1500/1500 size by regex-swapping `/\d+/\d+/`.
2. **Filename match**: other page images whose filename (last path segment) matches a canonical image's filename. Skip thumbnails under 200x200.
3. **Slug keyword filter**: if only 1 image found, expand to other 1500/1500 candidates, filtering by slug keywords extracted from the URL (brand name tokens ≥4 chars, excluding stopwords like men/women/color names). If still <5, take more anyway.

### Image upload: MUST download locally

`sendMediaGroup` with image URLs pointing to `rukmini*.flixcart.com` fails with `WEBPAGE_CURL_FAILED` — Telegram's servers can't fetch Flipkart CDN. Solution: download each image to a local file first, then use `requests.post` with multipart `files=` and `attach://fileN` references.

```
import requests
media = []
files = []
for i, p in enumerate(local_paths):
    entry = {"type": "photo", "media": f"attach://file{i}"}
    if i == 0:
        entry["caption"] = caption
        entry["parse_mode"] = "HTML"
    media.append(entry)
    files.append((f"file{i}", (os.path.basename(p), open(p, "rb"), "image/jpeg")))

r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMediaGroup",
    data={"chat_id": group, "media": json.dumps(media), "disable_web_page_preview": "false"},
    files=files,
    timeout=120,
)
```

The `attach://file{i}` in `media[i]` MUST match the multipart tuple key `("file{i}", ...)`. `disable_web_page_preview` must be a **string** `'false'`/`'true'` in multipart data (bool gets serialized incorrectly and drops the caption silently).

### Caption format (user's DEAL OF THE DAY template)

User rejected simpler captions — wants the full Deal-of-the-Day format with dividers, MRP strike-through, savings line, and BUY NOW link:

```
━━━━━━━━━━━━━━━━━━━━
🔥 <b>DEAL OF THE DAY</b> 🔥
━━━━━━━━━━━━━━━━━━━━

🛍️ <b>{product_title}</b>
💰 <s>Rs{mrp}</s> → <b>Rs{price}</b> ({off}% OFF)
💵 <b>Save Rs{savings} today!</b>
⭐ {rating} ({rcount} ratings)
🚚 <b>Free Delivery</b> | COD Available

━━━━━━━━━━━━━━━━━━━━
👉 <a href="{original_affiliate_url}"><b>🛒 BUY NOW - Rs{price}</b></a>
━━━━━━━━━━━━━━━━━━━━

⚡ <b>Limited stock!</b>
📲 <i>Forward this to friends!</i>
```

Caption attached ONLY to first photo of the album. HTML markup (not Markdown). Use `Rs` not `₹` — user's established format.

### CLI usage

```
python3 flipkart_batch.py <urls_file>           # post to Telegram
python3 flipkart_batch.py --dry <urls_file>     # preview caption + images
python3 flipkart_batch.py --trend <category_url> --n 10  # harvest + post from category
python3 flipkart_batch.py --min-rating 4.0 --min-ratings-count 500 <file>
```

Requires env: `BOT_TOKEN`, `CHAT_ID`, `AFFID`. `sent.json` in script dir dedups by pid.

## Pitfalls

- **"DRAF me karo" = plan only, no code.** When user says draft/plan/draf, write a `.md` file with options + tradeoffs only. Do NOT write scripts, do NOT touch existing code, do NOT create `.py` files. Implement only after explicit OK. Violated this rule 2x in one session (wrote full 400-line script when user said "draft"; completed user's truncated script without asking). Check user's exact words before assuming implementation is wanted.
- **When user shares their own code, review only.** Do not complete truncated code, do not "improve", do not rewrite. Report bugs + suggestions, ask before touching. User wants to own their code. If you spot a fatal bug (crash-on-start), flag it prominently but don't patch without permission.
- **Scraping works on Flipkart but is blocked on Meesho/Amazon.** Meesho returns 403 with Cloudflare+EdgeSuite; all server-side requests fail. Flipkart works reliably: `curl` with mobile UA (e.g. `Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)`) returns 1.1 MB pages with `"price"`, `"mrp"`, `"rating"` JSON fields and image URLs under `https://rukmini*.flixcart.com/image/...`. Googlebot UA (`Mozilla/5.0 (compatible; Googlebot/2.1)`) also works and returns slightly larger pages. Regex-extract: `r'<title>([^<]+?)\s*-\s*Buy'` for title, `r'"price"\s*:\s*(\d+)'` for price, `r'"mrp"\s*:\s*(\d+)'` for MRP. For image URLs use `r'https://[a-z0-9.\-]*flixcart\.com/image/[^"\s<>\)]+'` — the CDN has many subdomains (`rukmini1`, `rukminim1`, `rukminim2`, `rukminim3`, `rukminir`, etc.), so a pattern that only matches `rukmini\d*` silently misses a large share of images. After collecting URLs, filter to `1500/1500` or `1600/1920` sizes and deduplicate by base URL (strip `?` query).
- **Flipkart short URLs (`/s/XXXXX`) return HTTP 500 for deleted/inactive products — this is permanent, not rate limiting.** Body is tiny (`{"serverErrorMessage":"Please try again later"}`) at ~119 bytes. Do not retry with backoff; these products are gone. Move on and let the user know the link is dead. Genuine rate limiting shows HTTP 429 or slow responses on otherwise-valid pages.
- **Flipkart combo/multi-pack products render as near-empty pages** (title stays as generic `Buy Products Online at Best Price in India`, `price`/`mrp` fields return `0` or are absent). This happens for product URLs whose slug contains `-combo`. Combo data lives in a separate API call, not the initial HTML. Skip these products — they cannot be scraped with the standard regex workflow.
- **Flipkart short URL redirects can produce malformed final URLs** like `https://dl.flipkart.com/dlhttp://www.flipkart.com/...` — the `dlhttp://` prefix is a server-side bug in Flipkart's redirector. `curl -L` follows these to the target page but the response is only ~1.7 KB with no product data. Treat as dead link.
- **Search pages don't contain rating data.** `flipkart.com/search?q=...` and category pages (`flipkart.com/q/mens-shirts`) return product URLs but no ratings or review counts — those live only on individual product pages. To find trending products: scrape 4-9 search/category pages for URLs, then visit each unique product URL individually to extract rating+price+MRP+images.
- **Affiliate link format:** `?affid=<your_affiliate_id>` appended to any Flipkart product URL attributes sales. Extract user's `affid` once from a real affiliate link they paste and store in `config.json`; always append it to scraped product URLs.
- **Pin returns 404 without admin.** If `pinMessage` returns `{'ok': false, 'error_code': 404}`, tell user to grant admin rights in group settings before retrying. Do not retry silently.
- **Group ID must be the supergroup ID, not the invite link.** `-100xxxxxxxxx` numeric string, not `t.me/...`.
- **HTML not Markdown.** `<b>` not `**`, `<a href>` not `[x](url)`. Mixed markup raises `parse_entities` errors.
- **Do not put bot token in the Python source.** Even `os.environ['TG_TOKEN']` gets redacted in tool output; use a config file and load it via `json.load`.
- **Delete messages requires explicit IDs** — Telegram has no "list messages" API. Log every `message_id` sent, or sweep a range downward with `deleteMessage` and accept the noise. When deleting a range: `for mid in range(highest, lowest-1, -1): deleteMessage(mid)` — reverse order avoids rate-limit churn.
- **Rate-limit on batch posts.** 3s sleep per post; going faster raises 429s and forces a full minute backoff.
- **`sendMediaGroup` caption goes on FIRST photo only.** Attaching caption to multiple photos or as a separate message breaks the "bunch" visual. Caption appears below the first photo when user opens the album.
- **Multipart file keys must match `attach://` refs exactly.** `attach://file0` in `media[0]` requires the multipart tuple to be `('file0', open(path, 'rb'))` — not `('photo', ...)` or `('attachment_0', ...)`. Mismatch = HTTP 400 with no useful error body.
- **Flipkart CDN images fail in `sendMediaGroup` with URL-based media.** Telegram's servers can't fetch `rukmini*.flixcart.com` — returns `WEBPAGE_CURL_FAILED`. Download each image to a local file first, then use `requests.post` with `files=` multipart uploads. Never pass Flipkart CDN URLs directly as `media` entries.
- **Extra query params on `www.flipkart.com` URLs strip JSON-LD.** Fetching `www.flipkart.com/<slug>/p/<pid>?pid=X&lid=Y&marketplace=Z&affid=W` returns a 1.2 MB page without `"price"`/`"finalPrice"`/`"mrp"` JSON fields (React-rendered variant). Keeping ONLY `?pid=X` returns the 1.3 MB page with full JSON-LD. Strip extra params before fetching, preserve the original URL for the caption.
- **`disable_web_page_preview` in multipart data must be a string** `'false'`/`'true'`, not a Python bool. Bool serialization drops the caption field silently.
- **Products JSON can be a dict with wrapper.** Real-world `products.json` files often look like `{"default": {...}, "products": [...]}` — not a bare list. Check with `isinstance(data, dict)` before `.append()` on it; appending to the dict itself raises `AttributeError`.
- **Affiliate link generation requires platform approval** (Meesho Creator Club, GrabCash, etc.). Direct Meesho product URLs don't attribute commission to the poster unless they're their own affiliate links. Warn the user that without an approved affiliate program, they drive traffic but earn nothing.
