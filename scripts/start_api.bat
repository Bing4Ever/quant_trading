@echo off
REM API Server Startup Script for Windows

echo ========================================
echo  Quantitative Trading API Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [WARN] Virtual environment not found
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [INFO] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install/upgrade dependencies
echo [INFO] Installing/upgrading dependencies...
pip install --upgrade pip
pip install -r requirements_api.txt
echo.

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "config" mkdir config

REM Check if .env exists
if not exist ".env" (
    echo [WARN] .env file not found
    if exist ".env.example" (
        echo [INFO] Copying .env.example to .env
        copy .env.example .env
        echo [WARN] Please edit .env file with your configuration
    )
    echo.
)

REM Start the API server
echo ========================================
echo  Starting API Server...
echo ========================================
echo.
echo [INFO] API will be available at:
echo        - Swagger UI:  http://localhost:8000/docs
echo        - ReDoc:       http://localhost:8000/redoc
echo        - Health:      http://localhost:8000/health
echo.
echo [INFO] Press Ctrl+C to stop the server
echo ========================================
echo.

python api_main.py

REM If server exits, pause to show any errors
if errorlevel 1 (
    echo.
    echo [ERROR] Server exited with errors
    pause
)
