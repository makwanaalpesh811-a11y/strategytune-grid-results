# Scripts

- **bot.py** — Main Telegram → YouTube uploader. Run: `python bot.py`
- **auth_colab.py** — Generate `youtube_token.json` in Google Colab (no browser needed, paste URL)
- **auth_local.py** — Generate `youtube_token.json` on a machine WITH a browser (Windows/Mac/Linux desktop)

**On Termux:** Use `auth_colab.py` (Colab workflow). `auth_local.py` needs a real browser and can't run on Termux.

## First-time setup on Termux

```bash
# Install deps
pip install python-telegram-bot google-api-python-client google-auth google-auth-oauthlib python-dotenv

# Get your token from Colab (auth_colab.py) — save as youtube_token.json next to this dir

# Configure env
cp .env.example .env
# Edit .env with your real TG_BOT_TOKEN and TG_OWNER_ID

# Run
python bot.py
```
