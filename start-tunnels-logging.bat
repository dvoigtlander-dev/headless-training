@echo off
REM Start cloudflared tunnels with full logging output

cd /d "%~dp0"

echo Killing old processes...
taskkill /F /IM cloudflared.exe 2>nul
timeout /t 1

echo Starting API tunnel...
cloudflared.exe tunnel --url http://127.0.0.1:8008 2>&1 | tee api-tunnel-output.log

echo Starting Dashboard tunnel...
cloudflared.exe tunnel --url http://127.0.0.1:8501 2>&1 | tee dashboard-tunnel-output.log
