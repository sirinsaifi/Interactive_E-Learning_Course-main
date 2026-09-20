@echo off
title LearnSphere Frontend
cd /d "%~dp0frontend"

echo === Installing dependencies (if needed) ===
if not exist node_modules (
    npm install
)

echo.
echo === Starting frontend dev server ===
npm run dev
pause
