#!/bin/bash
echo "Starting Frontend Development Server..."

cd frontend || { echo "Failed to change directory to frontend"; exit 1; }

# Check if node_modules exists, install if not
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "Failed to install Node dependencies."
        exit 1
    fi
fi

# Start React development server
echo "Starting React development server on http://localhost:3000"
npm start

echo "Frontend server stopped."
