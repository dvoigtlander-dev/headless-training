@echo off
REM Clean restart script - forces all processes to restart fresh
REM Use when stuck processes prevent new tunnels from working

cd /d "%~dp0"

echo === Headless Training - CLEAN RESTART ===
echo.
echo Killing all stuck processes...

REM Force kill ALL instances
taskkill /F /IM cloudflared.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1

echo Waiting 3 seconds for cleanup...
timeout /t 3 /nobreak

echo.
echo Starting services fresh...
echo.

REM Clear old tunnel logs
del /Q cloudflared-*-session.log >nul 2>&1

REM Start FastAPI
echo [1/4] Starting FastAPI on port 8008...
start "FastAPI Server" python main.py
timeout /t 2 /nobreak

REM Start Streamlit
echo [2/4] Starting Streamlit on port 8501...
start "Streamlit Dashboard" streamlit run dashboard.py --server.port=8501 --logger.level=error
timeout /t 3 /nobreak

REM Start API tunnel
echo [3/4] Starting API tunnel (port 8008)...
start "Cloudflared - API" cloudflared.exe tunnel --url http://localhost:8008
timeout /t 3 /nobreak

REM Start Dashboard tunnel
echo [4/4] Starting Dashboard tunnel (port 8501)...
start "Cloudflared - Dashboard" cloudflared.exe tunnel --url http://localhost:8501
timeout /t 5 /nobreak

REM Extract and display tunnel URLs
echo.
echo === TUNNEL URLS ===
echo.

for /f "tokens=* usebackq" %%A in (`findstr /C:"trycloudflare" cloudflared-api-session.log ^| findstr /V "ERR" ^| FIND /N ".*" ^| findstr /C:": " ^| for /f "delims=: tokens=2*" %%B in ('more') do @echo(%%C`) do (
  echo API Tunnel: %%A
)

for /f "tokens=* usebackq" %%A in (`findstr /C:"trycloudflare" cloudflared-dashboard-session.log ^| findstr /V "ERR" ^| FIND /N ".*" ^| findstr /C:": " ^| for /f "delims=: tokens=2*" %%B in ('more') do @echo(%%C`) do (
  echo Dashboard Tunnel: %%A
)

echo.
echo === STARTUP COMPLETE ===
echo FastAPI (local):    http://localhost:8008
echo Dashboard (local):  http://localhost:8501
echo.
echo Check logs for full tunnel URLs:
echo   cloudflared-api-session.log
echo   cloudflared-dashboard-session.log
echo.
echo Update Slack app with the new API tunnel URL!
echo.
pause
