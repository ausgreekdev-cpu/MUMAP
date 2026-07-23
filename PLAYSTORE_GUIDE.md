# MUMAP - Play Store Submission Guide

## App Metadata

**App Name:** MUMAP - Agent Platform
**Package:** com.mumap.agents
**Category:** Productivity
**Content Rating:** Everyone
**Price:** Free (with in-app subscriptions)

### Short Description (80 chars)
Multi-agent orchestration platform for AI teams.

### Full Description (4000 chars)
MUMAP is a powerful multi-agent orchestration platform that lets you manage, monitor, and coordinate AI agent teams from your mobile device.

**Key Features:**
- Deploy and manage AI agents with one tap
- Real-time task monitoring and agent health tracking
- 10 industry-specific templates (Software Dev, Healthcare, Finance, E-Commerce, Marketing, Legal, Education, Manufacturing, Real Estate, HR)
- WebSocket-powered live updates
- Smart task assignment based on agent capabilities
- Agent lifecycle management (start, stop, restart)
- System health dashboard with metrics

**Choose Your Plan:**
- **Community (Free):** Up to 3 agents, 10 tasks/day, 2 templates
- **Pro ($14.99/mo):** 15 agents, unlimited tasks, all templates, analytics
- **Team ($39.99/mo):** 50 agents, API access, team collaboration, dedicated support

**Built for:**
- Developers building AI-powered automation
- Teams orchestrating multi-step AI pipelines
- Anyone who wants autonomous agents working around the clock

**Privacy First:** Your data stays on your device. We never sell your information.

### What's New (v1.0.0)
- Initial release
- Multi-agent management
- Industry templates
- Real-time monitoring
- Subscription plans

## Google Play Console Setup Steps

1. Go to https://play.google.com/console
2. Pay $25 one-time developer registration fee
3. Click "Create app"
4. Fill in:
   - App name: MUMAP - Agent Platform
   - Default language: English (United States)
   - App or game: App
   - Free or paid: Free
5. Accept terms → Create app
6. Complete all sections:
   - Store listing (description, screenshots, feature graphic)
   - App content (privacy policy, data safety)
   - Pricing & distribution
   - Content rating (IARC questionnaire)

## Subscriptions to Create in Play Console

Go to Monetize → Subscriptions and create:

### Subscription 1: Pro
- Product ID: com.mumap.agents.pro
- Name: Pro Plan

**Base Plan:**
- Plan ID: pro-monthly
- Billing period: Monthly
- Price: $14.99

### Subscription 2: Team
- Product ID: com.mumap.agents.team
- Name: Team Plan

**Base Plan:**
- Plan ID: team-monthly
- Billing period: Monthly
- Price: $39.99

## Build Requirements

### Install Android Studio
1. Download from https://developer.android.com/studio
2. Install with default settings
3. Open Android Studio → SDK Manager → Install Android 14 SDK

### Install Java JDK 17+
1. Download from https://adoptium.net/
2. Install with default settings
3. Set JAVA_HOME environment variable

### Generate Signing Key
```bash
keytool -genkey -v -keystore mumap-release.keystore -alias mumap -keyalg RSA -keysize 2048 -validity 10000
```

### Build Commands
```bash
cd frontend

# Build web app
npm run build

# Add Android platform (first time only)
npx cap add android

# Sync web assets to Android
npx cap sync

# Open in Android Studio
npx cap open android
```

### In Android Studio
1. Build → Generate Signed Bundle / APK
2. Select Android App Bundle
3. Choose your keystore file
4. Enter passwords
5. Select release build variant
6. Wait for build (2-5 minutes)
7. Find AAB at: android/app/build/outputs/bundle/release/app-release.aab

### Upload to Play Console
1. Go to your app → Production → Create new release
2. Upload app-release.aab
3. Add release notes
4. Review → Start roll-out

## App Store Assets Needed

### Required Images
- **Feature Graphic:** 1024 x 500 px (PNG/JPG)
- **App Icon:** 512 x 512 px (PNG, 32-bit)
- **Screenshots:** 3-5 screenshots
  - Phone: 1080 x 1920 px (9:16 ratio)
  - Tablet: 1200 x 1920 px (optional)
- **Privacy Policy URL:** Must be publicly accessible

### Recommended Screenshots
1. Dashboard overview
2. Agent list with live status
3. Templates page with industry cards
4. Task monitoring view
5. Pricing page
