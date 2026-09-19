@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: RUN_ME_FIRST.bat
:: Double-click this file to set up and run the project automatically.
:: Like: dotnet restore + dotnet run in one click.
:: ─────────────────────────────────────────────────────────────────────────────

echo.
echo =====================================================
echo   Student Performance Prediction System
echo   BCA 8th Semester Project Setup
echo =====================================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/4] Python found. Installing required packages...
echo       (Like: dotnet restore - only needed once)
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package installation failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo [2/4] Generating training data (600 student records)...
echo       (Like: running database seed / EF migrations)
echo.
python generate_data.py
if errorlevel 1 (
    echo [ERROR] Failed to generate data.
    pause
    exit /b 1
)

echo.
echo [3/4] Training ML models (first run only - takes ~30 seconds)...
echo.

echo.
echo [4/4] Starting the web application...
echo       Open your browser and go to: http://localhost:5000
echo       Press Ctrl+C in this window to stop the server.
echo.
echo =====================================================

python app.py

pause
