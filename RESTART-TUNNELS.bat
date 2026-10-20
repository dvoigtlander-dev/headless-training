@echo off
REM Restart cloudflared tunnels with fresh credentials

cd /d "%~dp0"

echo === Restarting Cloudflared Tunnels ===
echo.

REM Kill any existing cloudflared processes
echo Killing old cloudflared processes...
taskkill /F /IM cloudflared.exe 2>nul || true
timeout /t 2

REM Start fresh tunnels
echo Starting API tunnel on port 8008...
start "Cloudflared - API" /D "%~dp0" cloudflared.exe tunnel --url http://127.0.0.1:8008
timeout /t 3

echo Starting Dashboard tunnel on port 8501...
start "Cloudflared - Dashboard" /D "%~dp0" cloudflared.exe tunnel --url http://127.0.0.1:8501
timeout /t 3

echo.
echo === Tunnels Started ===
echo Check the cloudflared windows for public URLs
echo.
pause
