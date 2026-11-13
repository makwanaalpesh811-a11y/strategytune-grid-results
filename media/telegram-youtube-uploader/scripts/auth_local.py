"""Local OAuth flow for YouTube API. Run on a machine with a browser.
Produces youtube_token.json. Requires: pip install google-auth-oauthlib google-api-python-client
"""
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.readonly',
]

CLIENT_SECRET_FILE = os.environ.get('YT_CLIENT_SECRET', 'client_secret_*.json')
TOKEN_FILE = os.environ.get('YT_TOKEN_PATH', 'youtube_token.json')

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
creds = flow.run_local_server(port=0)
with open(TOKEN_FILE, 'w') as f:
    f.write(creds.to_json())
print(f"Token saved to {TOKEN_FILE}")

# Verify
yt = build('youtube', 'v3', credentials=creds)
items = yt.channels().list(part='snippet', mine=True).execute().get('items', [])
print(f"Verified: {len(items)} channel(s) linked")
for c in items:
    print(f" - {c['snippet']['title']} ({c['id']})")
