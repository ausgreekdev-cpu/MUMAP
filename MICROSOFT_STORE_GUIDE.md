# MUMAP — Microsoft Store Submission Guide (v2.1.0)

Get the MUMAP client into the Microsoft Store as a **paid, one-time-purchase
PWA package**. Users run the backend on their own server; the Store app is the
client.

## How it works

```
Microsoft Store (paid MSIX client)
        │  opens
        ▼
GitHub Pages PWA  (auto-deployed: https://ausgreekdev-cpu.github.io/MUMAP/)
        │  talks to a user-configured API URL (/setup screen, localStorage)
        ▼
User's own MUMAP server  (docker-compose, HTTPS, CORS_ORIGINS set)
```

The PWA ships a first-run **`/setup`** screen where each user enters their
server URL (validated against `GET {server}/health`). Nothing about the user's
data touches you — see `frontend/src/pages/Privacy.tsx`.

## Prerequisites

1. **Microsoft Partner account** — https://partner.microsoft.com, one-time $19
2. **A public HTTPS URL for the frontend** — already handled: every push to
   `main` auto-deploys to **https://ausgreekdev-cpu.github.io/MUMAP/** via the
   `deploy-pages` CI job. (Alternatives: Netlify drag-and-drop of
   `frontend/dist`, or your own domain.)
3. **Icon set** — already generated in `store/` (StoreLogo, Square44/150,
   Wide310, Large310 at 1× and 2× scales)
4. **Privacy policy URL** — use **https://ausgreekdev-cpu.github.io/MUMAP/privacy**
5. **Listing copy** — paste-ready fields in `store/STORE_LISTING.md`

### If account creation is blocked

Partner Center onboarding is flaky; work through this checklist before
escalating:

1. Use a **personal Microsoft account** (Outlook/Hotmail), not a work/school
   account — Individual enrollment rejects the wrong account type
2. Fresh **incognito window**, latest **Edge or Chrome**, **disable
   ad-blockers/VPN/proxies** (they break the enrollment scripts)
3. Your Microsoft account profile **name/address/phone must match your ID
   exactly** — mismatch triggers an instant "Microsoft runs on trust… request
   was blocked" rejection
4. Retry via the direct link:
   `partner.microsoft.com/dashboard/account/v3/enrollment/introduction`
5. If rejected, note the **reference / transaction / correlation ID** in the
   error and open a Partner Center support ticket — backend blocks (e.g. the
   known `AlternativeBusinessContact` individual-account bug) can only be
   cleared by Microsoft
6. **Do not retry repeatedly in one day** — repeated attempts extend the
   risk-based block window

Meanwhile the app stays installable without the Store (see README →
"Install as an app"), so distribution isn't blocked on this step.

## Step 1 — Build the PWA

CI does this for you. The `deploy-pages` job runs:

```bash
cd frontend
npm ci
BASE_PATH=/MUMAP/ npm run build   # dist/ with manifest + sw + 404.html
```

Sanity-check `dist/`: it must contain `manifest.webmanifest`, `sw.js`,
`404.html`, and `icons/` — manifest `start_url`/`scope` = `/MUMAP/`, name
**MUMAP — Multi-Agent Platform**, display `standalone`, theme `#0a0a0f`.

## Step 2 — Host the frontend

Automatic (this repo): the `deploy-pages` job publishes `dist/` to GitHub
Pages on every green push to `main`. Manual option: deploy `frontend/dist`
(`BASE_PATH=/` build, or the `pwa-dist` CI artifact) to any static host.

Your PWABuilder input URL is **`https://ausgreekdev-cpu.github.io/MUMAP/`**.

## Step 3 — PWABuilder package

1. Open https://www.pwabuilder.com and enter
   **https://ausgreekdev-cpu.github.io/MUMAP/** → **Start**
2. Fix anything flagged on the report card (manifest + icons are pre-wired)
3. **Package For Stores** → **Windows** → **Generate Package**
4. Enter your Partner Center identity (publisher ID from Partner Center)
5. Download the `.msixbundle`

## Step 4 — Partner Center submission

1. **Apps and games → New product** → reserve the name (e.g. `MUMAP`)
2. **Pricing**: set your one-time paid price (placeholder in
   `store/STORE_LISTING.md` suggests $24.99). Microsoft keeps 30% (85% after
   the first $10k/year in some programs — check current Partner Center terms)
3. **Properties**: age rating questionnaire, category **Developer tools** /
   **Productivity**, notes "self-hosted backend required"
4. **Store listings**: paste from `store/STORE_LISTING.md` (name, short/long
   description, keywords, what's new); upload screenshots (**1280×764**
   recommended, plus phone sizes if you want phone visibility — the UI is
   responsive)
5. **Availability**: markets, hidden/visible
6. **Upload** the `.msixbundle`, complete submission → certification (usually
   a few days)

### Submission checklist

- [ ] Public HTTPS URL live and PWABuilder report card clean
- [ ] Privacy policy URL reachable (`/privacy`)
- [ ] Screenshots at 1280×764 (min) — Dashboard, Agents, Tasks, Marketplace
- [ ] Pricing set (paid, one-time)
- [ ] Age rating questionnaire completed
- [ ] Store description mentions **BYO server** (no hosting included)
- [ ] Support contact / website = GitHub repo issues URL

## Step 5 — Backend expectations for users

Document this in your Store description (also in the repo README):

```bash
git clone https://github.com/ausgreekdev-cpu/MUMAP.git && cd MUMAP
docker-compose up -d
# then set CORS_ORIGINS to the PWA origin, e.g.
# CORS_ORIGINS=https://mumap.example.com
```

Users open the Store app → `/setup` → enter their server URL (HTTPS
recommended; `http://localhost:8000` works on the same machine for packaged
PWAs on Windows 11) → sign in / register.

> **HTTPS note**: browsers block `https://` pages from calling
> `http://` backends (mixed content) except localhost. Tell users to put their
> server behind HTTPS (Caddy/nginx/tailscale serve) or run it locally.

## Monetization notes

- The one-time Store price covers the **client license only**. Hosting, LLM
  API keys, and the free/pro/enterprise usage plans on the user's own instance
  remain theirs to manage (seeded plans live in `backend/services/usage.py`).
- No in-app purchase APIs are used — the Store handles the sale and install
  entitlement. This is the simplest Store-compliant paid model and avoids the
  Windows Store licensing APIs entirely.

## Optional: Electron fallback

If you later want a true desktop shell (offline start menu icon independent of
a host, direct Store licensing APIs), the v1.0.0 archive branch
(`archive/v1.0.0`) contains an electron-builder `appx` config — but the PWA
path above is the supported one for v2.1.0+.
