# Telegram -> YouTube Uploader

Send a video to your Telegram bot, it uploads to your YouTube channel and replies with the link.

## Quick start
1. Follow `references/google-cloud-setup.md` (project, YouTube API, test user, Web client with redirect `http://localhost`).
2. Run `scripts/auth_colab.py` in one Colab cell -> download `youtube_token.json`.
3. Create a bot with @BotFather, get your ID from @userinfobot.
4. `cp .env.example .env`, fill values, put `youtube_token.json` in the repo folder (it is git-ignored).
5. `pip install -r requirements.txt && python scripts/bot.py`
6. Send an mp4 (<20 MB) to the bot. Caption line 1 = title, rest = description.

## Give this to an AI
Upload this folder (or paste `SKILL.md`) and say: "Follow SKILL.md and set this up for me step by step."

## Limits
20 MB per file via Bot API, ~6 uploads/day quota, 7-day token expiry in Testing mode, unverified projects may lock videos to private. Details in `SKILL.md`.

## Security
Never commit `.env`, `youtube_token.json` or client secrets. The refresh token gives full control of the channel. Revoke at myaccount.google.com/permissions if leaked.
