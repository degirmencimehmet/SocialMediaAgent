#!/usr/bin/env bash
# AI Social Media Agent — Quick Start Script

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "─────────────────────────────────────────"
echo "  AI Sosyal Medya Ajansı — Başlatılıyor"
echo "─────────────────────────────────────────"

# ── Backend ───────────────────────────────────────────────────────────────────
echo ""
echo "► Backend kurulumu..."
cd "$ROOT/backend"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  .env dosyası oluşturuldu. Lütfen API anahtarlarını doldurun."
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo "► Backend başlatılıyor (port 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ── Frontend ──────────────────────────────────────────────────────────────────
echo ""
echo "► Frontend kurulumu..."
cd "$ROOT/frontend"

if [ ! -d "node_modules" ]; then
  npm install
fi

echo "► Frontend başlatılıyor (port 5173)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "─────────────────────────────────────────"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo "─────────────────────────────────────────"
echo ""
echo "  Durdurmak için: Ctrl+C"
echo ""

# Wait for both
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
