@echo off
echo Starting Backend Server...

REM Check if venv exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please ensure Python 3 is installed and in PATH.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .\venv\Scripts\activate

REM Install dependencies (Assumes requirements.txt exists)
echo Installing/updating Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Ensure requirements.txt exists and is correct.
    pause
    exit /b 1
)

REM Run Uvicorn server
echo Starting FastAPI server on http://localhost:8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo Backend server stopped.
pause