#!/bin/bash
echo "Starting Backend Server..."

# Check if python3 exists, otherwise try python
PYTHON_CMD=python3
command -v $PYTHON_CMD >/dev/null 2>&1 || { PYTHON_CMD=python; }
command -v $PYTHON_CMD >/dev/null 2>&1 || { echo >&2 "Python not found. Please install Python 3."; exit 1; }

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies (Assumes requirements.txt exists)
echo "Installing/updating Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Ensure requirements.txt exists and is correct."
    exit 1
fi

# Run Uvicorn server
echo "Starting FastAPI server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo "Backend server stopped."