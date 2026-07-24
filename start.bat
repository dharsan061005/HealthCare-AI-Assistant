@echo off
echo =====================================================
echo   Healthcare AI Assistant — Starting...
echo =====================================================
echo.

cd /d "%~dp0"

REM Kill any existing Streamlit process to force fresh reload
taskkill /f /im streamlit.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq streamlit*" >nul 2>&1
timeout /t 1 /nobreak >nul

REM Activate virtual environment
if exist "..\.venv\Scripts\activate.bat" (
    call "..\.venv\Scripts\activate.bat"
    echo [OK] Virtual environment activated.
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo [OK] Virtual environment activated.
) else (
    echo [WARN] No virtual environment found, using system Python.
)

echo.
echo [OK] Launching app at http://localhost:8501
echo [INFO] Press Ctrl+C to stop.
echo.

streamlit run app.py --server.runOnSave true

pause
