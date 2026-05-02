@echo off
cd /d "%~dp0"
echo ===================================================
echo   MEDGUARD-X ^| SYSTEM REPAIR ^& LAUNCH
echo ===================================================

echo 1. Stopping all background processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM node.exe /T 2>nul
echo    (Cleaned up)

if not exist ".venv" (
    echo    [SETUP] Creating Virtual Environment...
    python -m venv .venv
    echo    [SETUP] Installing Dependencies...
    .venv\Scripts\python -m pip install --upgrade pip
) else (
    echo    [SETUP] Virtual Environment found.
)

echo    [SETUP] Ensuring all dependencies are installed...
.venv\Scripts\python -m pip install flask flask-cors pandas fpdf matplotlib seaborn scikit-learn joblib paho-mqtt

cd frontend
call npm install
cd ..

echo 3. Launching System Components...

echo    [A] Starting Backend API...
start "MedGuard Backend" cmd /k ".venv\Scripts\python scripts/dashboard_server.py"

echo    [B] Starting AI Core (Auto-Mode 4: Live MQTT)...
start "MedGuard AI Core" cmd /k ".venv\Scripts\python src/core/main.py --mode 4"

echo    [C] Starting Dashboard...
cd frontend
start "MedGuard Dashboard" cmd /k "npm run dev"

echo ===================================================
echo    REPAIR COMPLETE - SYSTEM LAUNCHING...
echo    Open: http://localhost:5173
echo ===================================================
pause
