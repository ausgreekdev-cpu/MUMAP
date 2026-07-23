# MUMAP - Microsoft Store Submission Guide

## Quick Start (PWA Builder - Recommended)

The fastest way to get MUMAP into the Microsoft Store is via PWA Builder.

### Prerequisites
1. Deploy MUMAP to a public URL (e.g., Vercel, Netlify, or your own server)
2. Microsoft Developer Account ($19 one-time fee)

### Steps

1. **Deploy your app** to a public HTTPS URL
2. Go to https://pwabuilder.com
3. Enter your app URL and click **Start**
3. PWABuilder will evaluate your PWA (manifest, service worker, icons)
4. Fix any issues flagged in the report card
5. Click **Package For Stores**
6. Select **Windows** → **Generate Package**
7. Enter your Microsoft Store identity (from Partner Center)
8. Download the `.msixbundle` file
9. Upload to Microsoft Partner Center

---

## Alternative: Electron + MSIX (More Control)

If you need a standalone desktop app (not just a PWA wrapper):

### Install Dependencies

```bash
cd frontend
npm install electron electron-builder @electron-forge/cli @electron-forge/maker-squirrel
```

### Build Commands

```bash
# Build web app
npm run build

# Package as Electron app
npx electron-builder --win

# Package as MSIX for Store
npx electron-builder --win appx
```

### electron-builder.yml

```yaml
appId: com.mumap.agents
productName: MUMAP
directories:
  buildResources: build
files:
  - dist/**/*
  - electron/**/*
win:
  target: appx
  icon: build/icon.ico
appx:
  applicationId: MUMAP
  identityName: MUMAP.AgentPlatform
  publisher: "CN=YOUR-PUBLISHER-ID-FROM-PARTNER-CENTER"
  publisherDisplayName: "MUMAP"
```

---

## Microsoft Partner Center Setup

### 1. Create Developer Account
- Go to https://partner.microsoft.com
- Sign in with Microsoft account
- Pay $19 one-time registration fee

### 2. Reserve App Name
- Go to **Apps and games** → **New product**
- Choose **MSIX or PWA app**
- Name: `MUMAP - Agent Platform`
- Note your Package Identity (Publisher + Name)

### 3. Store Listing

**App Name:** MUMAP - Agent Platform

**Short Description (under 100 chars):**
Multi-agent orchestration platform for AI teams.

**Long Description:**
```
MUMAP is a powerful multi-agent orchestration platform that lets you 
manage, monitor, and coordinate AI agent teams from your desktop.

Key Features:
- Deploy and manage AI agents with one tap
- Real-time task monitoring and agent health tracking
- 10 industry-specific templates
- WebSocket-powered live updates
- Smart task assignment based on agent capabilities

Choose Your Plan:
- Community (Free): Up to 3 agents, 10 tasks/day
- Pro ($14.99/mo): 15 agents, unlimited tasks, all templates
- Team ($39.99/mo): 50 agents, API access, team collaboration

Built for developers, teams, and anyone building AI automation.
```

**Category:** Productivity
**Subcategory:** Business Software

### 4. Required Assets

| Asset | Size | Format |
|-------|------|--------|
| Store Logo | 50x50 | PNG |
| Square 44x44 | 44x44 | PNG |
| Square 150x150 | 150x150 | PNG |
| Wide 310x150 | 310x150 | PNG |
| Large 310x310 | 310x310 | PNG |
| Feature Graphic | 1024x500 | PNG |
| Screenshots | 1366x768 min | PNG |

### 5. Pricing

- Free with in-app purchases
- Create subscription products in Partner Center:
  - `com.mumap.agents.pro` - $14.99/month
  - `com.mumap.agents.team` - $39.99/month

### 6. Content Rating
- Complete the IARC questionnaire
- Rating: Everyone

### 7. Submit
1. Upload `.msixbundle` to Packages section
2. Complete all required sections
3. Click **Submit for Certification**
4. Review takes 1-3 business days

---

## Testing Locally

### Install MSIX for Testing
```powershell
# Enable Developer Mode in Windows Settings
# Then install:
Add-AppxPackage -Path ".\MUMAP.msix"
```

### Test with Windows App Certification Kit
```powershell
# Download from Windows SDK
# Run against your package:
WindowsAppCertKit.exe .\MUMAP.msix
```

---

## Build Script

```bash
# build-store.ps1
Write-Host "Building MUMAP for Microsoft Store..."

# Build web
cd frontend
npm run build

# Create PWA package via PWABuilder
# (Manual step - go to pwabuilder.com)

# Or build Electron MSIX
npx electron-builder --win appx

Write-Host "Done! Upload .msix to Partner Center"
```

---

## Pricing Strategy

Based on market research, MUMAP should use:

| Plan | Price | Target |
|------|-------|--------|
| Community | Free | Individual devs, evaluation |
| Pro | $14.99/mo | Power users, small teams |
| Team | $39.99/mo | Teams, collaboration |

**Annual billing:** 17% discount (Pro $12.49/mo, Team $33.25/mo)

**Market positioning:**
- Below Orchify ($39-$129/mo) and OpenLegion ($62-$279/mo)
- Above LLMHive ($10-$35/mo) and CodeAgent ($9.99/mo)
- Competitive with HyperAgency ($39.99-$96.99/mo)
