@echo off
cd /d C:\Users\dvoigtlander\claude\Headless_Training
cloudflared.exe tunnel --url http://127.0.0.1:8501
pause
