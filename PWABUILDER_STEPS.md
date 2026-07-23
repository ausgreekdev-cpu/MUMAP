# MUMAP - PWABuilder Deployment (Path A)

## Current Status
- Production build: ✅ Built to `frontend/dist/`
- Local server: Running on `http://127.0.0.1:8080`
- PWA manifest: ✅ `public/manifest.json`
- Service worker: ✅ `public/sw.js`

## Step-by-Step Instructions

### Option 1: Deploy to Netlify (Recommended)

1. Go to https://app.netlify.com
2. Sign up (free)
3. Drag & drop the `frontend/dist` folder onto the dashboard
4. Netlify gives you a URL like `https://random-name.netlify.app`
5. Go to https://www.pwabuilder.com
6. Enter that URL
7. Click **Start**
8. Fix any issues in the report card
9. Click **Package For Stores**
10. Select **Windows** → **Generate Package**
11. Enter your Microsoft Store identity
12. Download `.msixbundle`

### Option 2: Deploy to Vercel

1. Go to https://vercel.com
2. Sign up (free)
3. Click **New Project** → **Import**
4. Upload `frontend/dist` folder
5. Get the URL
6. Follow PWABuilder steps above

### Option 3: Use Localtunnel

Run in terminal:
```bash
cd frontend
npx localtunnel --port 8080
```
Copy the HTTPS URL and use it in PWABuilder.

## PWABuilder Steps

1. Open https://www.pwabuilder.com
2. Enter your public URL
3. Click **Start**
4. Review the report card
5. Click **Package For Stores**
6. Select **Windows**
7. Click **Generate Package**
8. Enter Microsoft Store identity (from Partner Center)
9. Download `.msixbundle`
10. Upload to https://partner.microsoft.com

## Important Notes

- The URL must be HTTPS (all options above provide this)
- The app must be accessible publicly
- PWABuilder checks: manifest, service worker, icons, offline support
- If icons are missing, PWABuilder will flag them
- Generate proper icons (50x50, 44x44, 150x150, 310x150, 310x310) before packaging
