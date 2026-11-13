# Run in ONE Google Colab cell. Produces youtube_token.json.
# Run the cell ONCE; do not re-run between opening the URL and pasting the result.
import os, subprocess, sys
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'   # allow http://localhost redirect
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'    # tolerate scope ordering differences
from urllib.parse import urlparse, parse_qs

subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q',
    'google-auth-httplib2', 'google-auth-oauthlib', 'google-api-python-client'])

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.colab import files
import getpass

CLIENT_ID = input('Client ID: ').strip()
CLIENT_SECRET = getpass.getpass('Client secret (hidden): ').strip()

REDIRECT_URI = 'http://localhost'
SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.readonly',
]
client_config = {'web': {
    'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'redirect_uris': [REDIRECT_URI]}}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
flow.redirect_uri = REDIRECT_URI
auth_url, state = flow.authorization_url(
    access_type='offline', prompt='consent', include_granted_scopes='false')

print('\n1) Open this URL, approve all scopes (Advanced -> Go to app (unsafe) if warned):\n')
print(auth_url)
print('\n2) Browser will show "localhost refused to connect". That is normal.')
print('   Copy the COMPLETE URL of that page.')
callback = input('\n3) Paste the complete localhost URL here: ').strip()

if callback.startswith('http'):
    q = parse_qs(urlparse(callback).query)
    if q.get('state', [''])[0] not in ('', state):
        raise RuntimeError("OAuth state mismatch: URL is from a different run. Run the cell once and use that run's URL.")
    if 'error' in q:
        raise RuntimeError('Google auth failed: ' + q['error'][0])
    flow.fetch_token(authorization_response=callback)
else:
    flow.fetch_token(code=callback)

creds = flow.credentials
if not creds.refresh_token:
    raise RuntimeError('No refresh token. Re-run and approve with prompt=consent.')

path = '/content/youtube_token.json'
open(path, 'w').write(creds.to_json())
print('\nAUTH SUCCESS. Scopes:', *creds.scopes, sep='\n - ')
files.download(path)

yt = build('youtube', 'v3', credentials=creds)
items = yt.channels().list(part='snippet', mine=True).execute().get('items', [])
print(f'\nYouTube API test: {len(items)} channel(s)')
for c in items:
    print(' -', c['snippet']['title'], c['id'])
