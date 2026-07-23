# MUMAP Android Build Script
# Run this after installing Android Studio and Java JDK

Write-Host "=== MUMAP Android Build ===" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$nodePath = "C:\Users\yiann\AppData\Local\Temp\node\node-v20.18.0-win-x64"
$env:PATH = "$nodePath;$env:PATH"

# Step 1: Build web app
Write-Host "`n[1/5] Building web app..." -ForegroundColor Yellow
cd "$PSScriptRoot\frontend"
npm run build
if ($LASTEXITCODE -ne 0) { throw "Build failed" }

# Step 2: Check for Android platform
Write-Host "`n[2/5] Checking Android platform..." -ForegroundColor Yellow
if (-not (Test-Path "android")) {
    Write-Host "Adding Android platform..."
    npx cap add android
}

# Step 3: Sync assets
Write-Host "`n[3/5] Syncing assets to Android..." -ForegroundColor Yellow
npx cap sync
if ($LASTEXITCODE -ne 0) { throw "Sync failed" }

# Step 4: Open in Android Studio
Write-Host "`n[4/5] Opening Android Studio..." -ForegroundColor Yellow
npx cap open android

# Step 5: Instructions
Write-Host "`n[5/5] Build Instructions:" -ForegroundColor Green
Write-Host @"
In Android Studio:
1. Build → Generate Signed Bundle / APK
2. Select 'Android App Bundle'
3. Choose your keystore file
4. Enter passwords
5. Select 'release' build variant
6. Wait for build (2-5 minutes)
7. Find AAB at: android/app/build/outputs/bundle/release/app-release.aab

Then upload to Google Play Console:
https://play.google.com/console
"@ -ForegroundColor White

Write-Host "`n=== Done! ===" -ForegroundColor Cyan
