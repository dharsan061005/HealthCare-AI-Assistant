@echo off
echo Starting Healthcare AI Assistant...
echo.

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "..\..\.venv\Scripts\activate.bat" (
    call "..\..\.venv\Scripts\activate.bat"
    echo Virtual environment activated.
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo Virtual environment activated.
) else (
    echo No virtual environment found, using system Python.
)

echo.
echo Launching Streamlit app at http://localhost:8501
echo Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
