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

## Turning into an APK (Capacitor Next Step)

When you are ready to wrap into an Android APK:
```bash
cd frontend
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init "Community Weave" com.communityweave.app --web-dir dist
npm run build
npx cap add android
npx cap open android
```
