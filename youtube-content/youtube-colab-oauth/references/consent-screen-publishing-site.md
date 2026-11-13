# Consent-Screen Publishing Site (GitHub Pages)

To publish an OAuth consent screen, Google requires **live URLs** for the app home page, privacy policy, and terms of service — it fetches them during verification. A local file or `localhost` URL will not verify.

## Why static HTML, not a JS/React build

The user may hand you a `client/` React/TypeScript project (components, `ui/` shadcn parts, `pages/`). Such a folder is often **incomplete**: no `package.json`, no `vite.config`, no `node_modules`, no `tsconfig` — just source files. It cannot be built, and guessing a build (npx vite, npm install) wastes time. The reliable path is a **hand-written static HTML site** with three pages, committed to a repo and served by GitHub Pages.

## Deploy recipe (verified working)

1. Write three self-contained pages (inline `<style>`, no external assets):
   - `index.html` — Home
   - `privacy-policy.html`
   - `terms.html`
2. Create the repo and push:
   ```bash
   gh repo create <user>/oauth-publishing-site --public --description "OAuth consent screen publishing site"
   cd oauth_site_static
   git init -q && git config user.name <user> && git config user.email <email>
   git add . && git commit -m "OAuth publishing site"
   git remote add origin https://github.com/<user>/oauth-publishing-site.git
   git branch -M main && git push -u origin main
   ```
3. Enable GitHub Pages (API — the URL form below is the exact working shape):
   ```bash
   gh api -X POST repos/<user>/oauth-publishing-site/pages \
     -f "source[branch]=main" -f "source[path]=/"
   ```
   Site URL: `https://<user>.github.io/oauth-publishing-site/`
4. Wait for the build (~30-45s; poll `gh api .../pages` until `status: built`). 404 during "building" is normal.
5. Verify each page with `curl -sL -o /dev/null -w "%{http_code}"` — expect 200 and matching `<title>`.

## Wire the URLs into the Branding page

| Field | Value |
|---|---|
| Application home page | `https://<user>.github.io/oauth-publishing-site/` |
| Privacy policy link | `.../privacy-policy` |
| Terms of service link | `.../terms` |
| Authorized domains | bare host only, e.g. `<user>.github.io` (never `https://`, never a path) |

## Pitfalls

- **Authorized domain must match the App domain host.** Link set to `github.com` but domain list empty → "Missing domain: github.com". Enter the bare host under `+ Add domain`.
- **App domain links are optional** — you can delete all three and skip authorized domains to publish faster (only developer contact email is mandatory).
- **`status: building` returns 404 on the site** — poll the Pages API, do not retry the site until `status: built`.
- **Pages URL has a trailing slash** — `/oauth-publishing-site` without `/` 301-redirects; use the slash form in App domain fields.
