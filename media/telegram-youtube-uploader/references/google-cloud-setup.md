# Google Cloud setup (works from phone Chrome with "Desktop site" on)

1. console.cloud.google.com -> create project (e.g. `Hermes-YouTube-Upload`).
2. **APIs & Services -> Library** -> search **YouTube Data API v3** -> **Enable**.
3. **Google Auth Platform** (old UI: OAuth consent screen)
   - Branding: app name, support email, developer email.
   - **Audience**: User type **External**, status **Testing**.
   - **Audience -> Test users -> + Add users** -> add the Gmail that owns the YouTube channel -> Save.
4. **Clients -> Create client**
   - Application type: **Web application**
   - Authorized JavaScript origins: leave EMPTY (delete empty rows, they block Save)
   - Authorized redirect URIs: `http://localhost`  (no trailing slash, no port, no spaces; phone keyboards add a space after `http:` so check)
   - Leave "Use this client for an AI-powered agent" unticked
   - Create -> copy Client ID and Client secret (secret is shown fully only at creation; use "Add secret" if lost)
5. Wait 2-5 minutes for settings to propagate.
6. Optional but recommended: Audience -> **Publish app** to avoid the 7-day token expiry.
