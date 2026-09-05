@echo off
title Andrei's Life Hub Assistant (Production)
echo ===================================================
echo   Andrei's Life Hub Assistant - Production Launcher
echo ===================================================

echo [1/3] Checking dependencies...
python -m pip install -q -r requirements.txt

echo [2/3] Checking frontend build...
if not exist "web\dist\index.html" (
    echo Building frontend for production...
    cd web
    call npm install
    call npm run build
    cd ..
)

echo [3/3] Starting Life Hub Assistant on http://0.0.0.0:8000...
echo Ready for local, Tailscale IP, and Tailscale Serve HTTPS access!
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
pause
