@echo off
cd /d "%~dp0"

taskkill /F /IM cloudflared.exe 2>nul
timeout /t 2

echo Opening Tunnel Windows...
start "Headless Training - API Tunnel (Port 8008)" cloudflared.exe tunnel --url http://127.0.0.1:8008
timeout /t 2
start "Headless Training - Dashboard Tunnel (Port 8501)" cloudflared.exe tunnel --url http://127.0.0.1:8501

echo.
echo Two windows should open showing tunnel URLs
echo Copy the HTTPS URLs and update your Slack command
pause
