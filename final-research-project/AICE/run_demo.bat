@echo off
echo ==========================================
echo      AICE Demo Wrapper (Windows)
echo ==========================================
echo.

echo [1/3] Generating random alert data...
python tools/generate_data.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to generate data. Is Python installed and in your PATH?
    pause
    exit /b
)

echo.
echo [2/3] Running Correlation Engine...
python run_aice.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Engine crashed.
    pause
    exit /b
)

echo.
echo [3/3] Converting JSON output to CSV...
python tools/json_to_csv.py

echo.
echo ==========================================
echo SUCCESS! Output files generated:
echo   - JSON: data\incidents.json
echo   - CSV:  data\incidents.csv
echo ==========================================
pause
