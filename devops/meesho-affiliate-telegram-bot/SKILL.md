---
name: meesho-affiliate-telegram-bot
version: 1.0.0
author: Alpesh Makwana
license: MIT
platforms: [android, termux]
description: "Use when setting up Meesho affiliate auto-posting."
---

# Meesho Affiliate + Telegram Auto-Poster

Build an auto-poster that shares product photos + affiliate links to a Telegram group on a schedule (5-10 posts/day, 0 manual work).

## Reality check (establish these first, don't promise what doesn't work)

- **Meesho does not allow product scraping** (Cloudflare + EdgeSuite) — `www.meesho.com/api/v1/search`, `api.meesho.com/v1/api/search`, mobile endpoints, and the affiliate invite redirect all return 403/404 to unauthenticated requests. Do not promise "scrapes Meesho top products daily."
- **Flipkart IS scrapable from a server** and its affiliate program (`affid=inf_...`) works fine — so the practical pipeline is a curated Flipkart affiliate product list, not Meesho. Scrape Flipkart images on demand; see the Pitfalls section for the curl + regex recipe.
- **`ajiio.cc`, `ajiio.com`, `meesho.cc` etc. are typosquatting ad landers.** Always use the real domain: `ajio.com`, `meesho.com`, `nykaa.com`.
- **Direct Meesho Creator Club affiliate** requires 10K Instagram followers or 5K YouTube subscribers for reliable approval. Below that, get a **GrabCash** affiliate account instead (no follower minimum, up to 25% commission, ₹10 payout, 30-day cookie, multi-brand).
- **No Termux-native Meesho app automation is possible.** Official `termux-api` (v0.53 and v0.60) has NO `termux-tap` and NO `termux-screenshot` commands — verified by listing the scripts/ directory on every tagged release in the `termux-api-package` repo. Neither is a regression from a removed feature; it never shipped. What Termux:API provides: clipboard, open-url, toast, notification, camera, WiFi, sensors, battery, contact, SMS — but no touch injection, no screen capture, no accessibility tree. Any automation plan claiming to drive an Android app from Termux must either (a) use third-party forks (`termux-api-addon` ecosystem, unofficial), (b) run proot Ubuntu with Playwright, or (c) run the scraper on Google Colab. Do not sell "I can drive the Meesho app from Termux" — user has no way to grant tap/screenshot without one of those.
- **`agent-browser` npm package does not build for Android.** Hermes's `browser_exec` tool depends on it. The installed package's wrapper detects platform via `uname -s -m` and rejects `android-arm64` with `Unsupported platform`. `agent-browser install` will not fetch a browser because the wrapper fails before it runs. This means the built-in browser automation is unavailable on Termux — do not present manual-login-handoff / affiliate-link-generation flows that require browser control. Ask the user to do it on their phone and send the result back.
- **User preference: DRAFT BEFORE IMPLEMENT.** For any non-trivial feature or workflow change, write a draft spec first and wait for `ok` before touching code. Applies to scrapers, poster scripts, cron schedules, group layouts. If user says "draf me karege agar me ok bolu to implement karege," freeze everything except spec writing.
- **User preference: NEVER delete uploaded videos/posts without explicit instruction.** "Delete all messages" = group posts only, never personal Hermes chat.
- **User preference: Hinglish short answers.** 3-5 bullets, emoji labels, decisive. No prose essays. No filler. When unclear, offer 3-4 labeled options and let user pick.
- **`ajiio.cc`, `ajiio.com`, `meesho.cc` etc. are typosquatting ad landers.** Always use the real domain: `ajio.com`, `meesho.com`, `nykaa.com`.

## Affiliate program comparison

| Platform | Follower min | Commission | Payout | Cookie | Approval |
|---|---|---|---|---|---|
| Meesho Creator Club (direct) | 10K IG / 5K YT | 9% catalog, 0.5% non | ~21 days | not disclosed | 24-72h |
| **GrabCash** | None | Up to 25% | 7-14 days | **30 days** | Instant |
| EarnKaro | None | Up to 15% | 30 days | 30 days | Instant |
| ExtraPe | None | Up to 20% | 30 days | not disclosed | Instant |

**Recommendation for beginners:** GrabCash first (works immediately), Meesho Creator Club after Instagram grows.

## Telegram bot setup (user side)

1. In Telegram, DM `@BotFather` → `/newbot` → name → username ending `_bot` → bot returns `TOKEN` (starts with digits + colon).
2. Never share the token publicly. Save to `~/.meesho_bot_env` with `chmod 600`.
3. For existing-user bot: check `~/.signal_bot_env` (`TG_TOKEN=`) — many users already have a bot token from earlier Hermes setup. Verify with `curl https://api.telegram.org/bot<TOKEN>/getMe`.

### Critical pitfall: token in Python code gets auto-redacted

