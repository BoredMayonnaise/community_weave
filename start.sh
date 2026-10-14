#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

echo "==> Starting Community Weave Backend on http://127.0.0.1:8000..."
cd "$DIR/backend"
./venv/bin/python manage.py migrate --noinput
./venv/bin/python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

echo "==> Starting Community Weave Frontend on http://localhost:5173..."
cd "$DIR/frontend"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT INT TERM
wait
