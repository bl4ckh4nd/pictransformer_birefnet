@echo off
echo Starting Frontend Development Server...

cd frontend

REM Check if node_modules exists, install if not
if not exist node_modules (
    echo Installing Node dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo Failed to install Node dependencies.
        pause
        exit /b 1
    )
)

REM Start React development server
echo Starting React development server on http://localhost:3000
npm start

echo Frontend server stopped.
pause