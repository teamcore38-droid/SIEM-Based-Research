@echo off
REM =====================================================
REM   MEDGUARD-X  ARS Dashboard Launcher
REM   Run this file to start all 3 services at once
REM   Model: ars_response_model_v2.pkl (93.7%% accuracy)
REM =====================================================

cd /d "%~dp0"

echo.
echo  ============================================================
echo       MEDGUARD-X  AUTOMATED RESPONSE SYSTEM
echo       Exam Demo Launcher
echo  ============================================================
echo.

echo  [0/3]  Clearing old log data for fresh demo...
if exist "logs\ars_events.json" del "logs\ars_events.json"
if exist "logs\inventory.json" del "logs\inventory.json"
echo         Done.
echo.

echo  [1/3]  Starting Backend API Server (port 5000)...
start "ARS Backend API" cmd /k "cd /d "%~dp0" && .venv\Scripts\python scripts\dashboard_server.py"

timeout /t 2 /nobreak >nul

echo  [2/3]  Starting AI Correlation Engine (port 8000)...
start "ARS AI Engine" cmd /k "cd /d "%~dp0" && .venv\Scripts\python scripts\ws_server.py --mode correlated"

timeout /t 3 /nobreak >nul

echo  [3/3]  Starting Frontend Dashboard (port 5173)...
start "ARS Web Dashboard" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo  ============================================================
echo    ALL SYSTEMS ONLINE
echo.
echo    Dashboard:  http://localhost:5173
echo    Login:      admin / medguard123
echo.
echo    AI Model:   ars_response_model_v2.pkl (93.7%% accuracy)
echo    Devices:    4 ESP32 IoMT sensors (real IPs)
echo  ============================================================
echo.
echo  Press any key to close this launcher (services keep running)
pause >nul
