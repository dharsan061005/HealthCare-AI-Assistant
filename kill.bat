@echo off
title Kill Healthcare AI Assistant
echo.
echo  =============================================
echo    Healthcare AI Assistant - Stopping...
echo  =============================================
echo.

set "FOUND=0"

REM Kill by port 8501
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8501 "') do (
    if not "%%a"=="0" (
        echo  Killing PID %%a on port 8501...
        taskkill /PID %%a /F >nul 2>&1
        set "FOUND=1"
    )
)

REM Kill any leftover streamlit processes by name
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq streamlit.exe" 2^>nul ^| findstr /i "streamlit"') do (
    echo  Killing streamlit.exe PID %%a...
    taskkill /PID %%a /F >nul 2>&1
    set "FOUND=1"
)

if "%FOUND%"=="1" (
    echo.
    echo  Done. Healthcare AI Assistant stopped.
) else (
    echo  No running instance found on port 8501.
)

echo.
pause
