#!/bin/bash
# API Server Startup Script for Linux/macOS

echo "========================================"
echo "  Quantitative Trading API Server"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.11+"
    exit 1
fi

echo "[INFO] Python version:"
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found"
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    echo "[INFO] Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
echo ""

# Install/upgrade dependencies
echo "[INFO] Installing/upgrading dependencies..."
pip install --upgrade pip
pip install -r requirements_api.txt
echo ""

# Create necessary directories
mkdir -p logs data config

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[WARN] .env file not found"
    if [ -f ".env.example" ]; then
        echo "[INFO] Copying .env.example to .env"
        cp .env.example .env
        echo "[WARN] Please edit .env file with your configuration"
    fi
    echo ""
fi

# Start the API server
echo "========================================"
echo "  Starting API Server..."
echo "========================================"
echo ""
echo "[INFO] API will be available at:"
echo "       - Swagger UI:  http://localhost:8000/docs"
echo "       - ReDoc:       http://localhost:8000/redoc"
echo "       - Health:      http://localhost:8000/health"
echo ""
echo "[INFO] Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python3 api_main.py
