# Troubleshooting (every error below was hit in real setup)

| Symptom | Cause | Fix |
|---|---|---|
| `Access blocked ... has not completed verification` / `403 access_denied` | Gmail not in Test users | Audience -> Test users -> add it; wait 2 min |
| `400 redirect_uri_mismatch` | `http://localhost` is missing from **Authorized redirect URIs** (maybe only in JS origins), or has a space/typo, or old client ID used | Add exactly `http://localhost` under redirect URIs, Save, wait 5 min, use the new client ID, generate a fresh auth URL |
| Save button disabled in client page | Empty URI rows or `http: //localhost` with space | Delete empty rows with trash icon, retype URI without space |
| "Google hasn't verified this app" | Normal in Testing | Advanced -> Go to <app> (unsafe) -> Continue |
| `localhost refused to connect` after Continue | Normal. Browser was redirected to localhost where nothing listens | Copy the FULL URL of that page (Chrome menu -> Open in Chrome, tap address bar, copy) |
| `RuntimeError: OAuth state mismatch` | Pasted URL from a different run than the printed auth URL | Run the cell ONCE, use that run's URL, paste that run's redirect. Never re-run the cell in between |
| `InsecureTransportError: OAuth 2 MUST utilize https` | oauthlib rejects http://localhost | `os.environ['OAUTHLIB_INSECURE_TRANSPORT']='1'` (already in script) and use a fresh code (codes are single-use) |
| `invalid_client` | Truncated/wrong client secret | Paste the full `GOCSPX-...` secret |
| `invalid_grant` | Code reused/expired, or refresh token expired (Testing = 7 days) | Re-run auth; publish app to production |
| `403 accessNotConfigured` / API not enabled | YouTube Data API v3 not enabled | Library -> enable |
| `quotaExceeded` | 10k units/day used | Wait for reset (midnight Pacific) or request quota extension |
| Video stuck at "Processing will begin shortly" | Upload reached YouTube; queue is slow or file codec odd | Wait 15-30 min, check YouTube Studio for status; use H.264 mp4 |
| Video is private after upload | Unverified API project lock | Make public in Studio, or complete YouTube API audit form |
| Bot cannot download video | File > 20 MB via Bot API | Use local Bot API server or Telethon |

## Telethon notes (files up to 2 GB)
Needs `api_id` and `api_hash` from my.telegram.org plus a bot token. Use `client.download_media(message, file=path)` inside a `events.NewMessage(from_users=OWNER_ID)` handler, then call the same `yt_upload()` from `scripts/bot.py`.
