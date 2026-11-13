"""Telegram -> YouTube uploader. Only TG_OWNER_ID may use it."""
import os, asyncio, tempfile, logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.environ['TG_BOT_TOKEN']
OWNER_ID = int(os.environ['TG_OWNER_ID'])
TOKEN_PATH = os.environ.get('YT_TOKEN_PATH', 'youtube_token.json')
PRIVACY = os.environ.get('YT_PRIVACY', 'private')  # private | unlisted | public


def get_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        open(TOKEN_PATH, 'w').write(creds.to_json())  # persist refreshed token
    return build('youtube', 'v3', credentials=creds)


def yt_upload(path, title, description=''):
    yt = get_service()
    req = yt.videos().insert(
        part='snippet,status',
        body={
            'snippet': {'title': title[:100], 'description': description, 'categoryId': '22'},
            'status': {'privacyStatus': PRIVACY, 'selfDeclaredMadeForKids': False},
        },
        media_body=MediaFileUpload(path, chunksize=-1, resumable=True),
    )
    return req.execute()['id']


async def on_video(update, ctx):
    if update.effective_user.id != OWNER_ID:
        return  # silently ignore strangers
    m = update.message
    f = m.video or m.document
    lines = (m.caption or 'Untitled').split('\n', 1)
    title, desc = lines[0], (lines[1] if len(lines) > 1 else '')
    if f.file_size and f.file_size > 20 * 1024 * 1024:
        await m.reply_text('File 20 MB se badi hai. Telethon / local Bot API server chahiye (references/troubleshooting.md).')
        return
    await m.reply_text('Download ho raha hai...')
    path = os.path.join(tempfile.gettempdir(), f'{f.file_id}.mp4')
    try:
        tg_file = await ctx.bot.get_file(f.file_id)
        await tg_file.download_to_drive(path)
        await m.reply_text('YouTube pe upload ho raha hai...')
        vid = await asyncio.to_thread(yt_upload, path, title, desc)
        await m.reply_text(f'Done ({PRIVACY}): https://youtu.be/{vid}\nProcessing me 5-30 min lag sakte hain.')
    except Exception as e:
        logging.exception('upload failed')
        await m.reply_text(f'Error: {e}')
    finally:
        if os.path.exists(path):
            os.remove(path)


if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, on_video))
    app.run_polling()
