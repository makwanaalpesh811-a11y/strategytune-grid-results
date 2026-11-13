# Telegram Bot API Cheatsheet — Deal Bot

Methods used by deal bots. All calls are `POST` to `https://api.telegram.org/bot<TOKEN>/<method>` with a JSON body. Responses are `{"ok": true, "result": ...}` or `{"ok": false, "error_code": N, "description": "..."}`.

## sendMessage

```json
{
  "chat_id": "-1001234567890",
  "text": "<b>Message</b>",
  "parse_mode": "HTML",
  "disable_web_page_preview": true,
  "disable_notification": false
}
```

Response `result` includes `message_id` — log it for later pin/delete.

- `chat_id`: int or `-100...` string for supergroups/channels.
- `parse_mode`: `HTML` for markup; Markdown is different (use `<b>` not `**`).
- `disable_web_page_preview`: set `true` for text-only messages to avoid link cards; set `false` when you want a rich link preview under the message.
- `disable_notification`: silent delivery (no sound) for low-priority posts.

## getChat

Read-only. Returns group title, ID, type, invite_link, and permissions.

```json
GET https://api.telegram.org/bot<TOKEN>/getChat?chat_id=-1001234567890
```

Use this to verify the bot can see the group before posting. If it errors, the bot was kicked or the group ID is wrong.

## pinMessage

Requires bot to be group admin with `can_pin_messages`. Otherwise returns 404.

```json
{"chat_id": "-1001234567890", "message_id": 135, "disable_notification": true}
```

Use `unpinAllChatMessages` (same shape minus `message_id`) to unpin.

## deleteMessage

```json
{"chat_id": "-1001234567890", "message_id": 134}
```

No "list messages" API — you must track sent `message_id`s in your own log, or sweep a guessed range and ignore the `"not modified"` responses.

## getUpdates

Only useful for bots polling for incoming messages (command handling). Not needed for one-way deal posting.

## Rate limits

- ~30 messages/minute globally per chat.
- 20 messages/second global per user token.
- After a 429, wait `retry_after` seconds (in `result.description` or response headers).
- Safe default: `time.sleep(3)` between consecutive posts.

## sendMediaGroup (album of photos with bio on first)

Sends multiple photos as a single album bunch. Caption attached to `media[0]` appears below the first photo when the user opens the album. This is the preferred format for scraped product images.

Uses **multipart/form-data** (not JSON) because it mixes file uploads with a JSON-encoded media array:

```python
import json, requests

media = []
for i, path in enumerate(files_list):
    entry = {'media': f'attach://file{i}', 'type': 'photo'}
    if i == 0:  # Caption ONLY on first photo
        entry['caption'] = bio_html
        entry['parse_mode'] = 'HTML'
    media.append(entry)

files = [(f'file{i}', open(path, 'rb')) for i, path in enumerate(files_list)]

r = requests.post(
    f'https://api.telegram.org/bot{token}/sendMediaGroup',
    data={
        'chat_id': '-100...',
        'media': json.dumps(media),          # JSON string, not raw list
        'disable_web_page_preview': 'false', # String, not bool
    },
    files=files,
    timeout=90,
)
```

Response `result` is an array of `{message_id, ...}` — one per photo. Log the first one as the album's anchor ID.

**Gotchas:**

- `media` must be a JSON string (`json.dumps(media)`), not a raw list.
- `attach://fileN` reference in each `media[i]` entry MUST match the multipart tuple key name (also `fileN`) in the `files` list. Mismatch = HTTP 400, no useful body.
- `disable_web_page_preview` must be a string `'false'`/`'true'` when in multipart data (bool serialization breaks the caption silently).
- Max 10 items per album; chunk larger sets.
- Caption is HTML-mode only when `parse_mode='HTML'` is set on that specific entry — the setting is per-photo, not global.
- Total file size per request: 50 MB. Each image max: 10 MB (photo), 50 MB (video).

## sendPhoto (single photo)

```json
{
  "chat_id": "-100...",
  "photo": "<URL or Attachment ID>",
  "caption": "<HTML bio>",
  "parse_mode": "HTML",
  "disable_web_page_preview": false
}
```

Use only for single-image posts. For multiple images per product, use `sendMediaGroup` instead — separate `sendPhoto` calls create N separate messages instead of one album.

## Parse mode — HTML entities

- `<b>` bold
- `<i>` italic
- `<s>` strikethrough
- `<a href="URL">text</a>` link
- `<code>` inline code
- `<pre>` code block
- `<br>` line break
- `<blockquote>` quote

Escaped chars: `&lt;` `&gt;` `&amp;` `&quot;`. Raw `<` `>` in user content must be escaped or Telegram returns a 400 `entities parse error`.
