@echo off
title Notion Tasks Desktop Widget
cd /d "%~dp0"
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)
if not exist "dist-electron\main.js" (
    echo Building widget bundle...
    call npm run build
)
start "" "node_modules\electron\dist\electron.exe" "dist-electron\main.js"
exit
