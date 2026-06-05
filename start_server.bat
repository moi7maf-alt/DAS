@echo off
cd /d "%~dp0"
echo Starting JLD Dashboard Server...
start /B python ai_server.py
echo ✅ Server started on http://localhost:5000
echo Close this window to stop the server (for testing only).
echo For permanent 24/7 operation, use install_service.bat instead.
pause
