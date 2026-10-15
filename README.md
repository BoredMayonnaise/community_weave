# Community Weave 🧵

A lightweight, mobile-first community app for neighborly sharing — requests, offers, direct messaging, and safety reports.

---

## Architecture & Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | **Vue 3 + Vite** | Mobile-first touch UI with bottom navigation & PWA manifest |
| **Backend** | **Django + DRF** | REST API with Token/Session Authentication |
| **Database** | **SQLite** | Low RAM, zero server maintenance |
| **Packaging** | **PWA → Capacitor** | Runs standalone in mobile browser; ready for APK export |

---

## Quick Start

### 1. Launch Both Services (One Command)
```bash
./start.sh
```
This starts:
- Django backend on: `http://127.0.0.1:8000`
- Vue frontend on: `http://localhost:5173`

**Port already in use?** Something else owns 8000 (a Docker container, usually). Move the backend and tell the frontend where it went:
```bash
BACKEND_PORT=8001 ./start.sh
```
If you see a spinner stuck on "Finding neighborhood posts..." with no error, the frontend is talking to whatever else is on 8000 — always start with `BACKEND_PORT` set.

### 2. Manual Startup

**Backend:**
```bash
cd backend
./venv/bin/python manage.py runserver 0.0.0.0:8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

---

## Seed Data & Demo Accounts

The database comes pre-seeded with sample posts and neighbor conversations. You can log in with any of these:

| Username | Password | Display Name | Neighborhood |
|---|---|---|---|
| `elena` | `pass123` | Elena Rostova | Downtown |
| `marcus` | `pass123` | Marcus Chen | North Hills |
| `sarah` | `pass123` | Sarah Jenkins | Riverside |

To re-seed the sample data at any time:
```bash
cd backend
./venv/bin/python manage.py seed_data
```

---

## Running Backend Tests

```bash
cd backend
./venv/bin/python manage.py test api
```

---

## Live API Server & Zero-Server-RAM Architecture

The Community Weave API is live over HTTPS:
- **Live Endpoint**: `https://communityweave.duckdns.org/api`
- **Zero-Server-RAM Client**: The frontend compiles directly into native mobile bundles (Android APK & iOS App). All UI rendering, DOM operations, and map rendering run entirely inside the client device's RAM — leaving the host server with minimal footprint (pure lightweight JSON REST responses).

---

## Mobile Apps (Capacitor & GitHub Actions CI/CD)

The project includes pre-configured native Android and iOS Capacitor projects with automated GitHub Actions CI/CD.

### 1. Automated APK & iOS Builds on GitHub
Pushing to `main` or `master` (or triggering `workflow_dispatch`) automatically builds mobile release packages via `.github/workflows/build-mobile.yml`:
- **Android APK**: Compiled via Gradle 8 on Ubuntu (`app-debug.apk`) uploaded as downloadable workflow artifact `community-weave-android-apk`.
- **iOS App**: Compiled via Xcode 16 on macOS (`CommunityWeave-iOS-Debug.zip`) uploaded as artifact `community-weave-ios-app`.

### 2. Local Mobile Development & Build
To build and sync locally:
```bash
cd frontend
npm run build
npx cap sync
```

**Open in Native IDEs:**
```bash
# Android Studio
npx cap open android

# Xcode (macOS)
npx cap open ios
```

**Build Android APK locally (with Android SDK):**
```bash
cd frontend/android
./gradlew assembleDebug
# Output APK: frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Responsive Device Support

The mobile UI is designed with adaptive styling across form factors:
- **Phone S (<=360px)**: Compact headers, optimized touch targets, fluid cards.
- **Phone M / L (375px - 480px)**: Native touch layout with bottom navigation bar and safe-area inset compensation for notch & home indicators.
- **Tablets (600px - 1024px+)**: Centered container canvas (up to 860px), 2-column post card grid, and clamped messaging panels.

