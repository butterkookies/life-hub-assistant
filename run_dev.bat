@echo off
title Andrei's Life Hub Assistant (Development Mode)
echo ===================================================
echo   Andrei's Life Hub Assistant - Dev Launcher
echo ===================================================

echo [1/2] Checking Python dependencies...
python -m pip install -q -r requirements.txt

echo [2/2] Launching backend server on http://0.0.0.0:8000...
start "Life Hub API Backend" cmd /k "python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Launching Vite development server on http://localhost:5173...
cd web
npm run dev

pause
