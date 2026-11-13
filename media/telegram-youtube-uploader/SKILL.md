---
name: telegram-youtube-uploader
description: Set up and run a Telegram bot that receives a video from the owner and uploads it to their YouTube channel using the YouTube Data API v3 (OAuth2). Use this skill whenever the user wants to automate YouTube uploads from Telegram, create a YouTube OAuth token (youtube_token.json) in Google Colab, fix Google OAuth errors (access_denied 403, redirect_uri_mismatch, state mismatch, insecure_transport), or deploy a Telegram-to-YouTube agent on a VPS, Termux or Colab, even if they only say "send video to bot and it posts on YouTube".
---

# Telegram -> YouTube Uploader

Owner sends a video to a Telegram bot. Bot downloads it, uploads to YouTube via API, replies with the link.

## Workflow (do in order, confirm each step with the user)

1. **Google Cloud setup** -> read `references/google-cloud-setup.md`
   - Project, YouTube Data API v3 enabled, OAuth consent screen (External), user's Gmail added under Test users, OAuth client type **Web application** with redirect URI `http://localhost` (in *Authorized redirect URIs*, NOT JavaScript origins).
2. **Generate token** -> run `scripts/auth_colab.py` in ONE Google Colab cell (or `scripts/auth_local.py` on a PC).
   - Output: `youtube_token.json`. Treat it as a password.
3. **Telegram bot** -> user creates bot via @BotFather, gets token and own numeric user ID (@userinfobot).
4. **Configure** -> copy `.env.example` to `.env`, fill `TG_BOT_TOKEN`, `TG_OWNER_ID`; place `youtube_token.json` next to `scripts/bot.py`.
5. **Run** -> `pip install -r requirements.txt` then `python scripts/bot.py`.
6. **Test** -> send a small mp4 (<20 MB) with a caption (caption = title). Bot must reply with a youtu.be link.

## Rules for the AI following this skill

- NEVER ask the user to paste full secrets (client secret, bot token, token JSON) into chat. Tell them to put them in `.env` / the script locally.
- NEVER commit `.env`, `youtube_token.json`, `client_secret*.json` (see `.gitignore`).
- Bot MUST ignore any Telegram user whose ID != `TG_OWNER_ID`. Do not remove this check.
- Default privacy is `private`. Unverified API projects get uploads locked to private anyway.
- Reply to the user in their language (this user's default: Hinglish).
- If any error appears, check `references/troubleshooting.md` first before improvising.

## Known limits (tell the user up front)

| Limit | Detail |
|---|---|
| Telegram Bot API download | 20 MB max. For bigger files use a local Bot API server or Telethon (up to 2 GB) |
| YouTube quota | 10,000 units/day; one upload = ~1600 units (about 6 uploads/day) |
| Testing mode | Refresh token expires in 7 days. Fix: Audience -> **Publish app** (In production) |
| Unverified project | Uploaded videos may stay private until a YouTube API compliance audit |
| Processing | "Processing will begin shortly" can last 5-30+ min; check YouTube Studio for real status |

## Extending

Scheduled publish: add `'publishAt': ISO8601` and `privacyStatus: 'private'`. Thumbnails: `thumbnails().set`. Playlists: `playlistItems().insert`. Large files: swap to Telethon (`references/troubleshooting.md` has notes).
