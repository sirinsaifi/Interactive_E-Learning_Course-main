@echo off
title LearnSphere — Startup
color 0A

echo ============================================
echo   LearnSphere — Starting all services
echo ============================================
echo.

:: Start MySQL
echo [1/3] Starting MySQL service...
net start MySQL80 2>nul || net start MySQL 2>nul || echo  MySQL already running or named differently.
echo.

:: Ensure DB exists (optional — skip if no root password)
echo [2/3] Ensuring database and user exist...
mysql -u root -e "CREATE DATABASE IF NOT EXISTS lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS 'lms_user'@'localhost' IDENTIFIED BY 'lms_password'; GRANT ALL PRIVILEGES ON lms_db.* TO 'lms_user'@'localhost'; FLUSH PRIVILEGES;" 2>nul
echo  Database ready (or already set up).
echo.

:: Start backend
echo [3/3] Installing backend deps and starting API...
cd /d "%~dp0backend"
pip install -r requirements.txt -q 2>nul
alembic upgrade head
start "LearnSphere Backend" cmd /k "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait then start frontend
timeout /t 4 /nobreak >nul
echo Starting frontend...
cd /d "%~dp0frontend"
start "LearnSphere Frontend" cmd /k "npm run dev"

:: Open browser
timeout /t 6 /nobreak >nul
start http://localhost:5174

echo.
echo ============================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5174
echo ============================================
pause
