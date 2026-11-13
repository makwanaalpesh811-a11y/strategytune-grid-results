# Flipkart Scrape → Save → Post Recipe

Validated end-to-end workflow for turning a Flipkart affiliate short link into a posted album in the Telegram group.

## 1. Resolve the short link

`dl.flipkart.com/s/xxxxx` is a shortened affiliate redirect. Follow it to get the real product URL:

```bash
curl -s -L -A "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)" \
  "https://dl.flipkart.com/s/xxxxx" \
  -o page.html -w "%{url_effective}\n"
```

Extract the canonical product path from the final URL (regex `flipkart\.com/[a-z0-9\-]+/p/[a-z0-9]+`), or parse it from the HTML body. The share page HTML does NOT contain product images — always fetch the resolved product page next.

**Sanity check the resolved URL before scraping:**
- `len(html) < 200_000` → not a real product (error, login, livestream, or empty share). Skip and report.
- URL contains `/play/watch` or `contentType=PURE_LIVE` → Flipkart Live stream, not a product. Skip.
- HTTP 500 with JSON body `{"serverErrorMessage":"Please try again later"...}` → rate-limited. Sleep 30–60s and retry the same code. Do NOT declare it dead after one attempt — Flipkart's short-link service blocks bursts, not individual codes.

## 2. Fetch the product page

```bash
curl -s -L -A "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)" \
  "https://www.flipkart.com/<slug>/p/<pid>" \
  -o product.html
```

Expect 1.1–1.4 MB of HTML. Title is in `<title>...</title>`. User-Agent choice is irrelevant — Desktop Chrome, mobile Safari, and Googlebot all work.

## 3. Extract data with regex

```python
import re
html = open('product.html').read()
title = re.search(r'<title>([^<]+)</title>', html).group(1)
imgs = list(dict.fromkeys(re.findall(
    r'https://[a-z0-9.\-]*flixcart\.com/image/[^"\s<>\)]+', html
)))
# Keep only 1500/1500 or 1600/1920 product shots (skip thumbnails & resized duplicates)
imgs = [u for u in imgs if '1500/1500' in u or '1600/1920' in u]
imgs = list(dict.fromkeys([u.split('?')[0] for u in imgs]))

price = re.findall(r'"price"\s*:\s*(\d+)', html)
Mrp = re.findall(r'"mrp"\s*:\s*(\d+)', html)
```

**Broaden the image regex to `https://[a-z0-9.\-]*flixcart\.com/image/...`**, not the narrow `rukmini\d*\.flixcart\.com`. Some products (ethnic sets, newer listings) live on `rukminim3.flixcart.com` or other `rukmini*` subdomains — the narrow regex returns 0 images for those products.

`list(dict.fromkeys(...))` preserves order while deduping — important because the same image URL appears multiple times in the HTML.

**If `"price"` regex returns nothing but the title & images are present**, the product page uses text-rendered prices instead of structured JSON. Fall back to:

```python
# Extract from the label structure (UNLOCKED = sale price, label_4 = MRP)
import re
matches = re.findall(r'"UNLOCKED":\{"value":\{"text":"(\d+)"\}\}.*?"label_4":\{"value":\{"text":"₹([\d,]+)"\}\}', html)
sale_price = int(matches[0][0].replace(',',''))
Mrp = int(matches[0][1].replace(',',''))
```

If even that fails, `re.findall(r'₹\s*([\d,]+)', html)` returns all price mentions including the "you may also like" rail — filter to values ≥ 100 and take the first pair (sale, MRP) where MRP > sale.

## 4. Download images

Images live at `rukmini1.flixcart.com` and are NOT hotlink-protected. Plain `requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})` returns 1500×1500 JPEGs (~100–350 KB each). Save to `photos/<slug>_<n>.jpg`. The suffix in the URL is what matters — don't append `.jpg` when the URL already ends in `.jpeg`.

## 5. Post as album with caption on FIRST photo

```python
import json, requests
from pathlib import Path

cfg = json.load(open('config.json'))
tok, grp = cfg['bot_token'], cfg['group_id']

bio = (
    '━━━━━━━━━━━━━━━━━━━━\n'
    '🔥 <b>{NAME} - DEAL</b> 🔥\n'
    '━━━━━━━━━━━━━━━━━━━━\n\n'
    '💰 <s>Rs{MRP}</s> → <b>Rs{PRICE}</b> ({OFF}% OFF)\n'
    '💵 <b>Save Rs{SAVINGS} today!</b>\n'
    '🎨 <b>Colors:</b> {COLORS}\n'
    '📏 <b>Size:</b> {SIZE}\n'
    '🧵 <b>Material:</b> {MATERIAL}\n'
    '🏷️ <b>Brand:</b> {BRAND}\n'
    '🚚 <b>Free Delivery</b> | COD\n\n'
    '━━━━━━━━━━━━━━━━━━━━\n'
    '👉 <a href="{URL}"><b>🛒 BUY NOW - Rs{PRICE}</b></a>\n'
    '━━━━━━━━━━━━━━━━━━━━\n\n'
    '⚡ Limited stock! | @alpeshalgobot\n'
    '📲 <i>Forward this to friends!</i>'
)

files_list = sorted(Path('photos').glob(f'{slug}_*.jpg'))
media = []
for i, p in enumerate(files_list):
    entry = {'media': f'attach://file{i}', 'type': 'photo'}
    if i == 0:
        entry['caption'] = bio
        entry['parse_mode'] = 'HTML'
    media.append(entry)
files = [(f'file{i}', open(p, 'rb')) for i, p in enumerate(files_list)]

r = requests.post(
    f'https://api.telegram.org/bot{tok}/sendMediaGroup',
    data={'chat_id': grp, 'media': json.dumps(media), 'disable_web_page_preview': 'false'},
    files=files, timeout=90,
)
```

`disable_web_page_preview` MUST be `false` — the link preview is the visual anchor users tap.

## 6. Save to products.json

Schema is a dict, NOT a list:

```json
{
  "default": [...],
  "products": [
    {
      "id": 35,
      "name": "Product Full Name",
      "emoji": "👕",
      "category": "Men's Sweatshirt",
      "price": 417,
      "mrp": 1999,
      "off": 79,
      "colors": ["Grey"],
      "sizes": ["S", "M", "L", "XL", "XXL"],
      "material": "Cotton Blend",
      "url": "https://www.flipkart.com/<slug>/p/<pid>?affid=inf_...",
      "source": "flipkart",
      "images": ["posu_1.jpg", "posu_2.jpg", "posu_3.jpg", "posu_4.jpg"]
    }
  ]
}
```

Append new products to `data['products']` (not `data`). Always write with `indent=2, ensure_ascii=False` so emojis and `&` in URLs stay readable.

## Pitfalls specific to this workflow

- **The share-link HTML has 0 images** — it's a redirect wrapper. Always resolve to the real `/p/<pid>` URL first, then fetch that.
- **Don't append `.jpg` to image URLs** that already end in `.jpeg`. The rukmini CDN 404s on the wrong suffix. Preserve the URL's original extension.
- **`disable_web_page_preview` MUST be `'false'`** (string, not bool). Telegram silently treats any truthy value as "hide preview." The preview is what makes the affiliate link clickable with a nice card.
- **The affiliate `affid=inf_...` param must be on the product URL** for commission attribution. The `dl.flipkart.com/s/` short link redirects to a URL that already has `affid=` — preserve it when saving to `products.json`.
- **Never paste the raw affiliate URL in caption** — always wrap in `<a href>...</a>` with a `BUY NOW` label. Raw URLs render as plain text with no tap affordance and kill CTR.