Hermes terminal and tool-output pipeline **redacts strings that look like API tokens** (long alphanumeric+colon+alphanumeric). If you write `BOT_TOKEN = ***"TG_TOKEN")` inside a Python file and the env var contains an actual token, tool output will show `***` for the value AND — worse — the *write* can leave a corrupted `BOT_TOKEN = ***"TG_TOKEN", "")` in the file, breaking syntax.

**Do this instead:** write a `config.json` at project root with `bot_token` and `group_id`, generated by execute_code reading `~/.signal_bot_env` directly (execute_code's `open()` path is not redacted):

```python
# Generate config.json (execute_code, not terminal heredoc)
import json
with open('/path/to/.signal_bot_env') as f:
    token = next(l.split('=',1)[1].strip() for l in f if l.startswith('TG_TOKEN='))
json.dump({'bot_token': token, 'group_id': GROUP_ID},
          open('/path/to/project/config.json', 'w'))
```

Then `meesho_bot.py` reads `config.json` at runtime with plain `json.load(open(CONFIG_PATH))`. No env lookup, no redaction, no shell interpolation. `write_file` and terminal heredocs that include the literal token string will get redacted on their way back to the model — always route the actual secret through `open()` in execute_code, not through shell variables or heredoc bodies.

## Telegram group ID discovery

Order of preference:
1. `@getidsbot` — most reliable, adds itself to group and posts `Group ID: -100...`.
2. `@myidbot` — fallback, adds itself and posts `Chat ID: -100...`.
3. `@RawDataBot` — prints full chat object as JSON.
4. **Manual fallback:** Group settings → Invite Link → copy the URL. Either `t.me/+AbCdEfGh...` (private invite) or `t.me/groupname` (public). The user can share the public group link with the bot owner, who decodes the group ID client-side.

**Group ID is always negative and starts with `-100` for groups, `-100123...` for channels. Personal chat IDs are positive integers.**

## Auto-poster architecture

```
products.json  ─▶  meesho_bot.py  ─▶  Telegram Bot API  ─▶  Group
                       ▲
                       │
                   cron (every 3h)
```

- `products.json`: curated list of 20-50 products with name, price, mrp, discount %, image URL, affiliate link, description.
- `meesho_bot.py`: reads JSON, rotates products (avoid duplicates within a day), formats message, sends photo + caption via Bot API.
- `run.sh` + `crontab -e`: schedule. `python3 ~/meesho_bot/meesho_bot.py >> log.txt 2>&1`.

## Message format (proven template)

```
🔥 DEAL OF THE DAY 🔥

<emoji> <Product Name> (<Size/Variant>)
💰 <s>Rs<mrp></s> → <b>Rs<price></b> (<off>% OFF)
💵 <b>Save Rs<mrp-price> today!</b>
🎨 <color1> | <color2> | <color3>
🚚 Free Delivery | COD Available

👉 <a href="<affiliate_link>"><b>🛒 BUY NOW - Rs<price></b></a>

⚡ Limited stock | Hurry!
📲 <i>Forward this to friends!</i>
```

Use Telegram HTML parse mode — `<a href>`, `<b>`, `<i>`, `<s>` (strikethrough). Linkify the buy-now call-to-action; never paste a raw URL.

### Photo upload: send all photos as ONE album (bunch) with caption on first

User wants ALL product photos delivered as a single bunched album with the product bio + affiliate link attached as the caption on the FIRST photo — NOT one photo + caption, NOT a separate bio message below the album.

`sendMediaGroup` requires multipart upload with `attach://fileN` references that MUST match the `fileN` form-field names, and `media` must be a JSON-encoded array. Caption goes inside the first media object with `parse_mode: "HTML"`:

```python
media = []
for i, path in enumerate(image_paths):
    entry = {"media": f"attach://file{i}", "type": "photo"}
    if i == 0:
        entry["caption"] = bio_text       # HTML caption
        entry["parse_mode"] = "HTML"
    media.append(entry)
files = [(f"file{i}", open(p, "rb")) for i, p in enumerate(image_paths)]
requests.post(
    f"https://api.telegram.org/bot{token}/sendMediaGroup",
    data={"chat_id": group_id, "media": json.dumps(media),
          "disable_web_page_preview": "false"},
    files=files, timeout=90,
)
```

If the `attach://` refs and `fileN` field names don't match exactly, Telegram errors. A caption-less `sendPhoto` loop sends N separate messages (not a bunch) — always use `sendMediaGroup` for albums. Cap at ~10 photos per album (Telegram limit).

Rotate 2-3 "top sellers" daily + 2-3 fresh picks.

## Schedule recommendation

```crontab
0 6,9,12,15,18,21 * * * cd ~/meesho_bot && python3 meesho_bot.py >> log.txt 2>&1
```

6 posts/day. Peak India e-commerce hours: 7-10pm and Sunday afternoons. Add a 22:00 or 21:30 slot if traffic warrants it.

## Pitfalls

- **Flipkart, however, scrapes cleanly from a server — but only via `www.flipkart.com`.** `curl -A "Mozilla/5.0 (iPhone...)" -L "https://www.flipkart.com/<slug>/p/<pid>"` returns a 1.1–1.4 MB page with full product data. Extract images with regex `https://rukmini\d*\.flixcart\.com/image/[^"\s<>]+`, prices with `"price"\s*:\s*(\d+)`, MRP with `"mrp"\s*:\s*(\d+)`. Since Meesho is blocked but Flipkart is open, curate a maintained JSON of Flipkart affiliate products and scrape their images on demand rather than hand-collecting every image.
- **`dl.flipkart.com/dl/<slug>/p/<pid>` returns a React-rendered shell with NO product data.** It has a truncated h1, `"price":366` in a nested cart JSON blob, but NO JSON-LD Product, NO MRP, NO rating, NO image list. When a share URL starts with `dl.flipkart.com/dl/`, rewrite it to `www.flipkart.com/<same-path>` (preserve query string) before fetching. This is a hard rewrite — the `www.` URL is what actually renders server-side HTML.
- **`dl.flipkart.com/s/XXXXX` short share links** redirect to a real product URL. Follow the redirect with `-L` and then fetch the resolved `www.flipkart.com/...` URL. Do NOT scrape the share page HTML — it's a redirect wrapper with 0 images.
- **Telegram `sendMediaGroup` CANNOT curl Flipkart's CDN directly.** Sending `{'media': 'https://rukminim2.flixcart.com/...'}` fails with `WEBPAGE_CURL_FAILED`. Telegram's image proxy can't reach Flipkart's CDN. **Always download images locally first, then upload as multipart form data** with `attach://file0..N` references. Use `requests.post(files=[('file0', ...), ...])` — a hand-rolled urllib multipart builder will silently fail with `media not found` because `attach://` needs proper boundary + filename headers.
- **Flipkart product images are often NOT at 1500x1500.** Only 1-3 images are actually 1500/1500; the rest are 530x710, 800x1070, etc. Force the CDN to `1500/1500` by URL rewriting (`/image/<w>/<h>/<path>` → `/image/1500/1500/<path>`) — the rukmini CDN accepts any size. Filter out thumbnails (<300x300 or square ≤120x120) to avoid sidebar icons. Fallback chain: JSON-LD Product.image → page images matching product slug filename → any >=300x300 page images.
- **JSON-LD `<script type="application/ld+json">` blocks are sometimes `[]`** (empty list) on newer Flipkart pages. Fallback: parse the h1 with `<div>more</div>` inside (strip inner HTML, remove trailing `...` and `more` text), then og:title if it doesn't contain `{TITLE}` template placeholders, then `<title>`, then product-name regex on the JSON blob.
- **Flipkart's `og:title` is often `{TITLE}` template placeholder** — skip it if it contains `{`. The actual product name is in h1 (but wrapped in a `<div>more</div>` expand button that must be stripped).
- **Do not send separate messages for photos and bio.** User rejects both "one photo + caption" and "bio in a separate message below the album." The correct shape is ONE `sendMediaGroup` album carrying every photo plus the bio caption on the first photo. A `sendPhoto` loop produces N individual messages, not a bunch.
- **`getidsbot` sometimes doesn't post in the group.** If the user adds the bot and no message appears, try `@myidbot` or `@RawDataBot`. Third fallback: group public invite link → user can share with bot owner.
- **Bot must be added to the group BEFORE posting.** `sendPhoto`/`sendMessage` to a group chat_id fails with 403 if the bot isn't a member.
- **Rate limits:** Telegram Bot API is 30 messages/second global + 20 messages/minute per chat. 6-12 messages/day is nowhere near the limit; don't over-engineer retry logic.
- **Flipkart scraping recipe** (share link → product page → images → album post → save to products.json): see `references/flipkart-scrape-and-post.md`.
- **Message format template and `sendMediaGroup` album shape** for the caption-on-first-photo layout: see `references/flipkart-scrape-and-post.md`.
- **Photo URLs from Meesho may 404 or be hotlink-protected** in the browser when accessed via bot API. Test that image URLs load with a plain curl before trusting them in messages. If 403, download the image locally first and send as multipart form.
- **Never delete the user's personal Hermes chat.** If the user has an existing bot bound to a personal chat_id in `~/.signal_bot_env`, that's their Hermes session — the new posting must go to a *separate* group chat_id.
- **Don't delete messages in the personal Hermes chat by mistake.** "Delete all messages" from the user should be interpreted as *delete old posts in the new group only*, never as `deleteMessage` on the personal chat.

## Verification

1. `curl https://api.telegram.org/bot<TOKEN>/getMe` returns bot username.
2. `curl https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<group_id>&text=test` returns `"ok":true`.
3. Group shows the test message.
4. First `meesho_bot.py` dry-run prints the formatted message without sending.
5. Cron installed: `crontab -l` shows the entry.
