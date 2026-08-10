#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")"

echo "=== MURTHEHELP WEB ==="

if ! command -v python >/dev/null 2>&1; then
  echo "[*] python o'rnatilmoqda..."
  pkg update -y
  pkg install -y python
fi

if ! python -c "import flask" >/dev/null 2>&1; then
  echo "[*] flask o'rnatilmoqda..."
  pip install -q flask
fi

python -c "import sqlite3" >/dev/null 2>&1 || pkg install -y python

echo "[*] Ishga tushmoqda..."
python app.py
