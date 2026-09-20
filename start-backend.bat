@echo off
title LearnSphere Backend
cd /d "%~dp0backend"

echo === Installing/updating dependencies ===
pip install -r requirements.txt --quiet

echo.
echo === Running database migrations ===
alembic upgrade head

echo.
echo === Starting backend on http://localhost:8000 ===
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
