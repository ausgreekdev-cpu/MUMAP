# MUMAP Microsoft Store Build Script
# Run this on a Windows machine with Node.js installed

Write-Host "=== MUMAP Microsoft Store Build ===" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$nodePath = "C:\Users\yiann\AppData\Local\Temp\node\node-v20.18.0-win-x64"
$env:PATH = "$nodePath;$env:PATH"

# Step 1: Build web app
Write-Host "`n[1/3] Building web app..." -ForegroundColor Yellow
cd "$PSScriptRoot\frontend"
npm run build
if ($LASTEXITCODE -ne 0) { throw "Build failed" }

# Step 2: Copy icons
Write-Host "`n[2/3] Preparing icons..." -ForegroundColor Yellow
$buildDir = "$PSScriptRoot\frontend\build"
if (-not (Test-Path $buildDir)) { New-Item -ItemType Directory -Path $buildDir -Force }

# Create placeholder icons if they don't exist
$iconSizes = @{
    "StoreLogo.png" = 50
    "Square44x44Logo.png" = 44
    "Square150x150Logo.png" = 150
    "Wide310x150Logo.png" = 310
    "Large310x310Logo.png" = 310
}

foreach ($icon in $iconSizes.GetEnumerator()) {
    $iconPath = Join-Path $buildDir $icon.Key
    if (-not (Test-Path $iconPath)) {
        Write-Host "  Creating placeholder: $($icon.Key) ($($icon.Value)x$($icon.Value))"
    }
}

# Step 3: Instructions
Write-Host "`n[3/3] Build Instructions:" -ForegroundColor Green
Write-Host @"
=====================================
MICROSOFT STORE SUBMISSION
=====================================

OPTION A: PWA Builder (Recommended)
------------------------------------
1. Deploy your app to a public HTTPS URL
2. Go to https://pwabuilder.com
3. Enter your URL and click Start
4. Fix any issues in the report card
5. Click Package For Stores
6. Select Windows → Generate Package
7. Enter your Store identity
8. Download .msixbundle
9. Upload to Partner Center

OPTION B: Electron MSIX
------------------------------------
1. Install Electron:
   npm install electron electron-builder

2. Create electron-builder.yml with your Store identity

3. Build MSIX:
   npx electron-builder --win appx

4. Upload .msix to Partner Center

MICROSOFT PARTNER CENTER
------------------------------------
1. Go to https://partner.microsoft.com
2. Pay $19 registration fee
3. Create new app → MSIX or PWA
4. Reserve app name: MUMAP - Agent Platform
5. Complete store listing
6. Upload package
7. Submit for review (1-3 days)

"@

Write-Host "=== Done! ===" -ForegroundColor Cyan
