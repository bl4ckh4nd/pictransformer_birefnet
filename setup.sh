#!/bin/bash

# Install Modal CLI if not already installed
pip install -U modal-client

# Login to Modal (will open browser for authentication)
modal token new

# Deploy the Modal application
modal deploy modal_api.py

# Get the deployment URL and save it to frontend .env
echo "Remember to:"
echo "1. Copy the Modal deployment URL from above"
echo "2. Create a .env.production file in the frontend directory with:"
echo "NEXT_PUBLIC_API_URL=your-modal-url"
echo "3. Deploy the frontend to Vercel using:"
echo "cd frontend && vercel"