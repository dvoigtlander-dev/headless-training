@echo off
REM Headless Training Search - Windows Startup

cd /d "%~dp0"

echo === Headless Training Search Startup ===
echo.

REM Kill any existing processes
echo Cleaning up old processes...
taskkill /F /IM python.exe 2>nul || true
taskkill /F /IM cloudflared.exe 2>nul || true
timeout /t 2 /nobreak

REM Start FastAPI server
echo Starting FastAPI server on port 8008...
start "FastAPI Server" python main.py > main-session.log 2>&1
timeout /t 3 /nobreak

REM Start Streamlit dashboard
echo Starting Streamlit dashboard on port 8501...
start "Streamlit Dashboard" python -m streamlit run dashboard.py --server.port 8501 > streamlit-session.log 2>&1
timeout /t 3 /nobreak

REM Start cloudflared tunnels
echo Starting cloudflared tunnels...
start "Cloudflared - API" cloudflared.exe tunnel --url http://127.0.0.1:8008 > api-tunnel.log 2>&1
timeout /t 2 /nobreak
start "Cloudflared - Dashboard" cloudflared.exe tunnel --url http://127.0.0.1:8501 > dashboard-tunnel.log 2>&1

timeout /t 5 /nobreak

echo.
echo === Systems Starting ===
echo FastAPI (localhost): http://localhost:8008
echo Dashboard (localhost): http://localhost:8501
echo.
echo Check cloudflared logs for public tunnel URLs:
echo   - cloudflared.log (API)
echo   - Check task manager for second tunnel output
echo.
echo To stop: Close cmd windows or use taskkill /F /IM python.exe /IM cloudflared.exe
pause
